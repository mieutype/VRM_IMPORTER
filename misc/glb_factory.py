"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
from .glb_bin_collector import Glb_bin_collection, Image_bin, Glb_bin
from ..gl_const import GL_CONSTANS
from collections import OrderedDict
import json
import struct
import sys.float_info
import bpy,bmesh

class Glb_obj():
	def __init__(self):
		self.json_dic = OrderedDict()
		self.bin = b""
		self.glb_bin_collector = Glb_bin_collection()
		self.result = None

	def convert_bpy2glb(self):
		#TODO
		self.armature_to_node_and_scenes_dic() #親のないboneは1つだけ as root_bone
		self.image_to_bin()
		self.texture_to_dic() 
		self.material_to_dic()
		self.mesh_to_bin_and_dic() #add to node and scenes mesh_object
		self.json_dic["scene"] = [0]
		self.glTF_meta_to_dic()
		#self.vrm_meta_to_dic()
		self.finalize()
		return self.result
	@classmethod
	def axis_blender_to_glb(vec3):
		return [vec3[i]*t for i,t in zip([0,2,1],[-1,1,1])]

	def armature_to_node_and_scenes_dic():
		def mesh_object_to_node(obj):
			node = {
				"name":obj.name,
				"translation":[0,0,0],
				"rotation":[0,0,0,1],
				"scale":[1,1,1]
			}
			if obj.type == "MESH":
				node["mesh"] = 0 #TODO ちゃんとしたIDを振る
				node["skin"] = 0 #TODO ちゃんとしたIDを振る
			return node
		nodes = []
		scene = []
		skins = []
		for obj_id,obj in enumerate(bpy.context.selected_objects):
			if obj.type =="MESH":
				nodes.append(mesh_object_to_node(obj))
				scene.append(obj_id)
			if obj.type =="ARMATURE":
				bone_id_dic = {b.name : obj_id + bone_id for bone_id,b in enumerate(obj.data.bones)}
				def bone_to_node(b_bone):
					node = {
						"name":b_bone.name,
						"translation":axis_blender_to_glb([b_bone.parent.head_local[i] - b_bone.head_local[i] for i in range(3)]),
						"rotation":[0,0,0,1],
						"scale":[1,1,1],
						"children":[bone_id_dic[child.name] for child in b_bone.children]
					}
					return node
				for bone in obj.data.bones:
					if bone.parent is None: #root bone
						root_bone_id = bone_id_dic[bone.name]
						skin = {"joints":[root_bone_id]}
						skin["skelton"] = root_bone_id
						scene.append(root_bone_id)
						nodes.append(bone_to_node(bone))
						bone_children = bone.children
						while bone_children:
							child = bone_children.pop()
							nodes.append(bone_to_node(child))
							skin["joints"].append(bone_id_dic[child.name])
							bone_children.extend(child.children)
						skins.append(skin)

		self.json_dic.update({"scenes":[{"nodes":scene}]})
		self.json_dic.update({"nodes":nodes})
		self.json_dic.update({"skins":skins})
		return 

	def image_to_bin(self):
		for image in bpy.data.images:
			with open(image.filepath_from_user(),"rb") as f:
				image_bin = f.read()
			name = image.name
			Image_bin(image_bin,name,self.glb_bin_collector)
		return

	def texture_to_dic(self):
		self.json_dic["samplers"] = [{
            "magFilter": GL_CONSTANS.LINEAR, #TODO 決め打ちすんな？
            "minFilter": GL_CONSTANS.LINEAR,
            "wrapS": REPEAT,
            "wrapT": REPEAT
        }]
		textures = []
		for id in range(len(self.glb_bin_collector.image_bins)):
			texture = {
				"sampler":0,
				"source": id
			}
			textures.append(texture)
		self.json_dic.update({"textures":textures})
		return


	def material_to_dic(self):
		material_list = []
		for b_mat in bpy.data.materials:
			mat_dic = {}
			mat_dic["name"] = b_mat.name
			#TODO do something
			material_list.append(mat_dic)
		self.json_dic.update({"materials" : material_list})
		return

	def mesh_to_bin_and_dic(self):
		for id,mesh in enumerate([obj for obj in bpy.context.selected_objects if obj.type == "MESH"]):
			self.json_dic["nodes"].append({
					"name":mesh.name,
					"translation":mesh.location, #原点にいてほしいけどね
					"rotation":[0,0,0,1],	#このへんは規約なので
					"scale":[1,1,1],		#このへんは規約なので
					"mesh":id,
					"skin":0 #TODO　決め打ちってどうよ：一体のモデルなのだから２つもあっては困る(から決め打ち(やめろ(やだ))
				})
			#region hell
			mesh.hide = False
			mesh.hide_select = False
			bpy.context.scene.objects.active = mesh
			bpy.ops.object.mode_set(mode='EDIT')
			bm = bmesh.from_edit_mesh(mesh.data)

			#region tempolary_used
			mat_id_dic = {mat.name:id for id,mat in enumerate(self.json_dic["materials"])} 
			material_slot_dic = {id:mat.name for mat in mesh.material_slots} 
			node_id_dic = {node["name"]:id for node in self.json_dic["nodes"]} 
			def joint_id_from_node_name_solver(node_name):
				node_id = node_id_dic[node_name]
				skin_id = self.json_dic["skins"][0]["joints"].index(node_id)
				return skin_id
			v_group_name_dic = {id:vg.name for vg in mesh.vertex_groups}
			fmin,fmax = sys.float_info.min,sys.float_info.max
			unique_vertex_id = 0
			unique_vertex_id_dic = {} #loop verts id : base vertex id (uv違いを同じ頂点番号で管理されているので)
			uvlayers_dic = {id:uvlayer.name for id,uvlayer in enumerate(mesh.uv_layers)}
			#endregion  tempolary_used
			primitive_index_bin_dic = OrderedDict({id:b"" for id in range(len(self.json_dic["materials"]))})
			shape_bin_dic = OrderedDict({shape.name:b"" for shape in mesh.data.shape_keys.key_blocks[1:]})#0番目Basisは省く
			shape_min_max_dic = OrderedDict({shape.name:[[fmax,fmax,fmax],[fmin,fmin,fmin]] for shape in mesh.data.shape_keys.key_blocks})
			position_bin =b""
			position_min_max = [[fmax,fmax,fmax],[fmin,fmin,fmin]]
			normal_bin = b""
			joints_bin = b""
			weights_bin = b""
			texcord_bins = {id:b"" for id in uvlayers_dic.keys()}
			f_vec4_packer = struct.Struct("<ffff")
			f_vec3_packer = struct.Struct("<fff")
			f_pair_packer = struct.Struct("<ff")
			I_scalar_packer = struct.Struct("<I")
			I_vec4_packer = struct.Struct("<IIII")
			def min_max(minmax,position):
				for i in range(3):
					minmax[0][i] = vert_location[i] if vert_location[i] < minmax[0][i] else minmax[0][i]
					minmax[1][i] = vert_location[i] if vert_location[i] > minmax[1][i] else minmax[1][i]
				return
			for face in bm.faces:
				#このへん絶対超遅い
				for loop in face.loops:
					for id,uvlayer_name in uvlayers_dic.items():
						uv_layer = bm.loops.layers.uv[uvlayer_name]
						uv = loop[uv_layer].uv
						texcord_bins[id] += f_pair_packer(uv[0],-uv[1]) #blenderとglbのuvは上下逆
					for shape_name,shape_bin in shape_bin_dic.items(): 
						shape_layer = bm.verts.layers.shape[shape_name]
						vert_location = axis_blender_to_glb( [loop.vert[shape_layer][i] - loop.vert.co[i] for i in range(3)])
						shape_bin += f_vec3_packer(vert_location)
						min_max(shape_min_max_dic[shape_name,vert_location])
					weights = [0.0, 0.0, 0.0, 0.0]
					magic = 9999999
					joints = [magic,magic,magic,magic]
					for v_group in mesh.data.vertices[loop.vert.index].groups:						
							weights.remove(3)
							weights.insert(0,v_group.weight)
							joints.remove(3)
							joints.insert(0,joint_id_from_node_name_solver(v_group_name_dic[v_group.group]))
					joints_bin += I_vec4_packer(joints)
					weights_bin += f_vec4_packer(weights) 
					vert_location = axis_blender_to_glb(loop.vert.co)
					position_bin += f_vec3_packer(vert_location)
					min_max(position_min_max,vert_location)
					normal_bin += f_vec3_packer(axis_blender_to_glb(loop.vert.normal))
					unique_vertex_id_dic[unique_vertex_id,vert.index]
					primitive_index_bin_dic[mat_id_dic[material_slot_dic[face.material_index]]] += I_scalar_packer(unique_vertex_id)
				unique_vertex_id += 1
			#DONE :index position, uv, normal, position morph,JOINT WEIGHT  
			#TODO morph_normal, color...?
			primitive_glbs_dic = OrderedDict({id:Glb_bin(index_bin,"SCALAR",GL_CONSTANS.UNSIGNED_INT,unique_vertex_id,None,self.glb_bin_collector)})
			pos_glb = Glb_bin(position_bin,"VEC3",GL_CONSTANS.FLOAT,unique_vertex_id,position_min_max,self.glb_bin_collector)
			nor_glb = Glb_bin(normal_bin,"VEC3",GL_CONSTANS.FLOAT,unique_vertex_id,None,self.glb_bin_collector)
			uv_glbs = [
				Glb_bin(texcood_bin,"VEC2",GL_CONSTANS.FLOAT,unique_vertex_id,None,self.glb_bin_collector)
					for texcood_bin in texcord_bins.values()]
			joints_glb = Glb_bin(joints_bin,"VEC4",GL_CONSTANS.UNSIGNED_INT,unique_vertex_id,None,self.glb_bin_collector)
			weights_glb = Glb_bin(weights_bin,"VEC4",GL_CONSTANS.FLOAT,unique_vertex_id,None,self.glb_bin_collector)
			morph_glbs = [Glb_bin(morph_pos_bin,"VEC3",GL_CONSTANS.FLOAT,unique_vertex_id,morph_minmax,self.glb_bin_collector) 
						for morph_pos_bin,morph_minmax in zip(shape_bin_dic.values(),shape_min_max_dic.values())
						]
			primitive_list = []
			for primitive_id,index_glb in primitive_glbs_dic.items():
				primitive = {"mode":4}
				primitive["material"] = primitive_id
				primitive["indices"] = index_glb.accessor_id
				primitive["attributes"] = {
					"POSITION":pos_glb.accessor_id,
					"NORMAL":nor_glb.accessor_id,
					"JOINTS_0":joints_glb.accessor_id,
					"WEIGHTS_0":weights_glb.accessor_id
				}
				primitive["attributes"].update({"TEXCOORD_{}".format(i):uv_glb for i,uv_glb in enumerate(uv_glbs)})
				primitive["targets"]=[OrderedDict({"POSITION":morph_glb for morph_glb in morph_glbs})]
				primitive["extras"] = {"targetNames":[shape.name for shape in shape_bin_dic.keys()]} 

			
			#endregion hell
		return



	def glTF_meta_to_dic(self):
		glTF_meta_dic = {
			"extensionsUsed":["VRM"],
			"asset":{
				"generator":"icyp_blender_vrm_exporter_experimental_0.0",
				"version":"2.0"
				}
			}

		self.json_dic.update(glTF_meta_dic)
		return

	def finalize(self):
		bin_json, self.bin = self.glb_bin_collector.pack_all()
		self.json_dic.update(bin_json)
		magic = b'glTF' + struct.pack('<I', 2)
		json_str = json.dumps(self.json_dic).encode("utf-8")
		json_size = struct.pack("<I", len(json_str))
		bin_size = struct.pack("<I",len(self.bin))
		total_size = struct.pack("<I",len(json_str) + len(self.bin))
		self.result = magic + total_size + \
				json_size + b"JSON" + json_str + \
				bin_size + b'BIN\x00' + self.bin
		return


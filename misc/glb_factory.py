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
from sys import float_info
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
		self.mesh_to_bin_and_dic() 
		self.json_dic["scene"] = [0]
		self.glTF_meta_to_dic()
		self.vrm_meta_to_dic() #colliderとかmetaとか....
		self.finalize()
		return self.result
	@staticmethod
	def axis_blender_to_glb(vec3):
		return [vec3[i]*t for i,t in zip([0,2,1],[-1,1,1])]

	def armature_to_node_and_scenes_dic(self):
		nodes = []
		scene = []
		skins = []
		for obj_id,obj in enumerate(bpy.context.selected_objects):
			if obj.type =="ARMATURE":
				bone_id_dic = {b.name : bone_id for bone_id,b in enumerate(obj.data.bones)}
				def bone_to_node(b_bone):
					parent_head_local = b_bone.parent.head_local if b_bone.parent is not None else [0,0,0]
					node = OrderedDict({
						"name":b_bone.name,
						"translation":self.axis_blender_to_glb([b_bone.head_local[i] - parent_head_local[i] for i in range(3)]),
						"rotation":[0,0,0,1],
						"scale":[1,1,1],
						"children":[bone_id_dic[ch.name] for ch in b_bone.children]
					})
					if len(node["children"]) == 0:
						node.pop("children")
					return node
				for bone in obj.data.bones:
					if bone.parent is None: #root bone
						root_bone_id = bone_id_dic[bone.name]
						skin = {"joints":[root_bone_id]}
						skin["skeleton"] = root_bone_id
						scene.append(root_bone_id)
						nodes.append(bone_to_node(bone))
						bone_children = [b for b in bone.children]
						while bone_children :
							child = bone_children.pop()
							nodes.append(bone_to_node(child))
							skin["joints"].append(bone_id_dic[child.name])
							bone_children += [ch for ch in child.children]
						nodes = sorted(nodes,key=lambda node: bone_id_dic[node["name"]])
						skins.append(skin)
						break

		self.json_dic.update({"scenes":[{"nodes":scene}]})
		self.json_dic.update({"nodes":nodes})
		self.json_dic.update({"skins":skins})
		return 

	def image_to_bin(self):
		for image in bpy.data.images:
			with open(image.filepath_from_user(),"rb") as f:
				image_bin = f.read()
			name = image.name
			filetype = "image/"+image.file_format.lower()
			Image_bin(image_bin,name,filetype,self.glb_bin_collector)
		return

	def texture_to_dic(self):
		self.json_dic["samplers"] = [{
            "magFilter": GL_CONSTANS.LINEAR, #TODO 決め打ちすんな？
            "minFilter": GL_CONSTANS.LINEAR,
            "wrapS": GL_CONSTANS.REPEAT,
            "wrapT": GL_CONSTANS.REPEAT
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
		self.json_dic["meshes"] = []
		for id,mesh in enumerate([obj for obj in bpy.context.selected_objects if obj.type == "MESH"]):
			self.json_dic["nodes"].append(OrderedDict({
					"name":mesh.name,
					"translation":[mesh.location[i] for i in range(3)], #原点にいてほしいけどね, vectorのままだとjsonに出来ないからこうする
					"rotation":[0,0,0,1],	#このへんは規約なので
					"scale":[1,1,1],		#このへんは規約なので
					"mesh":id,
					"skin":0 #TODO　決め打ちってどうよ：一体のモデルなのだから２つもあっては困る(から決め打ち(やめろ(やだ))
				}))
			self.json_dic["scenes"][0]["nodes"].append(len(self.json_dic["nodes"])-1)
			#region hell
			bpy.ops.object.mode_set(mode='OBJECT')
			mesh.hide = False
			mesh.hide_select = False
			bpy.context.scene.objects.active = mesh
			bpy.ops.object.mode_set(mode='EDIT')
			bm = bmesh.from_edit_mesh(mesh.data)

			#region tempolary_used
			mat_id_dic = {mat["name"]:i for i,mat in enumerate(self.json_dic["materials"])} 
			material_slot_dic = {i:mat.name for i,mat in enumerate(mesh.material_slots)} 
			node_id_dic = {node["name"]:i for i,node in enumerate(self.json_dic["nodes"])} 
			def joint_id_from_node_name_solver(node_name):
				node_id = node_id_dic[node_name]
				skin_id = self.json_dic["skins"][0]["joints"].index(node_id)
				return skin_id
			v_group_name_dic = {i:vg.name for i,vg in enumerate(mesh.vertex_groups)}
			fmin,fmax = float_info.min,float_info.max
			unique_vertex_id = 0
			unique_vertex_id_dic = {} #loop verts id : base vertex id (uv違いを同じ頂点番号で管理されているので)
			uvlayers_dic = {i:uvlayer.name for i,uvlayer in enumerate(mesh.data.uv_layers)}
			#endregion  tempolary_used
			primitive_index_bin_dic = OrderedDict({mat_id_dic[mat.name]:b"" for mat in mesh.material_slots})
			primitive_index_vertex_count = OrderedDict({mat_id_dic[mat.name]:0 for mat in mesh.material_slots})
			if mesh.data.shape_keys is None : 
				shape_bin_dic = {}
				shape_min_max_dic = {}
			else:
				shape_bin_dic = OrderedDict({shape.name:b"" for shape in mesh.data.shape_keys.key_blocks[1:]})#0番目Basisは省く
				shape_min_max_dic = OrderedDict({shape.name:[[fmax,fmax,fmax],[fmin,fmin,fmin]] for shape in mesh.data.shape_keys.key_blocks})
			position_bin =b""
			position_min_max = [[fmax,fmax,fmax],[fmin,fmin,fmin]]
			normal_bin = b""
			joints_bin = b""
			weights_bin = b""
			texcord_bins = {id:b"" for id in uvlayers_dic.keys()}
			f_vec4_packer = struct.Struct("<ffff").pack
			f_vec3_packer = struct.Struct("<fff").pack
			f_pair_packer = struct.Struct("<ff").pack
			I_scalar_packer = struct.Struct("<I").pack
			H_vec4_packer = struct.Struct("<HHHH").pack

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
					for shape_name in shape_bin_dic.keys(): 
						shape_layer = bm.verts.layers.shape[shape_name]
						vert_location = self.axis_blender_to_glb( [loop.vert[shape_layer][i] - loop.vert.co[i] for i in range(3)])
						shape_bin_dic[shape_name] += f_vec3_packer(*vert_location)
						min_max(shape_min_max_dic[shape_name],vert_location)
					magic = 0
					joints = [magic,magic,magic,magic]
					weights = [0.0, 0.0, 0.0, 0.0]
					for v_group in mesh.data.vertices[loop.vert.index].groups:						
							weights.pop()
							weights.insert(0,v_group.weight)
							joints.pop(3)
							joints.insert(0,joint_id_from_node_name_solver(
								v_group_name_dic[v_group.group])
								)
					joints_bin += H_vec4_packer(*joints)
					weights_bin += f_vec4_packer(*weights) 
					vert_location = self.axis_blender_to_glb(loop.vert.co)
					position_bin += f_vec3_packer(*vert_location)
					min_max(position_min_max,vert_location)
					normal_bin += f_vec3_packer(*self.axis_blender_to_glb(loop.vert.normal))
					unique_vertex_id_dic[unique_vertex_id]=loop.vert.index
					primitive_index_bin_dic[mat_id_dic[material_slot_dic[face.material_index]]] += I_scalar_packer(unique_vertex_id)
					primitive_index_vertex_count[mat_id_dic[material_slot_dic[face.material_index]]] +=1
					unique_vertex_id += 1
				
			#DONE :index position, uv, normal, position morph,JOINT WEIGHT  
			#TODO morph_normal, color...?
			primitive_glbs_dic = OrderedDict({
				mat_id:Glb_bin(index_bin,"SCALAR",GL_CONSTANS.UNSIGNED_INT,primitive_index_vertex_count[mat_id],None,self.glb_bin_collector)
				for mat_id,index_bin in primitive_index_bin_dic.items() if index_bin !=b""
			})
			pos_glb = Glb_bin(position_bin,"VEC3",GL_CONSTANS.FLOAT,unique_vertex_id,position_min_max,self.glb_bin_collector)
			nor_glb = Glb_bin(normal_bin,"VEC3",GL_CONSTANS.FLOAT,unique_vertex_id,None,self.glb_bin_collector)
			uv_glbs = [
				Glb_bin(texcood_bin,"VEC2",GL_CONSTANS.FLOAT,unique_vertex_id,None,self.glb_bin_collector)
					for texcood_bin in texcord_bins.values()]
			joints_glb = Glb_bin(joints_bin,"VEC4",GL_CONSTANS.UNSIGNED_SHORT,unique_vertex_id,None,self.glb_bin_collector)
			weights_glb = Glb_bin(weights_bin,"VEC4",GL_CONSTANS.FLOAT,unique_vertex_id,None,self.glb_bin_collector)
			if len(shape_bin_dic.keys()) != 0:
				morph_glbs = [Glb_bin(morph_pos_bin,"VEC3",GL_CONSTANS.FLOAT,unique_vertex_id,morph_minmax,self.glb_bin_collector) 
						for morph_pos_bin,morph_minmax in zip(shape_bin_dic.values(),shape_min_max_dic.values())
						]
			primitive_list = []
			for primitive_id,index_glb in primitive_glbs_dic.items():
				primitive = OrderedDict({"mode":4})
				primitive["material"] = primitive_id
				primitive["indices"] = index_glb.accessor_id
				primitive["attributes"] = {
					"POSITION":pos_glb.accessor_id,
					"NORMAL":nor_glb.accessor_id,
					"JOINTS_0":joints_glb.accessor_id,
					"WEIGHTS_0":weights_glb.accessor_id
				}
				primitive["attributes"].update({"TEXCOORD_{}".format(i):uv_glb.accessor_id for i,uv_glb in enumerate(uv_glbs)})
				if len(shape_bin_dic.keys()) != 0:
					primitive["targets"]=[{"POSITION":morph_glb.accessor_id} for morph_glb in morph_glbs]
					primitive["extras"] = {"targetNames":[shape_name for shape_name in shape_bin_dic.keys()]} 
				primitive_list.append(primitive)
			self.json_dic["meshes"].append({"name":mesh.name,"primitives":primitive_list})
			#endregion hell
		bpy.ops.object.mode_set(mode='OBJECT')
			
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

	def vrm_meta_to_dic(self):
		vrm_extension_dic = OrderedDict()
		vrm_extension_dic["meta"] = vrm_meta_dic = {}
		vrm_extension_dic["humanoid"] = vrm_humanoid_dic = {}
		for obj in bpy.context.selected_objects:
			if obj.type =="ARMATURE":
				vrm_metas = [
					"version",
					"author",
					"contactInformation",
					"reference",
					"title",
					"allowedUserName",
					"violentUssageName",
					"sexualUssageName",
					"commercialUssageName",
					"otherPermissionUrl",
					"licenseName",
					"otherLicenseUrl"
				]
				for key in vrm_metas:
					vrm_meta_dic[key] = obj[key] if key in obj.keys() else ""
				vrm_meta_dic["textures"] = len(self.glb_bin_collector.image_bins)

				node_name_id_dic = {node["name"]:i for i, node in enumerate(self.json_dic["nodes"])}
				vrm_humanoid_dic["humanBones"] = []
				for bone in obj.data.bones:
					if "humanBone" in obj.keys():
						vrm_humanoid_dic["humanBones"].append({ 
							"bone": bone["humanBone"],
							"node":node_name_id_dic[bone.name],
							"useDefaultValues": True
						})


				self.json_dic.update({"extensions":{"VRM":vrm_extension_dic}})
				break
		#TODO add secondary animations set up and MToon

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


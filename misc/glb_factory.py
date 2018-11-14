"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
from .glb_bin_collector import Glb_bin_collection, Image_bin, Glb_bin
from collections import OrderedDict
import json
import struct
import bpy

class Glb_obj():
	def __init__(self):
		self.json_dic = OrderedDict()
		self.bin = b""
		self.glb_bin_collector = Glb_bin_collection()

	def convert_bpy2glb(self):
		#TODO
		self.armature_to_node_and_scenes_dic() #親のないboneは1つだけ as root_bone
		self.image_to_bin()
		#self.texture_to_dic() #sampler etc
		self.material_to_dic()
		#self.mesh_to_bin_and_dic() #add to node and scenes mesh_object
		self.json_dic["scene"] = [0]
		self.glTF_meta_to_dic()
		#self.vrm_meta_to_dic()
		return self.finalize()
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

	def material_to_dic(self):
		material_list = []
		for b_mat in bpy.data.materials:
			mat_dic = {}
			mat_dic["name"] = b_mat.name
			#TODO do something
			material_list.append(mat_dic)
		self.json_dic.update({"materials" : material_list})
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
		magic = b'glTF' + struct.pack('<I', 2)
		json_str = json.dumps(self.json_dic).encode("utf-8")
		json_size = struct.pack("<I", len(json_str))
		bin_size = struct.pack("<I",len(self.bin))
		total_size = struct.pack("<I",len(json_str) + len(self.bin))
		result = magic + total_size + \
				json_size + b"JSON" + json_str + \
				bin_size + b'BIN\x00' + self.bin
		return result


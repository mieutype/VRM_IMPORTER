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
		#self.object_to_node_and_scene_dic() #include bones to node
		#self.bones_to_skin_dic()
		#self.image_to_bin()
		#self.texture_to_dic() #sampler etc
		#self.material_to_dic()
		#self.mesh_to_bin_and_dic()
		self.json_dic["scenes"] = [0]
		#self.glTF_meta_to_dic()
		#self.vrm_meta_to_dic()
		return self.finalize()

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

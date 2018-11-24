"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
import bpy
import bmesh
import re
from math import sqrt, pow
from collections import deque
class Bones_rename(bpy.types.Operator):
    bl_idname = "vrm.bones_rename"
    bl_label = "convert Vroid_bones"
    bl_description = "convert Vroid_bones as blender type"
    bl_options = {'REGISTER', 'UNDO'}
    
    
    def execute(self, context):
        for x in bpy.context.active_object.data.bones:
            for RL in ["L","R"]:
                ma = re.match("(.*)_"+RL+"_(.*)",x.name)
                if ma:
                    tmp = ""
                    for y in ma.groups():
                        tmp += y + "_"
                    tmp += RL
                    x.name = tmp
        return {"FINISHED"}


import json
from collections import OrderedDict
import os

class Vroid2VRC_ripsync_from_json_recipe(bpy.types.Operator):
    bl_idname = "vrm.ripsync_vrm"
    bl_label = "make ripsync4VRC"
    bl_description = "make ripsync from Vroid to VRC by json"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        recipe_uri =os.path.join(os.path.dirname(__file__) ,"Vroid2vrc_ripsync_recipe.json")
        recipe = None
        with open(recipe_uri,"rt") as raw_recipe:
            recipe = json.loads(raw_recipe.read(),object_pairs_hook=OrderedDict)
        for shapekey_name,based_values in recipe["shapekeys"].items():
            for k in bpy.context.active_object.data.shape_keys.key_blocks:
                k.value = 0.0
            for based_shapekey_name,based_val in based_values.items():
                bpy.context.active_object.data.shape_keys.key_blocks[based_shapekey_name].value = based_val
            bpy.ops.object.shape_key_add(from_mix = True)
            bpy.context.active_object.data.shape_keys.key_blocks[-1].name = shapekey_name
        for k in bpy.context.active_object.data.shape_keys.key_blocks:
                k.value = 0.0
        return {"FINISHED"}


class VRM_VALIDATOR(bpy.types.Operator):
    bl_idname = "vrm.model_validate"
    bl_label = "check as VRM model"
    bl_description = "NO Quad_Poly & N_GON, NO unSkind Mesh etc..."
    bl_options = {'REGISTER', 'UNDO'}

    #TODO: UI & class register 

    def execute(self,context):
        armature_count = 0
        node_name_set = set()
        for obj in bpy.context.selected_objects:
            if obj.name in node_name_set:
                print("VRM exporter need Nodes(mesh,bones) name is unique")
            node_name_set.add(obj.name)
            if obj.location != [0,0,0]:#mesh and armature origin is on [0,0,0]
                print("There are not on origine location object {}".format(obj.name))
            if obj.type == "MESH":
                for poly in mesh.data.polygons:
                    if poly.loop_total > 3:#polygons need all triangle
                        print("There are non Triangle faces in {}".format(mesh.name))
                #TODO: material's images are saved check
            if obj.type == "ARMATURE":
                armature_count += 1
                if armature_count > 2:#only one armature
                    print("VRM expoter needs only one armature")
                already_root_bone_exist = False
                for bone in obj.data.bones:
                    if bone.name in node_name_set:#nodes name is unique
                        print("VRM exporter need Nodes(mesh,bones) name is unique")
                    node_name_set.add(bone.name)
                    if bone.parent == None: #root bone is only 1
                        if already_root_bone_exist:
                            print("root bone is only one {},{}".format(bone.name,already_root_bone_exist))
                        already_root_bone_exist = bone.name
                #TODO: T_POSE,
            
        
        return {"FINISHED"}
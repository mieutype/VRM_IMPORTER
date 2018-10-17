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

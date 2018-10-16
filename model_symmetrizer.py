"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
import bpy
import bmesh
from math import sqrt, pow
from collections import deque
class Symmetrizer(bpy.types.Operator):
    bl_idname = "vrm.symmetraizer"
    bl_label = "x_axis based symmetraize"
    bl_description = "symmetraize"
    bl_options = {'REGISTER', 'UNDO'}
    


    
    def execute(self, context):
        target = context.active_object
        thoreshold = context.scene.vrm_thoreshold
        bm = bmesh.from_edit_mesh(target.data)
        vertslist = [v for v in bm.verts]
        def distance(co1, co2):
            return sqrt(pow(co1[0]-co2[0],2)+pow(co1[1]-co2[1],2)+pow(co1[2]-co2[2],2))
        while vertslist:
            v = vertslist.pop()
            #中心寄りを寄せる
            if abs(v.co[0]) < thoreshold:
                v.co[0] = 0.0
                continue
            if not vertslist:
                break
            #x軸逆転で閾値未満かつもっとも近傍の頂点を逆側の頂点と同じにする
            x_invert_v_co = [-v.co[0],v.co[1],v.co[2]]
            symmetry_v = vertslist[0]
            nearest_dist = 1000000
            for vert in vertslist:
                dist = distance(vert.co, x_invert_v_co)
                if dist < nearest_dist:
                    nearest_dist = dist
                    symmetry_v = vert
            if nearest_dist <= thoreshold:
                symmetry_v.co = [-v.co[0], v.co[1], v.co[2]]
            vertslist.remove(symmetry_v)

        bmesh.update_edit_mesh(target.data)
        context.active_object.data.update()
        return {"FINISHED"}

def add_prop():
    bpy.types.Scene.vrm_thoreshold = bpy.props.FloatProperty(name = "thoreshold",default = 0.005,min=0.0)

def del_prop():
    del bpy.types.Scene.vrm_thoreshold
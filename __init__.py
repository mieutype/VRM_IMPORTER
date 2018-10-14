"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import bpy
from bpy_extras.io_utils import ImportHelper
from . import vrm_load,model_build
import os


bl_info = {
    "name":"VRM_IMPORTER",
    "author": "iCyP",
    "version": (0, 2),
    "blender": (2, 79, 0),
    "location": "File->Import",
    "description": "VRM Importer",
    "warning": "",
    "support": "TESTING",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Import-Export"
}


class ImportVRM(bpy.types.Operator,ImportHelper):
    bl_idname = "import.vrm"
    bl_label = "import VRM"
    bl_description = "import VRM"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = '.vrm'
    filter_glob = bpy.props.StringProperty(
        default='*.vrm',
        options={'HIDDEN'}
    )



    def execute(self,context):
        fdir = self.filepath
        model_build.vrm_model_build(vrm_load.read_vrm(fdir))
        return {'FINISHED'}


def menu_import(self, context):
    self.layout.operator(ImportVRM.bl_idname, text="VRM (.vrm)")



class VRM_HELPER(bpy.types.Operator):
    bl_idname = "vrm.float_error_fix"
    bl_label = "float error fix"
    bl_description = "centerize by active vertex"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        import bmesh
        bm = bmesh.from_edit_mesh(context.active_object.data)
        if len(bm.select_history) != 0:
            x_error = bm.select_history[-1].co[0]
            for v in bm.verts:
                v.co[0] -= x_error
            context.active_object.data.update()
            context.scene.update()
            bm.free()
            return {"FINISHED"}
        else:
            print("PLEASE SELECT CENTOR VERTS")
            return{"PASS_THROUGH"}


class UI_controller(bpy.types.Panel):
    bl_label = "vrm import helper"
    #どこに置くかの定義
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "VRM HELPER"

    @classmethod
    def poll(self, context):
        if context.mode == "EDIT_MESH":
            return True
        else:
            return False
    def draw(self, context):
        self.layout.operator("vrm.float_error_fix")



classes = (
    ImportVRM,
    VRM_HELPER,
    UI_controller
)


# アドオン有効化時の処理
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.INFO_MT_file_import.append(menu_import)
 


# アドオン無効化時の処理
def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_import)
    for cls in classes:
        bpy.utils.unregister_class(cls)

if "__main__" == __name__:
    register()
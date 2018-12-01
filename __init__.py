"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import bpy
from bpy_extras.io_utils import ImportHelper,ExportHelper
from .importer import vrm_load,model_build
from .misc import VRM_HELPER
from .misc import glb_factory
import os


bl_info = {
    "name":"VRM_IMPORTER",
    "author": "iCyP",
    "version": (0, 3),
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
    bl_idname = "import_scene.vrm"
    bl_label = "import VRM"
    bl_description = "import VRM"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = '.vrm'
    filter_glob = bpy.props.StringProperty(
        default='*.vrm',
        options={'HIDDEN'}
    )

    is_put_spring_bone_info = bpy.props.BoolProperty(name = "Put Collider Empty")


    def execute(self,context):
        fdir = self.filepath
        model_build.Blend_model(vrm_load.read_vrm(fdir),self.is_put_spring_bone_info)
        return {'FINISHED'}


def menu_import(self, context):
    op = self.layout.operator(ImportVRM.bl_idname, text="VRM (.vrm)")
    op.is_put_spring_bone_info = True

class ExportVRM(bpy.types.Operator,ExportHelper):
    bl_idname = "export_scene.vrm"
    bl_label = "export VRM"
    bl_description = "export VRM"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = '.vrm'
    filter_glob = bpy.props.StringProperty(
        default='*.vrm',
        options={'HIDDEN'}
    )

    def execute(self,context):
        fdir = self.filepath
        bin =  glb_factory.Glb_obj().convert_bpy2glb()
        with open(fdir,"wb") as f:
            f.write(bin)
        return {'FINISHED'}


def menu_export(self, context):
    op = self.layout.operator(ExportVRM.bl_idname, text="VRM (.vrm)")


class VRM_IMPORTER_UI_controller(bpy.types.Panel):
    bl_label = "vrm import helper"
    #どこに置くかの定義
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "VRM HELPER"

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        self.layout.label(text="if you select armature in object mode")
        self.layout.label(text="armature renamer is shown")
        self.layout.label(text="if you in MESH EDIT")
        self.layout.label(text="symmetry button is shown")
        self.layout.label(text="*symmetry is in default blender")
        if context.mode == "OBJECT":
            if context.active_object is not None:
                self.layout.operator(VRM_HELPER.VRM_VALIDATOR.bl_idname)
                if context.active_object.type == 'ARMATURE':
                    self.layout.label(icon ="ERROR" ,text="EXPERIMENTAL!!!")
                    self.layout.operator(VRM_HELPER.Bones_rename.bl_idname)
                if context.active_object.type =="MESH":
                        self.layout.label(icon="ERROR",text="EXPERIMENTAL！お試し版。あてにしない")
                        self.layout.operator(VRM_HELPER.Vroid2VRC_ripsync_from_json_recipe.bl_idname)
        if context.mode == "EDIT_MESH":
            self.layout.operator(bpy.ops.mesh.symmetry_snap.idname_py())




classes = (
    ImportVRM,
    ExportVRM,
    VRM_HELPER.Bones_rename,
    VRM_HELPER.Vroid2VRC_ripsync_from_json_recipe,
    VRM_HELPER.VRM_VALIDATOR,
    VRM_IMPORTER_UI_controller
)


# アドオン有効化時の処理
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.INFO_MT_file_import.append(menu_import)
    bpy.types.INFO_MT_file_export.append(menu_export)
    
 


# アドオン無効化時の処理
def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_export)
    bpy.types.INFO_MT_file_import.remove(menu_import)
    for cls in classes:
        bpy.utils.unregister_class(cls)

if "__main__" == __name__:
    register()

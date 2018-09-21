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


# アドオン有効化時の処理
def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_import)
 


# アドオン無効化時の処理
def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_import)
    bpy.utils.unregister_module(__name__)

if "__main__" == __name__:
    register()
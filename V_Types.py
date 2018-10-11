"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
class VRM_pydata(object):
    def __init__(
            self,
            filepath = None,json = None,binaryReader = None,
            image_propaties = None,meshes =None,materials = None,
            bones_dict = None,origine_bones_dict = None, skins_joints_list = None
            ):
        self.filepath = filepath
        self.json = json
        self.binaryReader = binaryReader
        
        self.image_propaties = image_propaties if image_propaties is not None else []
        self.meshes = meshes if meshes is not None else []
        self.materials = materials if materials is not None else []
        self.bones_dict = bones_dict if bones_dict is not None else {}
        self.origine_bones_dict = origine_bones_dict if origine_bones_dict is not None else {}
        self.skins_joints_list = skins_joints_list if skins_joints_list is not None else []


class Mesh(object):
    def __init__(self):
        self.name = ""
        self.face_indices = []
        self.skin_id = None
        self.object_id = None



class Bone(object):
    def __init__(self):
        self.name = ""
        self.position = None
        self.rotation = None
        self.scale = None
        self.children = None



class Image_props(object):
    def __init__(self,name,filepath,fileType):
        self.name = name
        self.filePath = filepath
        self.fileType = fileType




class Material(object):
    def __init__(self):
        self.name = ""
        self.base_color = (1,1,1,1)
        self.color_texture_index = None
        self.color_texcoord_index = None
        self.normal_texture_index = None
        self.normal_texcoord_index = None
        self.displace_texture_index = None
        self.displace_texcoord_index = None
        self.doubleSided = True

if "__main__" == __name__:
    pass

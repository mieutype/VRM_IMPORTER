"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
class VRM_model:
    def __init__(
            self,filepath = None,json = None,binaryReader = None,
            image_propaties = [],meshes =[],materials = [],
            bones_dict = {},origine_bones_dict = {}, skins_joints_list = []
            ):
        self.filepath = filepath
        self.json = json
        self.binaryReader = binaryReader
        self.image_propaties = image_propaties
        self.meshes = meshes
        self.materials = materials
        self.bones_dict = bones_dict
        self.origine_bones_dict = origine_bones_dict
        self.skins_joints_list = skins_joints_list





class Mesh:
    def __init__(self):
        self.name = ""
        self.face_indices = []
        self.skin_id = None
        self.mesh_object_id = None
    def addAttribute(self,dic):
        for key,val in dic.items():
            setattr(self,key,val)



class Bone:
    def __init__(self,node):
        self.name = node["name"]
        self.position = node["translation"]
        self.rotation = node["rotation"]
        self.scale = node["scale"]
        if "children" in node:
            if type(node["children"]) is int:
                self.children = []
                self.children.append(node["children"])
            else:
                self.children = node["children"]
        else:
            self.children = None



class Image_props:
    def __init__(self,name,filepath,fileType):
        self.name = name
        self.filePath = filepath
        self.fileType = fileType




class Material:
    base_color = (1,1,1,1)
    color_texture_index = None
    color_texcoord_index = None
    normal_texture_index = None
    displace_texture_index = None

    def __init__(self,material):
        self.name = material["name"]
        if "pbrMetallicRoughness" in material:
            self.color_texture_index = material["pbrMetallicRoughness"]["baseColorTexture"]["index"]
            self.color_texcoord_index= material["pbrMetallicRoughness"]["baseColorTexture"]["texCoord"]
            if "baseColorFactor" in material["pbrMetallicRoughness"]:
                self.base_color = material["pbrMetallicRoughness"]["baseColorFactor"]

if "__main__" == __name__:
    pass

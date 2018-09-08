"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

class Mesh:
    def __init__(self):
        self.name = ""
        self.face_indices = []
        self.skin_id = None
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
            self.base_color = material["pbrMetallicRoughness"]["baseColorFactor"]

if "__main__" == __name__:
    pass

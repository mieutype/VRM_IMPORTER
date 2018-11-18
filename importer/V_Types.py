"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""
class VRM_pydata(object):
    def __init__(
            self,
            filepath = None,json = None,decoded_binary = None,
            image_propaties = None,meshes =None,materials = None,
            nodes_dict = None,origine_nodes_dict = None,
            skins_joints_list = None , skins_root_node_list = None
            ):
        self.filepath = filepath
        self.json = json
        self.decoded_binary = decoded_binary

        self.image_propaties = image_propaties if image_propaties is not None else []
        self.meshes = meshes if meshes is not None else []
        self.materials = materials if materials is not None else []
        self.nodes_dict = nodes_dict if nodes_dict is not None else {}
        self.origine_nodes_dict = origine_nodes_dict if origine_nodes_dict is not None else {}
        self.skins_joints_list = skins_joints_list if skins_joints_list is not None else []
        self.skins_root_node_list = skins_root_node_list if skins_root_node_list is not None else []


class Mesh(object):
    def __init__(self):
        self.name = ""
        self.face_indices = []
        self.skin_id = None
        self.object_id = None



class Node(object):
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
        self.shader_name = ""
        self.base_color = (1,1,1,1)
        self.color_texture_index = None
        self.color_texcoord_index = None
        self.normal_texture_index = None
        self.normal_texcoord_index = None
        self.displace_texture_index = None
        self.displace_texcoord_index = None
        self.alpha_mode = "Z_TRANSPARENCY"
        self.doubleSided = True

if "__main__" == __name__:
    pass

"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

from . import V_Types as VRM_Types

def material(mat,materialPropaties)->VRM_Types.Material:
    v_mat = VRM_Types.Material()
    v_mat.name = mat["name"]
    if v_mat.name in materialPropaties:
        mat_prop = materialPropaties[v_mat.name]
        if mat_prop["shader"] == "VRM/MToon":
            pass
            #TODO MToon読み込み




    if "pbrMetallicRoughness" in mat:
        pbrmat = mat["pbrMetallicRoughness"]
        v_mat.color_texture_index = pbrmat["baseColorTexture"]["index"]
        v_mat.color_texcoord_index= pbrmat["baseColorTexture"]["texCoord"]
        if "baseColorFactor" in pbrmat:
            v_mat.base_color = pbrmat["baseColorFactor"]
        if "metallicFactor" in pbrmat:
            v_mat.metallicFactor = pbrmat["metallicFactor"]
        if "roughnessFactor" in pbrmat:
            v_mat.roughnessFactor = pbrmat["roughnessFactor"]
    if "doubleSided" in mat:
        v_mat.doubleSided = mat["doubleSided"]

    return v_mat



def bone(node)->VRM_Types.Bone:
    v_bone = VRM_Types.Bone()
    v_bone.name = node["name"]
    v_bone.position = node["translation"]
    v_bone.rotation = node["rotation"]
    v_bone.scale = node["scale"]
    if "children" in node:
        if type(node["children"]) is int:
            v_bone.children = []
            v_bone.children.append(node["children"])
        else:
            v_bone.children = node["children"]
    else:
        v_bone.children = None
    return v_bone
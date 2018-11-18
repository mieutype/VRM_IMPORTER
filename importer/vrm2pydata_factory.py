"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

from . import V_Types as VRM_Types

def material(mat,materialPropaties,textures)->VRM_Types.Material:
    v_mat = VRM_Types.Material()
    v_mat.name = mat["name"]

    if "pbrMetallicRoughness" in mat:
        pbrmat = mat["pbrMetallicRoughness"]
        v_mat.shader_name = "pbr"
        if "baseColorTexture" in pbrmat:
            texture_index = pbrmat["baseColorTexture"]["index"]
            v_mat.color_texture_index = textures[texture_index]["source"]
            v_mat.color_texcoord_index= pbrmat["baseColorTexture"]["texCoord"]
        if "baseColorFactor" in pbrmat:
            v_mat.base_color = pbrmat["baseColorFactor"]
        if "metallicFactor" in pbrmat:
            v_mat.metallicFactor = pbrmat["metallicFactor"]
        if "roughnessFactor" in pbrmat:
            v_mat.roughnessFactor = pbrmat["roughnessFactor"]
    if "doubleSided" in mat:
        v_mat.doubleSided = mat["doubleSided"]
    if "alphaMode" in mat:
        if mat["alphaMode"] == "MASK":
            v_mat.alpha_mode = "MASK"
        if mat["alphaMode"] == "BLEND":
            v_mat.alpha_mode = "Z_TRANSPARENCY"
        if mat["alphaMode"] == "OPAQUE":
            v_mat.alpha_mode = "OPAQUE"


    def get_texture_index(matprop,attr):
        texture_index = None
        if attr in matprop["textureProperties"]:
            texture_index = matprop["textureProperties"][attr]
        return texture_index
    #拡張部分    
    #TODO　Emission_Color,shade_color等々は単純には再現不可なのでいつか
    try:
        EXT_props_name = [x["name"] for x in materialPropaties]
        prop_index = EXT_props_name.index(v_mat.name)
        mat_prop = materialPropaties[prop_index]
        if mat_prop["shader"] == "VRM/MToon":
            v_mat.shader_name = "VRM/MToon"
            if "_Color" in mat_prop:
                v_mat.base_color = mat_prop["_Color"]
            v_mat.color_texture_index = get_texture_index(mat_prop,"_MainTex")
            v_mat.normal_texture_index = get_texture_index(mat_prop,"_BumpMap")
            v_mat.normal_texcoord_index = 0
            #拡張テクスチャ
            sphere_id = get_texture_index(mat_prop,"_SphereAdd")
            if sphere_id is not None:
                v_mat.sphere_texture_index = sphere_id
            emission_id = get_texture_index(mat_prop,"_EmissionMap")
            if emission_id is not None:
                v_mat.emission_texture_index = emission_id
    except ValueError : #EXT_props_name.index(v_mat.name) でﾌﾟﾛﾊﾟﾃｨがないときはこれがくる
        print("{} material is not extension".format(v_mat.name))
    except Exception as e:
        print(e)
    return v_mat



def bone(node)->VRM_Types.Node:
    v_node = VRM_Types.Node()
    v_node.name = node["name"]
    v_node.position = node["translation"]
    v_node.rotation = node["rotation"]
    v_node.scale = node["scale"]
    if "children" in node:
        if type(node["children"]) is int:
            v_node.children = []
            v_node.children.append(node["children"])
        else:
            v_node.children = node["children"]
    else:
        v_node.children = None
    return v_node

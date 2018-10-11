"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

# codig :utf-8
#for python3.5 - for blender2.79
from .binaly_loader import Binaly_Reader
from .gl_const import GL_CONSTANS as GLC
from . import V_Types as VRM_Types
from . import pydata_factory
import os,re,copy
from math import sqrt,pow
import json
import numpy
from collections import OrderedDict




def parse_glb(data: bytes):
    reader = Binaly_Reader(data)
    magic = reader.read_str(4)
    if magic != b'glTF':
        raise Exception('magic not found: #{}'.format(magic))

    version = reader.read_as_dataType(GLC.UNSIGNED_INT)
    if version != 2:
        raise Exception('version:#{} is not 2'.format(version))

    size = reader.read_as_dataType(GLC.UNSIGNED_INT)
    size -= 12

    json_str = None
    body = None
    while size > 0:
        # print(size)

        if json_str is not None and body is not None:
            raise Exception('this vrm has chunks, this importer reads one chunk only.')

        chunk_size = reader.read_as_dataType(GLC.UNSIGNED_INT)
        size -= 4

        chunk_type = reader.read_str(4)
        size -= 4

        chunk_data = reader.read_binaly(chunk_size)
        size -= chunk_size

        if chunk_type == b'BIN\x00':
            body = chunk_data
        elif chunk_type == b'JSON':
            json_str = chunk_data.decode('utf-8')#blenderのpythonverが古く自前decode要す
        else:
            raise Exception('unknown chunk_type: {}'.format(chunk_type))

    return json.loads(json_str,object_pairs_hook=OrderedDict), body

#あくまでvrm(の特にバイナリ)をpythonデータ化するだけで、blender型に変形はここではしない
def read_vrm(model_path):
    vrm_pydata = VRM_Types.VRM_pydata(filepath=model_path)
    #datachunkは普通一つしかない
    with open(model_path, 'rb') as f:
        vrm_pydata.json, body_binary = parse_glb(f.read())
    vrm_pydata.binaryReader = Binaly_Reader(body_binary)
    
    #改変不可ﾗｲｾﾝｽを撥ねる
    if re.match("CC(.*)ND(.*)", vrm_pydata.json["extensions"]["VRM"]["meta"]["licenseName"]) is not None:
        raise Exception("This VRM is not allowed to Edit. CHECK ITS LICENSE　改変不可Licenseです。")
    #オリジナルライセンスに対する注意
    if vrm_pydata.json["extensions"]["VRM"]["meta"]["licenseName"] == "Other":
        print("Is this VRM allowed to Edit? CHECK IT LICENSE")
    
    texture_rip(vrm_pydata)
    mesh_read(vrm_pydata)
    material_read(vrm_pydata)
    node_read(vrm_pydata)
    skin_read(vrm_pydata)

    return vrm_pydata
    

def texture_rip(vrm_pydata):
    bufferViews = vrm_pydata.json["bufferViews"]
    accessors = vrm_pydata.json["accessors"]
    #ここ画像切り出し #blenderはバイト列から画像を読み込む術がないので、画像ファイルを書き出して、それを読み込むしかない。
    vrm_dir_path = os.path.dirname(os.path.abspath(vrm_pydata.filepath))
    for id,image_prop in enumerate(vrm_pydata.json["images"]):
        if "extra" in image_prop:
            image_name = image_prop["extra"]["name"]
        else :
            image_name = image_prop["name"]
        vrm_pydata.binaryReader.set_pos(bufferViews[image_prop["bufferView"]]["byteOffset"])
        image_binary = vrm_pydata.binaryReader.read_binaly(bufferViews[image_prop["bufferView"]]["byteLength"])
        image_type = image_prop["mimeType"].split("/")[-1]
        if image_name == "":
            image_name = "texture_" + str(id)
            print("no name image is named {}".format(image_name))
        image_path = os.path.join(vrm_dir_path, image_name + "." + image_type)
        if not os.path.exists(image_path):#すでに同名の画像がある場合は上書きしない
            with open(image_path, "wb") as imageWriter:
                imageWriter.write(image_binary)
        else:
            print(image_name + " Image is already exists. NOT OVER WRITTEN")
        image_propaty = VRM_Types.Image_props(image_name,image_path,image_type)
        vrm_pydata.image_propaties.append(image_propaty)

def mesh_read(vrm_pydata):
    bufferViews = vrm_pydata.json["bufferViews"]
    accessors = vrm_pydata.json["accessors"]
    #メッシュをパースする
    for n,mesh in enumerate(vrm_pydata.json["meshes"]):
        for j,primitive in enumerate(mesh["primitives"]):  
            vrm_mesh = VRM_Types.Mesh()
            vrm_mesh.object_id = n
            vrm_mesh.name = mesh["name"]+str(j)
            if primitive["mode"] != GLC.TRIANGLES:
                #TODO その他ﾒｯｼｭﾀｲﾌﾟ対応
                raise Exception("unSupported polygon type(:{}) Exception".format(primitive["mode"]))
                
            #まず、頂点indexを読む
            accessor = accessors[primitive["indices"]]
            vrm_pydata.binaryReader.set_pos(bufferViews[accessor["bufferView"]]["byteOffset"])
            for v in range(accessor["count"]):
                vrm_mesh.face_indices.append(vrm_pydata.binaryReader.read_as_dataType(accessor["componentType"]))
            #3要素ずつに変換しておく(GCL.TRIANGLES前提なので)
            #ＡＴＴＥＮＴＩＯＮ　これだけndarray
            vrm_mesh.face_indices = numpy.reshape(vrm_mesh.face_indices, (-1, 3))
            
            #ここから頂点属性
            def verts_attr_fuctory(accessor):  #data_lenghtは2以上(常にﾘｽﾄを返す)を想定
                type_num_dict = {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}
                type_num = type_num_dict[accessor["type"]]
                vrm_pydata.binaryReader.set_pos(bufferViews[accessor["bufferView"]]["byteOffset"])
                data_list = []
                for num in range(accessor["count"]):
                    data = []
                    for l in range(type_num):
                        data.append(vrm_pydata.binaryReader.read_as_dataType(accessor["componentType"]))
                    data_list.append(data)
                return data_list
            vertex_attributes = primitive["attributes"]
            #頂点属性は実装によっては存在しない属性（例えばJOINTSやWEIGHTSがなかったりもする）もあるし、UVや頂点カラー0->Nで増やせる（ｽｷﾆﾝｸﾞは1要素(ﾎﾞｰﾝ4本)限定
            for attr in vertex_attributes.keys():
                accessor = accessors[vertex_attributes[attr]]
                vrm_mesh.__setattr__(attr,verts_attr_fuctory(accessor))
            #region TEXCOORD_FIX [ 古いuniVRM誤り: uv.y = -uv.y ->修復 uv.y = 1 - ( -uv.y ) => uv.y=1+uv.y]
            #uvは0-1にある前提で、マイナスであれば変換ミスとみなす
            uv_count = 0
            while True:
                texcoordName = "TEXCOORD_{}".format(uv_count)
                if hasattr(vrm_mesh, texcoordName): 
                    texcoord = getattr(vrm_mesh,texcoordName)
                    for uv in texcoord:
                        if uv[1] < 0:
                            uv[1] = 1 + uv[1]
                    uv_count +=1
                else:
                    break

            #blenderとは上下反対のuv,それはblenderに書き込むときに直す
            #endregion TEXCOORD_FIX

            #マテリアルの場所を記録
            vrm_mesh.material_index = primitive["material"]
            #ここからモーフターゲット vrmのtargetは相対位置 normalは無視する
            if "targets" in primitive:
                morphTargetDict = dict()
                for i,morphTarget in enumerate(primitive["targets"]):
                    accessor = accessors[morphTarget["POSITION"]]
                    posArray = verts_attr_fuctory(accessor)
                    if "extra" in morphTarget:#for old AliciaSolid
                        morphTargetDict[primitive["targets"][i]["extra"]["name"]] = posArray
                    else:
                        morphTargetDict[primitive["extras"]["targetNames"][i]] = posArray
                vrm_mesh.__setattr__("morphTargetDict",morphTargetDict)

            vrm_pydata.meshes.append(vrm_mesh)


    #ここからマテリアル
def material_read(vrm_pydata):
    VRM_EXTENSION_material_promaties = None
    try:
        VRM_EXTENSION_material_promaties = vrm_pydata.json["extensions"]["VRM"]["materialProperties"]
    except Exception as e:
        print(e)
    for mat in vrm_pydata.json["materials"]:
        vrm_pydata.materials.append(pydata_factory.material(mat,VRM_EXTENSION_material_promaties))


    #node(ボーン)をﾊﾟｰｽする->親からの相対位置で記録されている
def node_read(vrm_pydata):
    for i,bone in enumerate(vrm_pydata.json["nodes"]):
        vrm_pydata.bones_dict[i] = pydata_factory.bone(bone)
        #TODO こっからorigine_bone
        if "mesh" in bone.keys():
            vrm_pydata.origine_bones_dict[i] = [vrm_pydata.bones_dict[i],bone["mesh"]]
            if "skin" in bone.keys():
                vrm_pydata.origine_bones_dict[i].append(bone["skin"])
            else:
                print(bone["name"] + "is not have skin")

    #skinをパース　->バイナリの中身はskining実装の横着用
    #skinのjointsの(nodesの)indexをvertsのjoints_0は指定してる
    #inverseBindMatrices: 単にｽｷﾆﾝｸﾞするときの逆行列。読み込み不要なのでしない(自前計算もできる、めんどいけど)
    #joints:JOINTS_0の指定node番号のindex
def skin_read(vrm_pydata):
    for skin in vrm_pydata.json["skins"]:
        vrm_pydata.skins_joints_list.append(skin["joints"])




if "__main__" == __name__:
    model_path = "./AliciaSolid\\AliciaSolid.vrm"
    model_path = "./Vroid\\Vroid.vrm"
    read_vrm(model_path)

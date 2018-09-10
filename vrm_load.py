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
import os,re,copy
from math import sqrt,pow
import json
import numpy
from collections import OrderedDict
import bpy, bmesh



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

#あくまでvrmをpythonデータ化するだけで、blender型に変形はここではしない（といったが現状それは嘘だ
def main(model_path):
    #datachunkは一つしかない前提
    vrm_parsed_json, body_binary = None,None
    with open(model_path, 'rb') as f:
        vrm_parsed_json, body_binary = parse_glb(f.read())
    binaly = Binaly_Reader(body_binary)
    
    #改変不可ﾗｲｾﾝｽを撥ねる
    if re.match("CC(.*)ND(.*)", vrm_parsed_json["extensions"]["VRM"]["meta"]["licenseName"]) is not None:
        raise Exception("This VRM is not allowed to Edit. CHECK ITS LICENSE　改変不可Licenseです。")
    #オリジナルライセンスに対する注意
    if vrm_parsed_json["extensions"]["VRM"]["meta"]["licenseName"] == "Other":
        print("Is this VRM allowed to Edit? CHECK IT LICENSE")
    
    bufferViews = vrm_parsed_json["bufferViews"]
    accessors = vrm_parsed_json["accessors"]
    #ここ画像切り出し #blenderはバイト列から画像を読み込む術がないので、画像ファイルを書き出して、それを読み込むしかない。
    vrm_image_props_list = []
    vrm_dir_path = os.path.dirname(os.path.abspath(model_path))
    for id,image_prop in enumerate(vrm_parsed_json["images"]):
        if "extra" in image_prop:
            image_name = image_prop["extra"]["name"]
        else :
            image_name = image_prop["name"]
        binaly.set_pos(bufferViews[image_prop["bufferView"]]["byteOffset"])
        image_binary = binaly.read_binaly(bufferViews[image_prop["bufferView"]]["byteLength"])
        image_type = image_prop["mimeType"].split("/")[-1]
        image_path = os.path.join(vrm_dir_path, image_name + "." + image_type)
        if not os.path.exists(image_path):#すでに同名の画像がある場合は上書きしない
            with open(image_path, "wb") as imageWriter:
                imageWriter.write(image_binary)
        else:
            print(image_name + " Image is already exists. NOT OVER WRITTEN")
        image_propaties = VRM_Types.Image_props(image_name,image_path,image_type)
        vrm_image_props_list.append(image_propaties)

    #メッシュをパースする
    vrm_meshes = []
    for n,mesh in enumerate(vrm_parsed_json["meshes"]):
        for i,primitive in enumerate(mesh["primitives"]):  
            vrm_mesh = VRM_Types.Mesh()
            vrm_mesh.mesh_id = n
            vrm_mesh.name = mesh["name"]+str(i)
            if primitive["mode"] != GLC.TRIANGLES:
                #TODO その他ﾒｯｼｭﾀｲﾌﾟ対応
                raise Exception("unSupported polygon type(:{}) Exception".format(primitive["mode"]))
                
            #まず、頂点indexを読む
            accessor = accessors[primitive["indices"]]
            binaly.set_pos(bufferViews[accessor["bufferView"]]["byteOffset"])
            for v in range(accessor["count"]):
                vrm_mesh.face_indices.append(binaly.read_as_dataType(accessor["componentType"]))
            #3要素ずつに変換しておく(GCL.TRIANGLES前提なので)
            #ＡＴＴＥＮＴＩＯＮ　これだけndarray
            vrm_mesh.face_indices = numpy.reshape(vrm_mesh.face_indices, (-1, 3))
            
            #ここから頂点属性
            def verts_attr_fuctory(accessor):  #data_lenghtは2以上(常にﾘｽﾄを返す)を想定
                type_num_dict = {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}
                type_num = type_num_dict[accessor["type"]]
                binaly.set_pos(bufferViews[accessor["bufferView"]]["byteOffset"])
                data_list = []
                for num in range(accessor["count"]):
                    data = []
                    for l in range(type_num):
                        data.append(binaly.read_as_dataType(accessor["componentType"]))
                    data_list.append(data)
                return data_list
            vertex_attributes = primitive["attributes"]
            #頂点属性が追加されたらここに書き足す↓(実装によっては存在しない属性もあるし、UVやｽｷﾆﾝｸﾞ情報は0->Nで増やせるが今は決め打ち)
            vertex_attributes_name =["POSITION","NORMAL","TANGENT","TEXCOORD_0","JOINTS_0","WEIGHTS_0"]
            for attr in vertex_attributes_name:
                if not attr in vertex_attributes:
                    print("this vrm_mesh {} doesn't have {} key".format(vrm_mesh.name,attr))
                    continue
                accessor = accessors[vertex_attributes[attr]]
                vrm_mesh.addAttribute({attr:verts_attr_fuctory(accessor)})
            #TEXCOORD_FIX [ 古いuniVRM誤り: uv.y = -uv.y ->修復 uv.y = 1 - ( -uv.y ) => uv.y=1+uv.y]
            #uvは0-1にある前提で、マイナスであれば変換ミスとみなす
            for uv in vrm_mesh.TEXCOORD_0:
                if uv[1] < 0:
                    uv[1] = 1 + uv[1]
            #blenderとは上下反対のuv,それはblenderに書き込むときに直す

            #マテリアルの場所を記録
            vrm_mesh.material_index = primitive["material"]
            #TODO ここからモーフターゲット vrmのtargetは相対位置
            if "targets" in primitive:
                morphTargetDict = dict()
                for i,morphTarget in enumerate(primitive["targets"]):
                    accessor = accessors[morphTarget["POSITION"]]
                    posArray = verts_attr_fuctory(accessor)
                    if "extra" in morphTarget:#for old AliciaSolid
                        morphTargetDict[primitive["targets"][i]["extra"]["name"]] = posArray
                    else:
                        morphTargetDict[primitive["extras"]["targetNames"][i]] = posArray
                vrm_mesh.addAttribute({"morphTargetDict":morphTargetDict})

            vrm_meshes.append(vrm_mesh)
    #ここからマテリアル
    vrm_materials = []
    for mat in vrm_parsed_json["materials"]:
        vrm_materials.append( VRM_Types.Material(mat))


    #node(ボーン)をﾊﾟｰｽする->親からの相対位置で記録されている
    vrm_bones = dict()
    origin_bone = dict()
    for i,bone in enumerate(vrm_parsed_json["nodes"]):
        vrm_bones[i]=VRM_Types.Bone(bone)
        #TODO こっからorigine_bone
        if "mesh" in bone.keys():
            origin_bone[i] = [vrm_bones[i],bone["mesh"]]
            if "skin" in bone.keys():
                origin_bone[i].append(bone["skin"])
            else:
                print(bone["name"] + "is not have skin")
    #TODO　skinをパースしてみる　->バイナリの中身はskining実装の横着用
    #TODO  skinのjointsの(nodesの)indexをvertsのjoints_0は指定してる
    def skin_attr_fuctory(accessor):  #data_lenghtは2以上(常にﾘｽﾄを返す)を想定
        type_num_dict = {"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}
        type_num = type_num_dict[accessor["type"]]
        binaly.set_pos(bufferViews[accessor["bufferView"]]["byteOffset"])
        data_list = []
        for num in range(accessor["count"]):
            data = []
            for l in range(type_num):
                data.append(binaly.read_as_dataType(accessor["componentType"]))
            data_list.append(data)
        return data_list
    vrm_skins_inverseBindMatrices_list = []
    vrm_skins_nodes_list = []
    #inverseBindMatrices: 単にｽｷﾆﾝｸﾞするときの逆行列。
    #省略されることもある。正直読み込み不要(自前計算できるので)
    #joints:JOINTS_0の指定node番号のindex
    for skin in vrm_parsed_json["skins"]:
        #accessor = accessors[skin["inverseBindMatrices"]]
        #vrm_skins_inverseBindMatrices_list.append(numpy.reshape(skin_attr_fuctory(accessor),(-1,4,4)))
        vrm_skins_nodes_list.append(skin["joints"])


    

#-------------------------------bpy zone  別クラスにしたい--------------------
    #image_path_to Texture
    textures = []
    for image_props in vrm_image_props_list:
        img = bpy.data.images.load(image_props.filePath)
        tex = bpy.data.textures.new(image_props.name,"IMAGE")
        tex.image = img
        textures.append(tex)
        
    #build bones as armature
    bpy.ops.object.add(type='ARMATURE', enter_editmode=True, location=(0,0,0))
    amt = bpy.context.object
    amt.name = vrm_parsed_json["extensions"]["VRM"]["meta"]["title"]
    bones = dict()
    def bone_chain(id,parentID):
        if id == -1:
            pass
        else:
            vb = vrm_bones_copy.pop(id)
            b = amt.data.edit_bones.new(vb.name)
            if parentID == -1:
                parentPos = [0,0,0]
            else:
                parentPos = bones[parentID].head
            b.head = numpy.array(parentPos)+numpy.array(vb.position)
            #temprary tail pos(gltf doesn't have bone. it defines as joints )
            #gltfは関節で定義されていて骨の長さとか向きとかないからまあなんかそれっぽい方向にボーンを向けて伸ばしたり縮めたり
            if vb.children == None:
                if parentID == -1:#唯我独尊：上向けとけ
                    b.tail = [b.head[0],b.head[1]+0.05,b.head[2]]
                else:#normalize lenght to 0.03　末代：親から距離をちょっととる感じ
                    lengh = sqrt(pow(vb.position[0],2)+pow(vb.position[1],2)+pow(vb.position[2],2))
                    lengh *= 30
                    if lengh <= 0.01:#0除算除けと気分
                        lengh =0.01
                    posDiff = [vb.position[0]/lengh,vb.position[1]/lengh,vb.position[2]/lengh]
                    if posDiff == [0.0,0.0,0.0]:
                        posDiff[1] += 0.01 #ボーンの長さが0だとOBJECT MODEに戻った時にボーンが消えるので上向けとく
                    b.tail = [b.head[0]+posDiff[0],b.head[1]+posDiff[1],b.head[2]+posDiff[2]]
            else:#子供たちの方向の中間を見る
                mean_relate_pos = [0,0,0]
                count=0
                for childID in vb.children:
                    count +=1
                    mean_relate_pos[0] += vrm_bones[childID].position[0]
                    mean_relate_pos[1] += vrm_bones[childID].position[1]
                    mean_relate_pos[2] += vrm_bones[childID].position[2]
                mean_relate_pos[0] /= count
                mean_relate_pos[1] /= count
                mean_relate_pos[2] /= count
                b.tail = [b.head[0]+mean_relate_pos[0],b.head[1]+mean_relate_pos[1],b.head[2]+mean_relate_pos[2]]
                    
            #end tail pos    
            bones[id] = b
            if parentID != -1:
                b.parent = bones[parentID]
            if vb.children != None:
                    for x in vb.children:
                        bone_chain(x,id)
            return 0
    vrm_bones_copy = copy.deepcopy(vrm_bones)
    while len(vrm_bones_copy.keys()):
        bone_chain(list(vrm_bones_copy.keys())[0],-1)
    #call when bone built    
    bpy.context.scene.update()
    bpy.ops.object.mode_set(mode='OBJECT')
    
        
    #Material_datas　適当なので要調整
    mat_dict = dict()
    for index,mat in enumerate(vrm_materials):
        b_mat = bpy.data.materials.new(mat.name)
        b_mat.use_shadeless = True
        b_mat.diffuse_color = mat.base_color[0:3]
        b_mat.use_transparency = True
        b_mat.alpha = 1
        ts = b_mat.texture_slots.add()
        ts.texture = textures[mat.color_texture_index]
        ts.use_map_alpha = True
        ts.blend_type = 'MULTIPLY'
        mat_dict[index] = b_mat
    
    blend_mesh_object_list = []
    #mesh_obj_build
    for mesh in vrm_meshes:
        msh = bpy.data.meshes.new(mesh.name)
        msh.from_pydata(mesh.POSITION, [], mesh.face_indices.tolist())
        msh.update()
        obj = bpy.data.objects.new(mesh.name, msh)
        blend_mesh_object_list.append(obj)
        #kuso of kuso
        origin = None
        for key,node in origin_bone.items():
            if node[1] == mesh.mesh_id:
                obj.location = node[0].position
                if len(node) == 3:
                    origin = node
                else:#len=2,skinがない場合
                    obj.parent = amt
                    obj.parent_type = "BONE"
                    obj.parent_bone = node[0].name
                    #boneのtail側にparentされるので、根元に動かす
                    obj.location = numpy.array(bones[key].head) - numpy.array(bones[key].tail)
        
        # vertex groupの作成
        if origin != None:
            vg_list = [] # VertexGroupのリスト
            nodes_index_list = vrm_skins_nodes_list[origin[2]]
            for n_index in nodes_index_list:
                obj.vertex_groups.new(vrm_bones[n_index].name)
                vg_list.append(obj.vertex_groups[-1])
            # VertexGroupに頂点属性から一個ずつｳｪｲﾄを入れる用の辞書作り
            vg_dict = {}
            for i,(joint_ids,weights) in enumerate(zip(mesh.JOINTS_0,mesh.WEIGHTS_0)):
                for joint_id,weight in zip(joint_ids,weights):
                    node_id = vrm_skins_nodes_list[origin[2]][joint_id]
                    if vrm_bones[node_id].name in vg_dict.keys():
                        vg_dict[vrm_bones[node_id].name].append([i,weight])#2個目以降のｳｪｲﾄ
                    else:
                        vg_dict[vrm_bones[node_id].name] = [[i,weight]]#1個目のｳｪｲﾄ（初期化兼）
            #頂点ﾘｽﾄに辞書から書き込む
            for vg in vg_list:
                if not vg.name in vg_dict.keys():
                    print("unused vertex group")
                    continue
                weights = vg_dict[vg.name]
                for w in weights:
                    if w[1] != 0.0:
                        vg.add([w[0]], w[1], 'REPLACE')
        obj.modifiers.new("amt","ARMATURE").object = amt

        #end of kuso
        scene = bpy.context.scene
        scene.objects.link(obj)
        
        # uv
        flatten_vrm_mesh_vert_index = mesh.face_indices.flatten()
        channnel_name = "TEXCOORD_0"
        msh.uv_textures.new(channnel_name)
        blen_uv_data = msh.uv_layers[channnel_name].data
        for id,v_index in enumerate(flatten_vrm_mesh_vert_index):
            blen_uv_data[id].uv = mesh.TEXCOORD_0[v_index]
            #blender axisnaize(上下反転)
            blen_uv_data[id].uv[0] =blen_uv_data[id].uv[0]
            blen_uv_data[id].uv[1] =blen_uv_data[id].uv[1]*-1+1
        #material
        obj.data.materials.append(mat_dict[mesh.material_index])


        def absolutaize_morph_Positions(basePoints,morphTargetpos):
            shape_key_Positions = []
            for basePos,morphPos in zip(basePoints,morphTargetpos):
                #numpyのarrayの加算は連結ではなく、要素ごとの加算
                shape_key_Positions.append(numpy.array(basePos) + numpy.array(morphPos))
            return shape_key_Positions
        #shapeKeys
        if hasattr(mesh,"morphTargetDict"):
            obj.shape_key_add("Basis")
            for morphName,morphPos in mesh.morphTargetDict.items():
                obj.shape_key_add(morphName)
                keyblock = msh.shape_keys.key_blocks[morphName]
                shape_data = absolutaize_morph_Positions(mesh.POSITION,morphPos)
                for i,co in enumerate(shape_data):
                    keyblock.data[i].co = co


    #cleaning
    bpy.ops.object.select_all(action="DESELECT")
    for obj in blend_mesh_object_list:
        obj.select = True
        bpy.ops.object.shade_smooth()
        bpy.context.scene.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.delete_loose()
        bpy.ops.mesh.select_all()
        bpy.ops.mesh.remove_doubles(use_unselected= True)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select = False

    #axis 
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action="DESELECT")
    for obj in blend_mesh_object_list:
        if obj.parent_type == 'BONE':#ボーンにくっ付いて動くのは無視:なんか吹っ飛ぶ髪の毛がいる?
            continue
        bpy.context.scene.objects.active = obj
        obj.select = True
        obj.rotation_mode = "XYZ"
        obj.rotation_euler[0] = numpy.deg2rad(90)
        obj.rotation_euler[2] = numpy.deg2rad(-90)
        bpy.ops.object.transform_apply(rotation=True)
        obj.select = False
    bpy.context.scene.objects.active = amt
    amt.select = True
    amt.rotation_mode = "XYZ"
    amt.rotation_euler[0] = numpy.deg2rad(90)
    amt.rotation_euler[2] = numpy.deg2rad(-90)
    bpy.ops.object.transform_apply(rotation=True)
    
    
    


if "__main__" == __name__:
    model_path = "./AliciaSolid\\AliciaSolid.vrm"
    model_path = "./Vroid\\Vroid.vrm"
    main(model_path)
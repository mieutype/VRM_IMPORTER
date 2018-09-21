import bpy, bmesh
from . import V_Types as VRM_Types
from math import sqrt,pow
import numpy
import json


def vrm_model_build(vrm_model):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action="DESELECT")
    #image_path_to Texture
    textures = []
    for image_props in vrm_model.image_propaties:
        img = bpy.data.images.load(image_props.filePath)
        tex = bpy.data.textures.new(image_props.name,"IMAGE")
        tex.image = img
        textures.append(tex)
        
    #build bones as armature
    bpy.ops.object.add(type='ARMATURE', enter_editmode=True, location=(0,0,0))
    amt = bpy.context.object
    amt.name = vrm_model.json["extensions"]["VRM"]["meta"]["title"]
    bones = dict()
    def bone_chain(id,parentID):
        if id == -1:
            pass
        else:
            vb = vrm_model.bones_dict[id]
            b = amt.data.edit_bones.new(vb.name)
            if parentID == -1:
                parentPos = [0,0,0]
            else:
                parentPos = bones[parentID].head
            b.head = numpy.array(parentPos)+numpy.array(vb.position)
            #temprary tail pos(gltf doesn't have bone. it defines as joints )
            def vector_length(bone_vector):
                return sqrt(pow(bone_vector[0],2)+pow(bone_vector[1],2)+pow(bone_vector[2],2))
            #gltfは関節で定義されていて骨の長さとか向きとかないからまあなんかそれっぽい方向にボーンを向けて伸ばしたり縮めたり
            if vb.children == None:
                if parentID == -1:#唯我独尊：上向けとけ
                    b.tail = [b.head[0],b.head[1]+0.05,b.head[2]]
                else:#normalize lenght to 0.03　末代：親から距離をちょっととる感じ
                    lengh = vector_length(vb.position)
                    lengh *= 30
                    if lengh <= 0.01:#0除算除けと気分
                        lengh =0.01
                    posDiff = [vb.position[0]/lengh,vb.position[1]/lengh,vb.position[2]/lengh]
                    if posDiff == [0.0,0.0,0.0]:
                        posDiff[1] += 0.01 #ボーンの長さが0だとOBJECT MODEに戻った時にボーンが消えるので上向けとく
                    b.tail = [b.head[0]+posDiff[0],b.head[1]+posDiff[1],b.head[2]+posDiff[2]]
            else:#子供たちの方向の中間を見る
                mean_relate_pos = numpy.array([0.0,0.0,0.0],dtype=numpy.float)
                count=0
                for childID in vb.children:
                    count +=1
                    mean_relate_pos += vrm_model.bones_dict[childID].position
                mean_relate_pos = mean_relate_pos / count
                if vector_length(mean_relate_pos) == 0:#子の位置の平均が根本と同じなら上向けとく
                    mean_relate_pos[1] +=0.1
                b.tail =[b.head[0]+mean_relate_pos[0],b.head[1]+mean_relate_pos[1],b.head[2]+mean_relate_pos[2]]

                    
            #end tail pos    
            bones[id] = b
            if parentID != -1:
                b.parent = bones[parentID]
            if vb.children != None:
                    for x in vb.children:
                        bone_chain(x,id)
            return 0
    rootnodes = [node for scene in vrm_model.json["scenes"] for node in scene["nodes"]] #scenesのなかのsceneのなかのnodesのﾘｽﾄを展開
    while len(rootnodes):
        bone_chain(rootnodes.pop(),-1)
    #call when bone built    
    bpy.context.scene.update()
    bpy.ops.object.mode_set(mode='OBJECT')
    
        
    #Material_datas　適当なので要調整
    mat_dict = dict()
    for index,mat in enumerate(vrm_model.materials):
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
    
    blend_mesh_object_dict = dict()
    #mesh_obj_build
    for mesh in vrm_model.meshes:
        msh = bpy.data.meshes.new(mesh.name)
        msh.from_pydata(mesh.POSITION, [], mesh.face_indices.tolist())
        msh.update()
        obj = bpy.data.objects.new(mesh.name, msh)
        if not mesh.mesh_object_id in blend_mesh_object_dict.keys():
            blend_mesh_object_dict[mesh.mesh_object_id] = [obj]
        else: 
            blend_mesh_object_dict[mesh.mesh_object_id].append(obj)
        #kuso of kuso kakugosiro
        origin = None
        for key,node in vrm_model.origine_bones_dict.items():
            if node[1] == mesh.mesh_object_id:
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
            nodes_index_list = vrm_model.skins_joints_list[origin[2]]
            for n_index in nodes_index_list:
                obj.vertex_groups.new(vrm_model.bones_dict[n_index].name)
                vg_list.append(obj.vertex_groups[-1])
            # VertexGroupに頂点属性から一個ずつｳｪｲﾄを入れる用の辞書作り
            if hasattr(mesh,"JOINTS_0") and hasattr(mesh,"WEIGHTS_0"):
                vg_dict = {}
                for i,(joint_ids,weights) in enumerate(zip(mesh.JOINTS_0,mesh.WEIGHTS_0)):
                    for joint_id,weight in zip(joint_ids,weights):
                        node_id = vrm_model.skins_joints_list[origin[2]][joint_id]
                        if vrm_model.bones_dict[node_id].name in vg_dict.keys():
                            vg_dict[vrm_model.bones_dict[node_id].name].append([i,weight])#2個目以降のｳｪｲﾄ
                        else:
                            vg_dict[vrm_model.bones_dict[node_id].name] = [[i,weight]]#1個目のｳｪｲﾄ（初期化兼）
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
        texcoord_num = 0
        while True:
            channnel_name = "TEXCOORD_" + str(texcoord_num)
            if hasattr(mesh,channnel_name):
                msh.uv_textures.new(channnel_name)
                blen_uv_data = msh.uv_layers[channnel_name].data
                vrm_texcoord  = getattr(mesh,channnel_name)
                for id,v_index in enumerate(flatten_vrm_mesh_vert_index):
                    blen_uv_data[id].uv = vrm_texcoord[v_index]
                    #blender axisnaize(上下反転)
                    blen_uv_data[id].uv[1] = blen_uv_data[id].uv[1] * -1 + 1
                texcoord_num += 1
            else:
                break

        #material
        obj.data.materials.append(mat_dict[mesh.material_index])


        def absolutaize_morph_Positions(basePoints,morphTargetpos):
            shape_key_Positions = []
            for basePos,morphPos in zip(basePoints,morphTargetpos):
                #numpy.array毎回作るのは見た目きれいだけど8倍くらい遅い
                shape_key_Positions.append([
                    basePos[0] + morphPos[0],
                    basePos[1] + morphPos[1],
                    basePos[2] + morphPos[2]
                ])
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
    #mesh build end
    #json dump
    textblock = bpy.data.texts.new("{}.json".format(vrm_model.json["extensions"]["VRM"]["meta"]["title"]))
    textblock.write(json.dumps(vrm_model.json,indent = 4))
    
    #cleaning
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action="DESELECT")
    for objs in blend_mesh_object_dict.values():
        for obj in objs:
            obj.select = True
            bpy.ops.object.shade_smooth()
            bpy.context.scene.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.delete_loose()
            bpy.ops.mesh.select_all()
            bpy.ops.mesh.remove_doubles(use_unselected= True)
            bpy.ops.object.mode_set(mode='OBJECT')
            obj.select = False

    #join primitives
    joined_objects = []
    bpy.ops.object.select_all(action="DESELECT")
    for objs in blend_mesh_object_dict.values():
        bpy.context.scene.objects.active = objs[0]
        for obj in objs:
            obj.select = True
        bpy.ops.object.join()
        bpy.ops.object.select_all(action="DESELECT")
        joined_objects.append(bpy.context.active_object)

    #axis armature->>boneの順でやらないと不具合
    bpy.context.scene.objects.active = amt
    amt.select = True
    amt.rotation_mode = "XYZ"
    amt.rotation_euler[0] = numpy.deg2rad(90)
    amt.rotation_euler[2] = numpy.deg2rad(-90)
    bpy.ops.object.transform_apply(rotation=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action="DESELECT")
    for obj in  joined_objects:
        bpy.context.scene.objects.active = obj
        obj.select = True
        if obj.parent_type == 'BONE':#ボーンにくっ付いて動くのは無視:なんか吹っ飛ぶ髪の毛がいる?
            bpy.ops.object.transform_apply(rotation=True)
            print("bone parent object {}".format(obj.name))
            continue
        obj.rotation_mode = "XYZ"
        obj.rotation_euler[0] = numpy.deg2rad(90)
        obj.rotation_euler[2] = numpy.deg2rad(-90)
        bpy.ops.object.transform_apply(rotation=True)
        obj.select = False
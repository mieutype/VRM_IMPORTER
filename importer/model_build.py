"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""


import bpy, bmesh
from mathutils import Vector,Matrix
from .. import V_Types as VRM_Types
from math import sqrt,pow,radians
import numpy
import json,copy

class Blend_model():
    def __init__(self,vrm_pydata,is_put_spring_bone_info):
        self.textures = None
        self.armature = None
        self.bones = None
        self.material_dict = None
        self.primitive_obj_dict = None
        self.mesh_joined_objects = None
        self.vrm_model_build(vrm_pydata,is_put_spring_bone_info)


    def vrm_model_build(self,vrm_pydata,is_put_spring_bone_info):

        affected_object = self.scene_init()
        self.texture_load(vrm_pydata)
        self.make_armature(vrm_pydata)
        self.make_material(vrm_pydata)
        self.make_primitive_mesh_objects(vrm_pydata)
        self.json_dump(vrm_pydata)
        self.attach_vrm_attributes(vrm_pydata)
        self.cleaning_data()
        self.axis_transform()
        if is_put_spring_bone_info:
            self.put_spring_bone_info(vrm_pydata)
        self.finishing(affected_object)
        return 0

    def scene_init(self):
        # active_objectがhideだとbpy.ops.object.mode_set.poll()に失敗してエラーが出るのでその回避と、それを元に戻す
        affected_object = None
        if bpy.context.active_object != None:
            if hasattr(bpy.context.active_object, "hide"):
                if bpy.context.active_object.hide:
                    bpy.context.active_object.hide = False
                    affected_object = bpy.context.active_object
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action="DESELECT")
        return affected_object

    def finishing(self,affected_object):
        #initで弄ったやつを戻す
        if affected_object is not None:
            affected_object.hide = True
        return

        #image_path_to Texture
    def texture_load(self, vrm_pydata):
        self.textures = []
        for image_props in vrm_pydata.image_propaties:
            img = bpy.data.images.load(image_props.filePath)
            tex = bpy.data.textures.new(image_props.name,"IMAGE")
            tex.image = img
            self.textures.append(tex)
        return
            
    def make_armature(self, vrm_pydata):
        #build bones as armature
        bpy.ops.object.add(type='ARMATURE', enter_editmode=True, location=(0,0,0))
        self.armature = bpy.context.object
        self.armature.name = "skelton"
        self.bones = dict()
        def bone_chain(self_and_parent_id_tuple):
            id = self_and_parent_id_tuple[0]
            parent_id = self_and_parent_id_tuple[1]

            if id == -1:#自身がrootのrootの時
                pass
            else:
                py_bone = vrm_pydata.nodes_dict[id]
                print("pybone name is "+py_bone.name+" .")
                if py_bone.blend_bone:#すでにインスタンス化済みのボーンが出てきたとき。
                    li = [py_bone.blend_bone]
                    while li:
                        bo = li.pop()
                        if parent_id != -1:
                            bo.translate(self.bones[parent_id].head)
                            bo.parent = self.bones[parent_id]
                        for ch in bo.children:
                            li.append(ch)
                    return
                if py_bone.mesh_id is not None and py_bone.children is None:
                    return  #子がなく、mesh属性を持つnodeはboneを生成しない
                b = self.armature.data.edit_bones.new(py_bone.name)
                py_bone.name = b.name
                py_bone.blend_bone = b
                if parent_id == -1:
                    parent_pos = [0,0,0]
                else:
                    parent_pos = self.bones[parent_id].head
                b.head = numpy.array(parent_pos)+numpy.array(py_bone.position)
                #region temprary tail pos(gltf doesn't have bone. there defines as joints )
                def vector_length(bone_vector):
                    return sqrt(pow(bone_vector[0],2)+pow(bone_vector[1],2)+pow(bone_vector[2],2))
                #gltfは関節で定義されていて骨の長さとか向きとかないからまあなんかそれっぽい方向にボーンを向けて伸ばしたり縮めたり
                if py_bone.children == None:
                    if parent_id == -1:#唯我独尊：上向けとけ
                        b.tail = [b.head[0],b.head[1]+0.05,b.head[2]]
                    else:#normalize length to 0.03　末代：親から距離をちょっととる感じ
                        lengh = vector_length(py_bone.position)
                        lengh *= 30
                        if lengh <= 0.01:#0除算除けと気分
                            lengh =0.01
                        posDiff = [py_bone.position[i]/lengh for i in range(3)]
                        if posDiff == [0.0,0.0,0.0]:
                            posDiff[1] += 0.01 #ボーンの長さが0だとOBJECT MODEに戻った時にボーンが消えるので上向けとく
                        b.tail = [b.head[i]+posDiff[i] for i in range(3)]
                else:#子供たちの方向の中間を見る
                    mean_relate_pos = numpy.array([0.0,0.0,0.0],dtype=numpy.float)
                    count=0
                    for childID in py_bone.children:
                        count +=1
                        mean_relate_pos += vrm_pydata.nodes_dict[childID].position
                    mean_relate_pos = mean_relate_pos / count
                    if vector_length(mean_relate_pos) == 0:#子の位置の平均が根本と同じなら上向けとく
                        mean_relate_pos[1] +=0.1
                    b.tail =[b.head[i] + mean_relate_pos[i] for i in range(3)]

                #endregion tail pos    
                self.bones[id] = b

                if parent_id != -1:
                    b.parent = self.bones[parent_id]
                if py_bone.children != None:
                        for x in py_bone.children:
                            bone_nodes.append((x,id))
            return 0
        root_node_set = list(set(vrm_pydata.skins_root_node_list))
        root_nodes =  root_node_set if root_node_set else [node for scene in vrm_pydata.json["scenes"] for node in scene["nodes"]] 
        bone_nodes = [(root_node,-1) for root_node in root_nodes]
        while len(bone_nodes):
            bone_chain(bone_nodes.pop())
        #call when bone built    
        bpy.context.scene.update()
        bpy.ops.object.mode_set(mode='OBJECT')
        return
    
    #region material
    def make_material(self, vrm_pydata):
        #Material_datas　適当なので要調整
        self.material_dict = dict()
        for index,mat in enumerate(vrm_pydata.materials):
            b_mat = bpy.data.materials.new(mat.name)
            b_mat.use_shadeless = True  #分かりやすさ重視
            b_mat["shader_name"] = mat.shader_name
            if type(mat) == VRM_Types.Material_GLTF:
                self.build_material_from_GLTF(b_mat, mat)
            if type(mat) == VRM_Types.Material_MToon:
                self.build_material_from_MToon(b_mat, mat)
            if type(mat) == VRM_Types.Material_Transparent_Z_write:
                self.build_material_from_Transparent_Z_write
            self.material_dict[index] = b_mat
        return

    def set_material_transparent(self,b_mat, transparent_mode):
        if transparent_mode == "OPAQUE":
            b_mat.use_transparency = False
        elif transparent_mode == "Z_TRANSPARENCY":
            b_mat.use_transparency = True
            b_mat.alpha = 1
            b_mat.transparency_method = "Z_TRANSPARENCY"
        elif transparent_mode == "MASK":
            b_mat.use_transparency = True
            b_mat.alpha = 1
            b_mat.transparency_method = "MASK"
        return

    def texture_add(self,b_mat,b_texture,texture_param_dict,slot_param_dict):
        ts = b_mat.texture_slots.add()
        ts.texture = b_texture
        for attr,param in texture_param_dict.items():
            setattr(ts.texture,attr,param)
        for attr,param in slot_param_dict.items():
            setattr(ts,attr,param)
        return ts

    def texture_add_helper(self, b_mat, texture_id, mapping, uv_layer_num=0,
                            texture_param_dict = None, slot_param_dict=None):
        if texture_id == None:
            return
        b_texture = self.textures[texture_id]
        texture_param_dict = {} if texture_param_dict == None else texture_param_dict
        slot_param_dict = {} if slot_param_dict == None else slot_param_dict
        slot_param_dict.update({"texture_coords": mapping})
        if mapping == "UV":
            slot_param_dict.update({"uv_layer": "TEXCOORD_{}".format(uv_layer_num)})
        tex_slot = self.texture_add(b_mat, b_texture, texture_param_dict, slot_param_dict)
        return tex_slot

    def color_texture_add(self, b_mat, texture_index, uv_layer_index):
        self.texture_add_helper(
            b_mat, texture_index,
            "UV", uv_layer_index, None,
            {"use_map_alpha": True, "blend_type": "MULTIPLY"}
            )
    def normal_texture_add(self, b_mat, texture_index, uv_layer_index):
        self.texture_add_helper(
            b_mat, texture_index,
            "UV", uv_layer_index,
            {"use_normal_map": True},
            {"blend_type": "MIX",
            "use_map_color_diffuse":False,
            "use_map_normal": True})

    def un_affect_texture_add(self, b_mat, texture_index, uv_layer_index, role):
        ts = self.texture_add_helper(
            b_mat,texture_index,
            "UV", uv_layer_index,
            None,
            {"use_map_color_diffuse": False})
        if ts is not None:
            if "role" in ts.texture:
                print("{} texture's role :{}: is over written".format(ts.texture.name,role))             
            ts.texture["role"] = role

    def build_material_from_GLTF(self, b_mat, pymat):
        b_mat.use_shadeless = pymat.shadeless
        b_mat.diffuse_color = [pow(v,2.2) for v in pymat.base_color[0:3]] #ungamma
        self.set_material_transparent(b_mat, pymat.alphaMode)

        self.color_texture_add(
            b_mat, pymat.color_texture_index,
            pymat.color_texcoord_index)
        
        self.texture_add_helper(
            b_mat, pymat.normal_texture_index,
            pymat.normal_texture_texcoord_index)
        return

    def build_material_from_MToon(self, b_mat, pymat):
        for k, v in pymat.float_props_dic.items():
            b_mat[k] = v
        for tex_name, tex_index in pymat.texture_index_dic.items():
            if tex_name == "_MainTex":
                self.color_texture_add(b_mat, tex_index, 0)
            elif tex_name == "_BumpMap":
                self.normal_texture_add(b_mat, tex_index, 0)
            elif tex_name == "_SphereAdd":
                self.texture_add_helper(b_mat, tex_index, "NORMAL", None, {}, {"blend_type": "ADD"})
            else:
                self.un_affect_texture_add(b_mat, tex_index, 0, tex_name)
        for k, v in pymat.vector_props_dic.items():
            if k == "_Color":
                b_mat.diffuse_color =  [pow(val,2.2) for val in v[0:3]] #un gamma
            else:
                b_mat[k] = v
        for k, v in pymat.keyword_dic.items():
            b_mat[k] = v
        transparant_exchange_dic = {0:"OPAQUE",1:"MASK",2:"Z_TRANSPARENCY",3:"Z_TRANSPARENCY"}#Trans_Zwrite(3)も2扱いで。
        self.set_material_transparent(b_mat,transparant_exchange_dic[pymat.float_props_dic["_BlendMode"]])

    def build_material_from_Transparent_Z_write(self, b_mat, pymat):
        for k, v in pymat.float_props_dic.items():
            b_mat[k] = v
        for tex_name, tex_index in pymat.texture_index_dic.items():
            if tex_name == "_MainTex":
                self.color_texture_add(b_mat, tex_index, 0)
        for k, v in pymat.vector_props_dic.items():
            if k == "_Color":
                b_mat.diffuse_color = [pow(val,2.2) for val in v[0:3]]
            else:
                b_mat[k] = v
        self.set_material_transparent(b_mat,"Z_TRANSPARENCY")          
        return                

    #endregion material


    def make_primitive_mesh_objects(self, vrm_pydata):
        self.primitive_obj_dict = {pymesh.object_id:[] for pymesh in vrm_pydata.meshes}
        morph_cache_dict = {} #key:tuple(POSITION,targets.POSITION),value:points_data
        #mesh_obj_build
        for pymesh in vrm_pydata.meshes:
            b_mesh = bpy.data.meshes.new(pymesh.name)
            b_mesh.from_pydata(pymesh.POSITION, [], pymesh.face_indices.tolist())
            b_mesh.update()
            obj = bpy.data.objects.new(pymesh.name, b_mesh)
            self.primitive_obj_dict[pymesh.object_id].append(obj)
            #kuso of kuso kakugosiro
            #origin 0:Vtype_Node 1:mesh 2:skin
            origin = None
            for key_is_node_id,node in vrm_pydata.origine_nodes_dict.items():
                if node[1] == pymesh.object_id:
                    obj.location = node[0].position #origin boneの場所に移動
                    if len(node) == 3:
                        origin = node
                    else:  #len=2 ≒ skinがない場合
                        parent_id = None
                        for id, py_node in vrm_pydata.nodes_dict.items():
                            if py_node.children is None:
                                continue
                            if key_is_node_id in py_node.children:
                                parent_id = id
                        obj.parent = self.armature
                        obj.parent_type = "BONE"
                        obj.parent_bone = self.armature.data.bones[vrm_pydata.nodes_dict[parent_id].name].name
                        #boneのtail側にparentされるので、根元からmesh nodeのpositionに動かしなおす
                        #obj.location = node[0].position
                        obj.matrix_world =  Matrix.Translation([self.armature.matrix_world.to_translation()[i]  \
                                            + self.armature.data.bones[obj.parent_bone].matrix_local.to_translation()[i] \
                                            + node[0].position[i] for i in range(3)] )

                        #obj.rotation_euler[2] = numpy.deg2rad(90)
                        #bpy.ops.object.transform_apply(rotation=True)
                        

            
            # vertex groupの作成
            if origin != None:
                nodes_index_list = vrm_pydata.skins_joints_list[origin[2]]
                # VertexGroupに頂点属性から一個ずつｳｪｲﾄを入れる用の辞書作り
                if hasattr(pymesh,"JOINTS_0") and hasattr(pymesh,"WEIGHTS_0"):
                    vg_dict = { #使うkey(bone名)のvalueを空のリストで初期化（中身まで全部内包表記で？キモすぎるからしない。
                        vrm_pydata.nodes_dict[nodes_index_list[joint_id]].name : list() 
                            for joint_id in [joint_id for joint_ids in pymesh.JOINTS_0 for joint_id in joint_ids]
                    }
                    for v_index,(joint_ids,weights) in enumerate(zip(pymesh.JOINTS_0,pymesh.WEIGHTS_0)):
                        for joint_id,weight in zip(joint_ids,weights):
                            node_id = nodes_index_list[joint_id]
                            vg_dict[vrm_pydata.nodes_dict[node_id].name].append([v_index,weight])
                    vg_list = [] # VertexGroupのリスト
                    for vg_key in vg_dict.keys():
                        obj.vertex_groups.new(vg_key)
                        vg_list.append(obj.vertex_groups[-1])
                    #頂点ﾘｽﾄに辞書から書き込む
                    for vg in vg_list:
                        weights = vg_dict[vg.name]
                        for w in weights:
                            if w[1] != 0.0:
                                #頂点はまとめてﾘｽﾄで追加できるようにしかなってない
                                vg.add([w[0]], w[1], 'REPLACE')
                obj.modifiers.new("amt","ARMATURE").object = self.armature

            #end of kuso
            scene = bpy.context.scene
            scene.objects.link(obj)
            
            # uv
            flatten_vrm_mesh_vert_index = pymesh.face_indices.flatten()
            texcoord_num = 0
            while True:
                channnel_name = "TEXCOORD_" + str(texcoord_num)
                if hasattr(pymesh,channnel_name):
                    b_mesh.uv_textures.new(channnel_name)
                    blen_uv_data = b_mesh.uv_layers[channnel_name].data
                    vrm_texcoord  = getattr(pymesh,channnel_name)
                    for id,v_index in enumerate(flatten_vrm_mesh_vert_index):
                        blen_uv_data[id].uv = vrm_texcoord[v_index]
                        #blender axisnaize(上下反転)
                        blen_uv_data[id].uv[1] = blen_uv_data[id].uv[1] * -1 + 1
                    texcoord_num += 1
                else:
                    break

            #material適用
            obj.data.materials.append(self.material_dict[pymesh.material_index])
            
            #vertex_color　なぜかこれだけ面基準で、loose verts and edgesに色は塗れない
            #また、頂点カラーにalpha（４要素目）がないから完全対応は無理
            #TODO: テスト (懸案：cleaningで頂点結合でデータ物故割れる説)
            vcolor_count = 0
            while True:
                vc_color_name = "COLOR_{}".format(vcolor_count)
                if hasattr(pymesh,vc_color_name):
                    vc = b_mesh.vertex_colors.new(name = vc_color_name)
                    for v_index,col in enumerate(vc.data):
                        vc.data[v_index].color = getattr(pymesh,vc_color_name)[flatten_vrm_mesh_vert_index[v_index]][0:3]
                    vcolor_count += 1
                else:
                    break

            #shapekey_data_factory with cache
            def absolutaize_morph_Positions(basePoints,morphTargetpos_and_index):
                shape_key_Positions = []
                morphTargetpos = morphTargetpos_and_index[0]
                morphTargetindex = morphTargetpos_and_index[1]

                #すでに変換したことがあるならそれを使う
                if (pymesh.POSITION_accessor,morphTargetindex) in morph_cache_dict.keys():
                    return morph_cache_dict[(pymesh.POSITION_accessor,morphTargetindex)]

                for basePos,morphPos in zip(basePoints,morphTargetpos):
                    #numpy.array毎回作るのは見た目きれいだけど8倍くらい遅い
                    shape_key_Positions.append([
                        basePos[0] + morphPos[0],
                        basePos[1] + morphPos[1],
                        basePos[2] + morphPos[2]
                    ])
                morph_cache_dict[(pymesh.POSITION_accessor,morphTargetindex)] = shape_key_Positions
                return shape_key_Positions
                
            #shapeKeys
            if hasattr(pymesh,"morphTarget_point_list_and_accessor_index_dict"):
                obj.shape_key_add("Basis")
                for morphName,morphPos_and_index in pymesh.morphTarget_point_list_and_accessor_index_dict.items():
                    obj.shape_key_add(morphName)
                    keyblock = b_mesh.shape_keys.key_blocks[morphName]
                    shape_data = absolutaize_morph_Positions(pymesh.POSITION,morphPos_and_index)
                    for i,co in enumerate(shape_data):
                        keyblock.data[i].co = co

    def attach_vrm_attributes(self,vrm_pydata):
        VRM_extensions = vrm_pydata.json["extensions"]["VRM"]
        try:
            humanbones_relations = VRM_extensions["humanoid"]["humanBones"]
            for humanbone in humanbones_relations:
                self.armature.data.bones[vrm_pydata.json["nodes"][humanbone["node"]]["name"]]["humanBone"] = humanbone["bone"]
        except Exception as e:
            print(e)
            pass
        try:   
            for metatag,metainfo in vrm_pydata.json["extensions"]["VRM"]["meta"].items():
                if metatag == "texture":
                    self.armature[metatag] = self.textures[metainfo].image.name
                else:
                    self.armature[metatag] = metainfo
        except Exception as e:
            print(e)
            pass
            
        return

    def json_dump(self, vrm_pydata):
        vrm_ext_dic = vrm_pydata.json["extensions"]["VRM"]
        model_name = vrm_ext_dic["meta"]["title"]
        textblock = bpy.data.texts.new("{}_raw.json".format(model_name))
        textblock.write(json.dumps(vrm_pydata.json,indent = 4))


        def write_textblock_and_assgin_to_armature(block_name,value):
            text_block = bpy.data.texts.new("{}_{}.json".format(model_name,block_name))
            text_block.write(json.dumps(value,indent = 4))
            self.armature["{}".format(block_name)] = text_block.name
        
        #region humanoid_parameter
        humanoid_params = copy.deepcopy(vrm_ext_dic["humanoid"])
        del humanoid_params["humanBones"]
        write_textblock_and_assgin_to_armature("humanoid_params",humanoid_params)
        #endregion humanoid_parameter
        #region first_person
        #TODO: mesh annotations
        firstperson_params = copy.deepcopy(vrm_ext_dic["firstPerson"])
        if firstperson_params["firstPersonBone"] != -1:
            firstperson_params["firstPersonBone"] = vrm_pydata.json["nodes"][firstperson_params["firstPersonBone"]]["name"]
        if "meshAnnotations" in firstperson_params.keys():
            for meshAnotation in firstperson_params["meshAnnotations"]:
                meshAnotation["mesh"] = vrm_pydata.json["meshes"][meshAnotation["mesh"]]["name"]

        
        
        write_textblock_and_assgin_to_armature("firstPerson_params",firstperson_params)
        #endregion first_person

        #region blendshape_master
        blendShapeGroups_list = copy.deepcopy(vrm_ext_dic["blendShapeMaster"]["blendShapeGroups"])
        #meshをidから名前に
        #weightを0-100から0-1に
        #shape_indexを名前に
        #materialValuesはそのままで行けるハズ・・・
        for bsg in blendShapeGroups_list:
            for bind_dic in bsg["binds"]:
                bind_dic["index"] = vrm_pydata.json["meshes"][bind_dic["mesh"]]["primitives"][0]["extras"]["targetNames"][bind_dic["index"]]
                bind_dic["mesh"] = self.primitive_obj_dict[bind_dic["mesh"]][0].name
                bind_dic["weight"] = bind_dic["weight"] / 100
        write_textblock_and_assgin_to_armature("blendshape_group",blendShapeGroups_list)
        #endregion blendshape_master

        #region springbone
        spring_bonegroup_list =copy.deepcopy(vrm_ext_dic["secondaryAnimation"]["boneGroups"])
        colliderGroups_list = vrm_ext_dic["secondaryAnimation"]["colliderGroups"]
        #node_idを管理するのは面倒なので、名前に置き換える
        #collider_groupも同じく
        for bone_group in spring_bonegroup_list:
            bone_group["bones"] = [ vrm_pydata.json["nodes"][node_id]["name"] for node_id in bone_group["bones"]]
            bone_group["colliderGroups"] = [vrm_pydata.json["nodes"][colliderGroups_list[collider_gp_id]["node"]]["name"] for collider_gp_id in bone_group["colliderGroups"]]
        write_textblock_and_assgin_to_armature("spring_bone",spring_bonegroup_list)
        #endregion springbone

        return

    def cleaning_data(self):
        #cleaning
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action="DESELECT")
        for objs in self.primitive_obj_dict.values():
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
        self.mesh_joined_objects = []
        bpy.ops.object.select_all(action="DESELECT")
        for objs in self.primitive_obj_dict.values():
            bpy.context.scene.objects.active = objs[0]
            for obj in objs:
                obj.select = True
            bpy.ops.object.join()
            for unused_mesh in [obj.data for obj in objs[1:]]:
                bpy.data.meshes.remove(unused_mesh)
            self.mesh_joined_objects.append(bpy.context.active_object)
            bpy.ops.object.select_all(action="DESELECT")
        return

    def axis_transform(self):
        #axis armature->>objの順でやらないと不具合
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.scene.objects.active = self.armature
        self.armature.select = True
        self.armature.rotation_mode = "XYZ"
        self.armature.rotation_euler[0] = numpy.deg2rad(90)
        self.armature.rotation_euler[2] = numpy.deg2rad(-180)
        self.armature.location = [self.armature.location[axis]*inv for axis,inv in zip([0,2,1],[-1,1,1])]
        bpy.ops.object.transform_apply(location = True,rotation=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action="DESELECT")
        for obj in self.mesh_joined_objects:
            bpy.context.scene.objects.active = obj
            obj.select = True
            if obj.parent_type == 'BONE':#ボーンにくっ付いて動くのは無視:なんか吹っ飛ぶ髪の毛がいる?
                bpy.ops.object.transform_apply(rotation=True)
                print("bone parent object {}".format(obj.name))
                obj.select = False
                continue
            obj.rotation_mode = "XYZ"
            obj.rotation_euler[0] = numpy.deg2rad(90)
            obj.rotation_euler[2] = numpy.deg2rad(-180)
            obj.location = [obj.location[axis]*inv for axis,inv in zip([0,2,1],[-1,1,1])]
            bpy.ops.object.transform_apply(location= True,rotation=True)
            obj.select = False
        return
    
    def put_spring_bone_info(self,vrm_pydata):

        if not "secondaryAnimation" in vrm_pydata.json["extensions"]["VRM"]:
            print("no secondary animation object")
            return 
        secondaryAnimation_json = vrm_pydata.json["extensions"]["VRM"]["secondaryAnimation"]
        spring_rootbone_groups_json = secondaryAnimation_json["boneGroups"]
        collider_groups_json = secondaryAnimation_json["colliderGroups"]
        nodes_json = vrm_pydata.json["nodes"]
        for bone_group in spring_rootbone_groups_json:
            for bone_id in bone_group["bones"]:
                bone = self.armature.data.bones[nodes_json[bone_id]["name"]]
                for key, val in bone_group.items():
                    if key == "bones":
                        continue
                    bone[key] = val
                    
        for collider_group in collider_groups_json:
            collider_base_node = nodes_json[collider_group["node"]]
            node_name = collider_base_node["name"]
            for i, collider in enumerate(collider_group["colliders"]):
                collider_name = "{}_collider_{}".format(node_name,i)
                obj = bpy.data.objects.new(name = collider_name,object_data = None)
                obj.parent = self.armature
                obj.parent_type = "BONE"
                obj.parent_bone = node_name
                offset = [collider["offset"]["x"],collider["offset"]["y"],collider["offset"]["z"]] #values直接はindexｱｸｾｽ出来ないのでしゃあなし
                offset = [offset[axis]*inv for axis,inv in zip([0,2,1],[-1,-1,1])] #TODO: Y軸反転はuniVRMのシリアライズに合わせてる
                
                obj.matrix_world = self.armature.matrix_world * Matrix.Translation(offset) * self.armature.data.bones[node_name].matrix_local
                obj.empty_draw_size = collider["radius"]  
                obj.empty_draw_type = "SPHERE"
                bpy.context.scene.objects.link(obj)
                
        return 
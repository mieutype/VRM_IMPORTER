"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""


import bpy, bmesh
from mathutils import Vector,Matrix
from . import V_Types as VRM_Types
from math import sqrt,pow
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
        def bone_chain(id,parent_id):
            if id == -1:#自身がrootのrootの時
                pass
            else:
                py_bone = vrm_pydata.nodes_dict[id]
                b = self.armature.data.edit_bones.new(py_bone.name)
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
                            bone_chain(x,id)
                return 0
        root_node_set = set(vrm_pydata.skins_root_node_list)
        root_nodes =  root_node_set if root_node_set else [node for scene in vrm_pydata.json["scenes"] for node in scene["nodes"]] 
        while len(root_nodes):
            bone_chain(root_nodes.pop(),-1)
        #call when bone built    
        bpy.context.scene.update()
        bpy.ops.object.mode_set(mode='OBJECT')
        return
        
    def make_material(self, vrm_pydata):
        #Material_datas　適当なので要調整
        self.material_dict = dict()
        for index,mat in enumerate(vrm_pydata.materials):
            b_mat = bpy.data.materials.new(mat.name)
            b_mat.use_shadeless = True
            b_mat.diffuse_color = mat.base_color[0:3]
            if mat.alpha_mode == "OPAQUE":
                b_mat.use_transparency = False
            elif mat.alpha_mode == "Z_TRANSPARENCY":
                b_mat.use_transparency = True
                b_mat.alpha = 1
                b_mat.transparency_method = "Z_TRANSPARENCY"
            elif mat.alpha_mode == "MASK":
                b_mat.use_transparency = True
                b_mat.alpha = 1
                b_mat.transparency_method = "MASK"
            def texture_add(tex_index,texture_param_dict,slot_param_dict):
                ts = b_mat.texture_slots.add()
                ts.texture = tex_index
                for attr,param in texture_param_dict.items():
                    setattr(ts.texture,attr,param)
                for attr,param in slot_param_dict.items():
                    setattr(ts,attr,param)
                return
            if mat.color_texture_index is not None:
                texture_param_dict = {}
                slot_param_dict = {
                    "texture_coords":"UV",
                    "uv_layer":"TEXCOORD_{}".format(mat.color_texcoord_index),
                    "use_map_alpha":True,
                    "blend_type":"MULTIPLY"
                    }
                texture_add(self.textures[mat.color_texture_index],texture_param_dict,slot_param_dict)
            if mat.normal_texture_index is not None:
                texture_param_dict = {
                    "use_normal_map":True,
                }
                slot_param_dict = {
                    "texture_coords":"UV",
                    "uv_layer":"TEXCOORD_{}".format(mat.normal_texcoord_index),
                    "blend_type":"MIX",
                    "use_map_color_diffuse":False,
                    "use_map_normal":True
                    }
                texture_add(self.textures[mat.normal_texture_index],texture_param_dict,slot_param_dict)
            if hasattr(mat,"sphere_texture_index"):
                texture_param_dict = {}
                slot_param_dict = {
                    "texture_coords":"NORMAL",
                    "blend_type":"ADD"
                    }
                texture_add(self.textures[mat.sphere_texture_index],texture_param_dict,slot_param_dict)
            #FIXME blenderのemissionは光量のmap、Mtoonのemissionは光色
            if hasattr(mat,"emission_texture_index"):
                texture_param_dict = {}
                slot_param_dict = {
                    "texture_coords":"UV",
                    "uv_layer":"TEXCOORD_{}".format(mat.color_texcoord_index),
                    "use_map_color_diffuse":False,
                    "use_map_emit":True,
                    "blend_type":"ADD"
                    }
                texture_add(self.textures[mat.emission_texture_index],texture_param_dict,slot_param_dict)
            self.material_dict[index] = b_mat
        for mat in self.material_dict.values():
            print(mat.name)
        return 

    def make_primitive_mesh_objects(self, vrm_pydata):
        self.primitive_obj_dict = dict()
        morph_cache_dict = {} #key:tuple(POSITION,targets.POSITION),value:points_data
        #mesh_obj_build
        for pymesh in vrm_pydata.meshes:
            b_mesh = bpy.data.meshes.new(pymesh.name)
            b_mesh.from_pydata(pymesh.POSITION, [], pymesh.face_indices.tolist())
            b_mesh.update()
            obj = bpy.data.objects.new(pymesh.name, b_mesh)
            if not pymesh.object_id in self.primitive_obj_dict.keys():
                self.primitive_obj_dict[pymesh.object_id] = [obj]
            else: 
                self.primitive_obj_dict[pymesh.object_id].append(obj)
            #kuso of kuso kakugosiro
            #origin 0:Vtype_Node 1:mesh 2:skin
            origin = None
            for key,node in vrm_pydata.origine_nodes_dict.items():
                if node[1] == pymesh.object_id:
                    obj.location = node[0].position #origin boneの場所に移動
                    if len(node) == 3:
                        origin = node
                    else:#len=2 ≒ skinがない場合
                        obj.parent = self.armature
                        obj.parent_type = "BONE"
                        obj.parent_bone = node[0].name
                        #boneのtail側にparentされるので、根元に動かす
                        obj.location = numpy.array(self.bones[key].head) - numpy.array(self.bones[key].tail)
            
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
            #TODO テスト (懸案：cleaningで頂点結合でデータ物故割れる説)
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
        
        #region blendshape_master
        blendShapeGroups_list = copy.deepcopy(vrm_ext_dic["blendShapeMaster"]["blendShapeGroups"])
        #meshをidから名前に
        #weightを0-100から0-1に
        #shape_indexを名前に
        for bsg in blendShapeGroups_list:
            for bind_dic in bsg["binds"]:
                bind_dic["index"] = vrm_pydata.json["meshes"][bind_dic["mesh"]]["primitives"][0]["extras"]["targetNames"][bind_dic["index"]]
                bind_dic["mesh"] = self.primitive_obj_dict[bind_dic["mesh"]][0].name
                bind_dic["weight"] = bind_dic["weight"] / 100

        blendshape_block = bpy.data.texts.new("{}_blend_shape_group.json".format(model_name))
        blendshape_block.write(json.dumps(blendShapeGroups_list,indent = 4))
        self.armature["blendshape_json"] = blendshape_block.name
        #endregion blendshape_master

        #region springbone
        spring_bonegroup_list =copy.deepcopy(vrm_ext_dic["secondaryAnimation"]["boneGroups"])
        colliderGroups_list = vrm_ext_dic["secondaryAnimation"]["colliderGroups"]
        #node_idを管理するのは面倒なので、名前に置き換える
        #collider_groupも同じく
        for bone_group in spring_bonegroup_list:
            bone_group["bones"] = [ vrm_pydata.json["nodes"][node_id]["name"] for node_id in bone_group["bones"]]
            bone_group["colliderGroups"] = [vrm_pydata.json["nodes"][colliderGroups_list[collider_gp_id]["node"]]["name"] for collider_gp_id in bone_group["colliderGroups"]]
        spring_bonegroup_block = bpy.data.texts.new("{}_secondary_root_bones.json".format(model_name))
        spring_bonegroup_block.write(json.dumps(spring_bonegroup_list,indent = 4))
        self.armature["spring_bone_json"] = spring_bonegroup_block.name
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
            bpy.ops.object.select_all(action="DESELECT")
            for unused_mesh in [obj.data for obj in objs[1:]]:
                bpy.data.meshes.remove(unused_mesh)
            self.mesh_joined_objects.append(bpy.context.active_object)
        return

    def axis_transform(self):
        #axis armature->>objの順でやらないと不具合
        bpy.context.scene.objects.active = self.armature
        self.armature.select = True
        self.armature.rotation_mode = "XYZ"
        self.armature.rotation_euler[0] = numpy.deg2rad(90)
        self.armature.rotation_euler[2] = numpy.deg2rad(-180)
        bpy.ops.object.transform_apply(rotation=True)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action="DESELECT")
        for obj in self.mesh_joined_objects:
            bpy.context.scene.objects.active = obj
            obj.select = True
            if obj.parent_type == 'BONE':#ボーンにくっ付いて動くのは無視:なんか吹っ飛ぶ髪の毛がいる?
                bpy.ops.object.transform_apply(rotation=True)
                print("bone parent object {}".format(obj.name))
                continue
            obj.rotation_mode = "XYZ"
            obj.rotation_euler[0] = numpy.deg2rad(90)
            obj.rotation_euler[2] = numpy.deg2rad(-180)
            bpy.ops.object.transform_apply(rotation=True)
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
                offset = [offset[axis]*inv for axis,inv in zip([0,2,1],[-1,1,1])]
                
                obj.matrix_world = self.armature.matrix_world * Matrix.Translation(offset) * self.armature.data.bones[node_name].matrix_local
                obj.empty_draw_size = collider["radius"]  
                obj.empty_draw_type = "SPHERE"
                bpy.context.scene.objects.link(obj)
                
        return 
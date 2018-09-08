"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import json

read_path = "./vroid\\Vroid.json"
loaded_json =""
with open(read_path,"rb") as f:
    loaded_json = json.load(f)
print(loaded_json["scenes"])
for id in loaded_json["scenes"][0]["nodes"]:
    print("scenes nodes {}".format(loaded_json["nodes"][id]["name"]))
for i,node in enumerate(loaded_json["nodes"]):
    if node["name"] == "HairOrigin":
        print("HairOrigin id is {}".format(i))
        print("HairOrigin has child :{}".format("children" in node))
        print("HairOrigin has {}".format(node.keys()))
print("node の列挙")
import copy
nodes_name_list = {i:node["name"] for i, node in enumerate(loaded_json["nodes"]) }
nodes_name_list_copy = copy.deepcopy(nodes_name_list)
from pprint import pprint
pprint(nodes_name_list)

for i,node in enumerate(loaded_json["nodes"]):
    if "children" in node:
        if 151 in node["children"]:
            print(i)

print("--skinごとのjoints列挙--")
for skin in loaded_json["skins"]:
    for joint in skin["joints"]:
        try:
            print(nodes_name_list.pop(joint))
        except:
            print(nodes_name_list_copy[joint])
    print("")

print("---残り物(skinのjointで使われなかったnode達、そもそもボーンなのか？)----")
for nokori in nodes_name_list.values():
    print(nokori)

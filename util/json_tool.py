"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import json
import tkinter
import tkinter.filedialog
import struct
from collections import OrderedDict
read_path = tkinter.filedialog.askopenfilename(filetypes=[("vrm,json","*.vrm;*.json")])
loaded_json =""
with open(read_path, "rb") as f:
    filetype = read_path.split(".")[-1]
    if filetype == "vrm":
        bi = f.read()
        magic = 12 #offset from header
        bi_size = struct.unpack("<I", bi[magic:magic+4])[0]
        magic = 20 #offset from header
        loaded_json = json.loads(bi[magic:magic+bi_size].decode("utf-8"),object_pairs_hook=OrderedDict)
    elif filetype =="json":
        loaded_json = json.load(f)
    else:
        print("unsupported format :{}".format(filetype))
        exit()

#something do in below with loaded_json
for scene in loaded_json["scenes"]:
    for node in scene["nodes"]:
        print(loaded_json["nodes"][node]["name"])

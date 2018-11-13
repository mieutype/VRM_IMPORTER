"""
Copyright (c) 2018 iCyP
Released under the MIT license
https://opensource.org/licenses/mit-license.php

"""

import json
import tkinter
import tkinter.filedialog
read_path = tkinter.filedialog.askopenfilename()
loaded_json =""
with open(read_path,"rb") as f:
    loaded_json = json.load(f)
    search_list = ["Hairs",
                    "J_Bip_C_Head",
                    "J_Bip_C_Neck",
                    "J_Bip_C_UpperChest",
                    "J_Bip_C_Chest",
                    "J_Bip_C_Spine",
                    "J_Bip_C_Hips",
                    "Position",
                    "Global",
                    ]
    import numpy
    sum = numpy.array([0.0,0.0,0.0])
    for id,node in enumerate(loaded_json["nodes"]):
        if node["name"] in search_list:
            print("{} id:{} is {}".format(node["name"],id,node["translation"]))
            sum += numpy.array(node["translation"])
    print("{:.5f}, {:.5f}, {:.5f}".format(sum[0],sum[1],sum[2]))

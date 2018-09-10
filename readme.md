# MIT　license　
# バグ　要望　催促 ﾌﾟﾙﾘｸ：あなたがForkしてDIY(Do it yourself)お願いします。
# 注意
## 雰囲気でｲﾝﾎﾟｰﾄしたので、間違いがあるかもしれません
## GroupshapeKey、物理他Extension未実装
## マテリアルは（まだ）適当
## 変更禁止(CC_ND)VRMは一応弾く" 仕様 "のつもりです悪しからず。

## 既知の不具合　
 - 複数primitiveを持つﾒｯｼｭのﾓｰﾌがおかしい->uniVRM0.43以降のVRMであれば直ると思うので放置。
 - マテリアルがおかしい->blender2.8が出たら本気だす(直すとは言ってない)

## 内容説明
-  \_\_init\_\_.py ：blenderのaddonシステム接続する<br>
-  vrm_load.py ： importer本体。砂上の楼閣レベルの品、特にblenderに書き込む側<br>
-  binaly_loader： 名前の通り。上の補助。<br>
-  V_Types.py： 文字通りの構造体が複数<br>
-  gl_const.py：定数集<br>
## 上記をフォルダにまとめてaddonsフォルダに突っ込んで有効化(TESTINGの中にいる)したら左上FileからImport->VRM!!!!!
### 以下オマケ

- vrm_ripper.py： 動いたらVRMからjsonとテクスチャを切り出してくれる。動けば。動かないけど。
- json_tool.py： 上で切り出したjsonを適当に読み下すために作った何か。jsonのどこに何があるかとか探すときに使う。
- readme.md：これ！！
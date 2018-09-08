# MIT　license　
# Done is better than perfect!!!!!(終わらせてどーする)
# バグ　要望　催促 ﾌﾟﾙﾘｸ：あなたがForkしてDIY(Do it yourself)してあなたのものにしよう！
# 注意
## ｸｿｻﾞｺ事務員の魔剤と完徹の勢いによって書かれたコード　
## 仕様違い・漏れ多数：ロバストも何もあったもんじゃねえな！というか仕様がわからねえ！雰囲気importだ！
## (Group)shapeKey、物理他Extension未実装なのでほしい人はウルトラスーパーDIYおすすめ
## マテリアルは適当なのでDIY超おすすめ
## 変更禁止(CC_ND)VRMは一応弾く" 仕様 "のつもりです悪しからず。
## blenderの仕様上テクスチャは書き出さないと読めないので、vrmのあるフォルダにテクスチャファイルを書き散らかします。注意
# JUST DO IT NOW!!!!!!  DIY!!!!!

## 内容説明
-  \_\_init\_\_.py ：blenderのaddonシステム接続する<br>
-  vrm_load.py ： importer本体。砂上の楼閣レベルの品、特にblenderに書き込む側<br>
-  binaly_loader： 名前の通り。上の補助。<br>
-  V_Types.py： なんか適当な文字通りの構造体複数<br>
-  gl_const.py：定数集<br>
## 上記をフォルダにまとめてaddonsフォルダに突っ込んで有効化したら左上FileからImport->VRM!!!!!
### 以下オマケ

- vrm_ripper.py： 動いたらVRMからjsonとテクスチャを切り出してくれる。動けば。動かないけど。
- json_tool.py： 上で切り出したjsonを適当に読み下すために作った何か。jsonのどこに何があるかとか探すときに使う。
- readme.md：今あなたが読んで時間を無駄にしたこれ！！！！
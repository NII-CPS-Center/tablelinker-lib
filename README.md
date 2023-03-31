# tablelinker-lib

TableLinker をコマンドライン / プログラム組み込みで利用するためのライブラリ。

## インストール手順

Poetry を利用します。

```
$ poetry install --with group=dev
$ poetry shell
```

MacOS の場合、デフォルトの python バージョンが 3.11 なので
pytorch がインストールできません。以下の手順が必要です。

```
% pyenv install 3.10
% poetry env use 3.10
% poetry shell
% poetry install --with group=dev
```

## コマンドラインで利用する場合

tablelinker モジュールを実行すると、標準入力から受け取った CSV を
コンバータで変換し、標準出力に送るパイプとして利用できます。

```
$ cat sample/datafiles/yanai_tourism.csv | \
  python -m tablelinker sample/taskfiles/task.json
```

利用するコンバータと、コンバータに渡すパラメータは JSON ファイルに記述し、
パラメータで指定します。

## 組み込んで利用する場合

`sample.py` を参照してください。

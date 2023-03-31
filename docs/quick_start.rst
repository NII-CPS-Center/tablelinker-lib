.. _quick_start:

クイックスタート
================

使い方1: コマンドラインで利用する
---------------------------------

Tablelinker を Python コマンドとして実行すると、
CSV や Excel の表データを読み込み、用意されているコンバータを
利用して表データを変換し、結果を CSV データとして出力する
コマンドとして利用できます。

実行例は次のようになります。このコマンドは、「市区町村コード」列を
「都道府県コード又は市区町村コード」に変更します。

.. code-block:: bash

    $ tablelinker -i opendata.xlsx -o clean_opendata.csv -c rename_col -p '{"input_col_idx":"市区町村コード", "output_col_name": "都道府県コード又は市区町村コード"}'

毎回長いパラメータを指定するのは大変なので、利用したいコンバータ名と
パラメータを JSON ファイルに記述しておき、呼び出すこともできます。 ::

    $ tablelinker -i opendata.xlsx -o clean_opendata.csv task.json

``task.json`` には次のような JSON を記述します。

.. code-block:: json

    {
        "convertor":"rename_col",
        "params":{
            "input_col_idx": "市区町村コード",
            "output_col_name": "都道府県コード又は市区町村コード"
        }
    }

複数のコンバータを一つの JSON ファイルにまとめて書くこともできるので、
何度も使う手順を JSON ファイルにしておけば簡単に繰り返して実行できます。

Python プログラミングのスキルがない方や、バッチ処理向けです。


使い方2: Python パッケージとして利用する
----------------------------------------

Tablelinker パッケージを Python スクリプトに import することで、
表データの読み込み、変換、出力機能を利用できます。

簡単な利用例を示します。

.. code-block:: python

    >>> from tablelinker import Table
    >>> table = Table("opendata.xlsx")  # Excel ファイルを読み込み
    >>> table = table.convert(          # コンバータで変換
    ...     convertor="rename_col",     # コンバータ名
    ...     params={                    # コンバータに渡すパラメータ
    ...         "input_col_idx": "市区町村コード",       # 入力列名
    ...         "output_col_name":
    ...             "都道府県コード又は市区町村コード",  # 出力列名
    ...     },
    ... )
    >>> table.save("opendata_renamed.csv")

上記の例は、``opendata.xlsx`` を読み込み、「市区町村コード」列を
「都道府県コード又は市区町村コード」列に変更します。
その結果を ``opendata_renamed.csv`` に出力します。

Python スクリプトから直接 Table オブジェクトが管理している CSV データにアクセスすることもできるので、ファイルの読み込みや
簡単な整形処理は Tablelinker で実装し、
それ以降の複雑な処理は独自に実装するといった使い方ができます。

データ変換の前処理をわざわざ実装したくない Python プログラマ向けです。

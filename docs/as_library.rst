.. _as_library:

パッケージとして利用
====================

Tablelinker を Python アプリケーションやスクリプトに読み込むと、
表データの読み込みやクリーニングなどの処理を簡単に実装できます。

変換した表データは CSV ファイルとして保存したり、
一行ずつ取り出して Python コード内で利用できます。

より高度な使い方として、 `pandas <http://pandas.pydata.org/>`_ や
`Polars <https://www.pola.rs/>`_ の DataFrame を Tablelinker に読み込んだり、
Tablelinker で変換した結果の表データを DataFrame に変換することもできます。
詳細は :ref:`use_with_pandas` および :ref:`use_with_polars` を参照してください。

- サンプルデータのダウンロード

    このページでは厚生労働省の「人口動態調査(2020年)」の
    `上巻_3-3-1_都道府県（特別区－指定都市再掲）別にみた人口動態総覧 <https://www.data.go.jp/data/dataset/mhlw_20211015_0019>`_ から
    ダウンロードできる **ma030000.csv** をサンプルとして利用します。

表データを開く
--------------

表データは :py:class:`~tablelinker.core.table.Table` クラスの
オブジェクトとして管理します。
**ma030000.csv** ファイルから Table オブジェクトを作成する
コードの例を示します。

.. code-block:: python
    :caption: ファイルでTableを初期化
    :name: init_by_file

    >>> from tablelinker import Table
    >>> table = Table("ma030000.csv")

.. note::

    表データとして CSV ファイル、Excel ファイルを開けます。
    CSV ファイルの文字エンコーディングや区切り文字、
    表データの前のコメントのスキップなどのクリーニング処理も、
    ファイルを読み込む際に自動的に実行します。

**ヒント** 文字列やバイト列から Table オブジェクトを作成したい場合は、

.. code-block:: python

    >>> table = Table(data="ID,氏名,メールアドレス\n1,山田 太郎,yamada@example.com\n")

のように **data** パラメータで初期化してください。

表データの表示
--------------

:py:class:`~tablelinker.core.table.Table` オブジェクトが管理している
表データを表示するには、 :py:meth:`~tablelinker.core.table.Table.write`
メソッドを呼び出します。
**lines** オプションパラメータで表示する
行数を制限できます（省略すると全行表示します）。

.. code-block:: python
    :linenos:
    :caption: 表データを表示
    :name: write_table

    >>> from tablelinker import Table
    >>> table = Table("ma030000.csv")
    >>> table.write(lines=10)
    ,人口,出生数,死亡数,（再掲）,,自　然,死産数,,,周産期死亡数,,,婚姻件数,離婚件数
    ,,,,乳児死亡数,新生児,増減数,総数,自然死産,人工死産,総数,22週以後,早期新生児,,
    ,,,,,死亡数,,,,,,の死産数,死亡数,,
    全　国,123398962,840835,1372755,1512,704,-531920,17278,8188,9090,2664,2112,552,525507,193253
    01 北海道,5188441,29523,65078,59,25,-35555,728,304,424,92,75,17,20904,9070
    02 青森県,1232227,6837,17905,18,15,-11068,145,87,58,32,17,15,4032,1915
    03 岩手県,1203203,6718,17204,8,3,-10486,150,90,60,21,19,2,3918,1679
    04 宮城県,2280203,14480,24632,27,15,-10152,311,141,170,56,41,15,8921,3553
    05 秋田県,955659,4499,15379,9,4,-10880,98,63,35,18,15,3,2686,1213
    06 山形県,1060586,6217,15348,14,9,-9131,119,66,53,22,16,6,3530,1362

**ヒント** 画面（標準出力）以外に出力したい場合は **file** パラメータで指定できます。

.. code-block:: python

    >>> import io
    >>> buffer = io.StringIO()
    >>> table.write(lines=10, file=buffer)

コンバータの適用
----------------

:py:class:`~tablelinker.core.table.Table` オブジェクトに
:ref:`convertor` を適用することで、さまざまな変換処理を行うことができます。
コンバータを適用するには :py:meth:`~tablelinker.core.table.Table.convert`
メソッドを呼び出します。

メソッドのパラメータとして、利用するコンバータ名を表す **convertor** と、
そのコンバータに渡すパラメータ **params** を指定する必要があります。

:numref:`write_table` の表示結果を見ると先頭の列名が空欄なので、列名を変更する
:py:class:`rename_col <tablelinker.convertors.basics.rename_col.RenameColConvertor>`
コンバータを利用して「地域」に変更してみます。

.. code-block:: python
    :linenos:
    :caption: 列名を変更
    :name: rename_col

    >>> table = table.convert(
    ...     convertor='rename_col',
    ...     params={
    ...         'input_col_idx': 0,
    ...         'output_col_name': '地域',
    ...    }
    ... )
    >>> table.write(lines=5)
    地域,人口,出生数,死亡数,（再掲）,,自　然,死産数,,,周産期死亡数,,,婚姻件数,離婚件数
    ,,,,乳児死亡数,新生児,増減数,総数,自然死産,人工死産,総数,22週以後,早期新生児,,
    ,,,,,死亡数,,,,,,の死産数,死亡数,,
    全　国,123398962,840835,1372755,1512,704,-531920,17278,8188,9090,2664,2112,552,525507,193253
    01 北海道,5188441,29523,65078,59,25,-35555,728,304,424,92,75,17,20904,9070

次に列の選択と並び替えを行う
:py:class:`reorder_cols <tablelinker.convertors.basics.reorder_col.ReorderColsConvertor>`
コンバータを利用して、「地域」「人口」「出生数」「死亡数」の
4列を抜き出します。

.. code-block:: python
    :linenos:
    :caption: 指定した列を選択
    :name: reorder_cols

    >>> table = table.convert(
    ...     convertor='reorder_cols',
    ...     params={
    ...         'column_list':['地域','人口','出生数','死亡数'],
    ...     })
    >>> table.write(lines=5)
    地域,人口,出生数,死亡数
    ,,,
    ,,,
    全　国,123398962,840835,1372755
    01 北海道,5188441,29523,65078

.. note::

    利用できるコンバータおよびパラメータについては
    :ref:`convertor` を参照してください。

CSV ファイルに保存
------------------

変換した結果を :py:meth:`~tablelinker.core.table.Table.save()`
メソッドで CSV ファイルに保存します。

.. code-block:: python

    >>> table.save('ma030000_clean.csv')

保存した CSV ファイル **ma030000_clean.csv** は次のようになります。

.. code-block:: bash
    :linenos:

    $ cat ma03000_clean.csv
    地域,人口,出生数,死亡数
    ,,,
    ,,,
    全　国,123398962,840835,1372755
    01 北海道,5188441,29523,65078
    02 青森県,1232227,6837,17905
    03 岩手県,1203203,6718,17204
    04 宮城県,2280203,14480,24632
    05 秋田県,955659,4499,15379
    06 山形県,1060586,6217,15348
    ...

**ヒント** 既存の CSV ファイルに追記したい場合は、
:py:meth:`~tablelinker.core.table.Table.merge()` メソッドを利用してください。
追記先の列名が一致することを確認し、列の順番が一致していない場合は
自動的に並べ替えます。


表データにアクセス
------------------

Python プログラム内で、Table オブジェクトが管理する表データに
ファイルを経由せずに直接アクセスしたい場合、
:py:meth:`~tablelinker.core.table.Table.open` メソッドで
**csv.reader** のように列のリストを1行ずつ取得するイテレータを利用できます。

たとえば「地域」列が空欄の行をスキップするコードは次のように書けます。

.. code-block:: python
    :linenos:
    :caption: 表データにアクセス

    >>> with table.open() as reader:
    ...     for rows in reader:
    ...         if rows[0] != '':
    ...             print(','.join(rows))
    ...
    地域,人口,出生数,死亡数
    全　国,123398962,840835,1372755
    01 北海道,5188441,29523,65078
    02 青森県,1232227,6837,17905
    03 岩手県,1203203,6718,17204
    04 宮城県,2280203,14480,24632
    05 秋田県,955659,4499,15379
    06 山形県,1060586,6217,15348
    ...

**ヒント** csv.DictReader のように列名と値の dict を取得するイテレータを
利用したい場合、 ``table.open(as_dict=True)`` としてください。


見出し列のマッピング
--------------------

表データの変換処理で比較的頻度が高いものの一つに、
テンプレートとなる出力フォーマットに合わせて列を並び替えたり
列名を変更したりする **マッピング作業** があります。
:py:meth:`~tablelinker.core.table.Table.mapping` メソッドを利用することで
この作業を半自動化できます。

- サンプルデータ

    この節では山口県柳井市のオープンデータ `【柳井市】観光施設一覧(令和2年3月11日時点) 
    <https://yamaguchi-opendata.jp/ckan/dataset/352128-tourism>`_
    からダウンロードできる Excel ファイル **2311.xlsx** を
    サンプルとして利用します。

    また、デジタル庁の `「推奨データセット一覧」 <https://www.digital.go.jp/resources/data_dataset/>`_ ページ内、
    「5 観光施設一覧」の `CSV <https://www.digital.go.jp/assets/contents/node/basic_page/field_ref_resources/0066e8a8-6734-44ab-a9a9-8e09ba9cb508/xxxxxx_tourism.csv>`_ 
    からダウンロードできる **xxxxxx_tourism.csv** をテンプレートとして
    利用します。

例として、柳井市の観光施設一覧をダウンロードした **2311.xlsx** を、
推奨データセットテンプレートの **xxxxxx_tourism.csv** に
マッピングするコードを示します。

.. code-block:: python
    :linenos:
    :caption: 表データのマッピング

    >>> from tablelinker import Table
    >>> table = Table("2311.xlsx")
    >>> table.write(lines=1)
    市区町村コード,NO,都道府県名,市区町村名,名称,名称_カナ,名称_英語,POIコード,住所,方書,緯度,経度,利用可能曜日,開始時間,終了時間,利用可能日時特記事項,料金(基本),料金(詳細),説明,説明_英語,アクセス方法,駐車場情報,バリアフリー情報,連絡先名称,連絡先電話番号,連絡先内線番号,画像,画像_ライセンス,URL,備考
    >>> template = Table("xxxxxx_tourism.csv")
    >>> template.write(lines=1)
    都道府県コード又は市区町村コード,NO,都道府県名,市区町村名,名称,名称_カナ,名称_英語,POIコード,住所,方書,緯度,経度,利用可能曜日,開始時間,終了時間,利用可能日時特記事項,料金（基本）,料金（詳細）,説明,説明_英語,アクセス方法,駐車場情報,バリアフリー情報,連絡先名称,連絡先電話番号,連絡先内線番号,画像,画像_ライセンス,URL,備考
    >>> column_map = table.mapping(template)
    >>> new_table = table.convert(
    ...     convertor="mapping_cols",
    ...     params={"column_map":column_map},
    ... )
    >>> new_table.write(lines=2)
    都道府県コード又は市区町村コード,NO,都道府県名,市区町村名,名称,名称_カナ,名称_英語,POIコード,住所,方書,緯度,経度,利用可能曜日,開始時間,終了時間,利用可能日時特記事項,料金（基本）,料金（詳細）,説明,説明_英語,アクセス方法,駐車場情報,バリアフリー情報,連絡先名称,連絡先電話番号,連絡先内線番号,画像,画像_ライセンス,URL,備考
    352128,1,山口県,柳井市,白壁の町並み,シラカベノマチナミ,,,山口県柳井市柳井津,,,,月火水木金土日,,,随時見学可能,無料,,"中世の町割りがそのまま今日も生きており、約200ｍの街路に面した両側に江戸時代の商家の家並みが続いています。藩政時代には岩国藩のお納戸と呼ばれ、産物を満載した大八車が往来してにぎわった町筋です。
    昭和59年に国の重要伝統的建造物群保存地区に選定されました。往時の面影をしのばせる町並みで、心安らぐひとときを味わえます。",,JR柳井駅から徒歩5分。玖珂I.C.から車で約20分。,白壁周辺の観光客駐車場（無料）を使用,,柳井市経済部商工観光課,0820-22-2111,,,,,

4行目に柳井市の列見出しが、7行目に推奨データセットの列見出しが
それぞれ表示されています。比較してみるとほとんど一致していますが、

- 1列目：「都道府県コード又は市区町村コード」が「市区町村コード」になっている。
- 17列目：「料金（基本）」が「料金(基本)」（半角カッコ）になっている。
- 18列目：「料金（詳細）」が「料金(詳細)」（半角カッコ）になっている。

という違いがあります。この違いを吸収するための変換表 **column_map** を
8行目で作成し、9行目でその変換表をパラメータとして
:py:class:`mapping_cols <tablelinker.convertors.basics.mapping_col.MappingColsConvertor>`
コンバータを呼び出し、マッピングを行っています。
14行目、15行目の結果を見ると、柳井市のデータが推奨データセットと
同じ列名に変更されていることが確認できます。

このサンプルでは確認できませんが、列の順番の入れ替えや欠損などにも
対応できます。


.. _use_with_pandas:

Pandas 連携
-----------

Tablelinker のコンバータにはない複雑な変換処理を
実装する必要があったり、変換結果を Excel や RDBMS テーブルに
出力したい場合などは、 Pandas 連携機能を利用してください。

.. note::

    Excel ファイルや RDBMS の入出力に必要なライブラリ
    （xlrd, sqlalchemy など）を別途インストールする必要があります。

pandas.DataFrame から Table オブジェクトを作成するには
Table クラスメソッド
:py:meth:`~tablelinker.core.table.Table.fromPandas` を利用します。

.. code-block:: python

    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     "都道府県名":["北海道", "青森県", "岩手県"],
    ...     "人口":[5188441, 1232227, 1203203],})
    >>> from tablelinker import Table
    >>> table = Table.fromPandas(df)
    >>> table.write()
    都道府県名,人口
    北海道,5188441
    青森県,1232227
    岩手県,1203203

Table オブジェクトから pandas.DataFrame を作成するには、
:py:meth:`~tablelinker.core.table.Table.toPandas` メソッドを呼び出します。

.. code-block:: python

    >>> new_df = table.toPandas()
    >>> new_df.columns
    Index(['都道府県名', '人口'], dtype='object')
    >>> new_df.to_json(force_ascii=False)
    '{"都道府県名":{"0":"北海道","1":"青森県","2":"岩手県"},"人口":{"0":"5188441","1":"1232227","2":"1203203"}}'

.. note::

    DataFrame オブジェクトが利用可能なメソッドは 
    `Pandas API reference (DataFrame) <https://pandas.pydata.org/docs/reference/frame.html>`_
    を参照してください。

.. _use_with_polars:

Polars 連携
-----------

Polars は軽量・高速な Dataframe ライブラリです。

.. note::

    Polars は Tablelinker をインストールしてもインストールされませんので、
    利用する場合は別途インストールしてください。

polars.DataFrame から Table オブジェクトを作成するには
Table クラスメソッド
:py:meth:`~tablelinker.core.table.Table.fromPolars` を利用します。

.. code-block:: python

    >>> import polars as pl
    >>> df = pl.DataFrame({
    ...     "都道府県名":["北海道", "青森県", "岩手県"],
    ...     "人口":[5188441, 1232227, 1203203],})
    >>> from tablelinker import Table
    >>> table = Table.fromPolars(df)
    >>> table.write()
    都道府県名,人口
    北海道,5188441
    青森県,1232227
    岩手県,1203203

Table オブジェクトから polars.DataFrame を作成するには、
:py:meth:`~tablelinker.core.table.Table.toPolars` メソッドを呼び出します。

.. code-block:: python

    >>> new_df = table.toPolars()
    >>> new_df.columns
    ['都道府県名', '人口']
    >>> new_df.write_json()
    '{"columns":[{"name":"都道府県名","datatype":"Utf8","values":["北海道","青森県","岩手県"]},{"name":"人口","datatype":"Int64","values":[5188441,1232227,1203203]}]}'

.. note::

    DataFrame オブジェクトが利用可能なメソッドは 
    `Polars API reference <https://pola-rs.github.io/polars/py-polars/html/reference/>`_
    を参照してください。

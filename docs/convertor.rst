.. _convertor:

コンバータ
==========

コンバータは、表データを別の表データに変換する処理を表します。

Tablelinker では、列名の変更や列の削除、挿入などの操作、
特定の条件を満たす行の選択など、列や行に対する処理を行うものを
「基本コンバータ」、和暦・西暦変換やジオコーディングなど、
外部の知識を利用して表データに情報を追加したり表現を変換する
処理を行うものを「拡張コンバータ」と便宜上分類しています。

基本コンバータを利用するには外部の辞書等は不要ですが、
拡張コンバータを利用するには事前に辞書をダウンロードしたり、
利用時にインターネット接続が必要になります。


.. _basic_convertor:

基本コンバータ
--------------

以下の基本コンバータが利用可能です。

列操作
^^^^^^

列の増減や名前の変更を伴うコンバータです。
SQL では **ALTER TABLE** を必要とする処理に該当します。

.. autoclass::
    tablelinker.convertors.basics.calc_col.CalcColConvertor

.. autoclass::
    tablelinker.convertors.basics.concat_col.ConcatColConvertor

.. autoclass::
    tablelinker.convertors.basics.concat_col.ConcatColsConvertor

.. autoclass::
    tablelinker.convertors.basics.delete_col.DeleteColConvertor

.. autoclass::
    tablelinker.convertors.basics.delete_col.DeleteColsConvertor

.. autoclass::
    tablelinker.convertors.basics.generate_pk.GeneratePkConvertor

.. autoclass::
    tablelinker.convertors.basics.insert_col.InsertColConvertor

.. autoclass::
    tablelinker.convertors.basics.insert_col.InsertColsConvertor

.. autoclass::
    tablelinker.convertors.basics.mapping_col.MappingColsConvertor

.. autoclass::
    tablelinker.convertors.basics.move_col.MoveColConvertor

.. autoclass::
    tablelinker.convertors.basics.rename_col.RenameColConvertor

.. autoclass::
    tablelinker.convertors.basics.rename_col.RenameColsConvertor

.. autoclass::
    tablelinker.convertors.basics.reorder_col.ReorderColsConvertor

.. autoclass::
    tablelinker.convertors.basics.split_col.SplitColConvertor


行操作
^^^^^^

行の増減を伴うコンバータです。
SQL では **SELECT**, **INSERT**, **DELETE** を必要とする処理に該当します。

.. autoclass::
    tablelinker.convertors.basics.concat_title.ConcatTitleConvertor

.. autoclass::
    tablelinker.convertors.basics.delete_row.StringMatchDeleteRowConvertor

.. autoclass::
    tablelinker.convertors.basics.delete_row.StringContainDeleteRowConvertor

.. autoclass::
    tablelinker.convertors.basics.delete_row.PatternMatchDeleteRowConvertor

.. autoclass::
    tablelinker.convertors.basics.split_col.SplitRowConvertor

.. autoclass::
    tablelinker.convertors.basics.select_row.StringMatchSelectRowConvertor

.. autoclass::
    tablelinker.convertors.basics.select_row.StringContainSelectRowConvertor

.. autoclass::
    tablelinker.convertors.basics.select_row.PatternMatchSelectRowConvertor


値の操作
^^^^^^^^

値の変更を行うコンバータです。
SQL では **UPDATE** を必要とする処理に該当します。

.. autoclass::
    tablelinker.convertors.basics.round.RoundConvertor

.. autoclass::
    tablelinker.convertors.basics.truncate.TruncateConvertor

.. autoclass::
    tablelinker.convertors.basics.update_col.UpdateColConvertor

.. autoclass::
    tablelinker.convertors.basics.update_col.StringMatchUpdateColConvertor

.. autoclass::
    tablelinker.convertors.basics.update_col.StringContainUpdateColConvertor

.. autoclass::
    tablelinker.convertors.basics.update_col.PatternMatchUpdateColConvertor

.. autoclass::
    tablelinker.convertors.basics.zenkaku.ToHankakuConvertor

.. autoclass::
    tablelinker.convertors.basics.zenkaku.ToZenkakuConvertor


拡張コンバータ
--------------

外部知識や外部サービスを利用するコンバータです。

拡張コンバータは辞書の読み込みやネットワーク接続を行う必要があるため、
最初に利用する際に少し時間がかかることがあります。

日時抽出・変換
^^^^^^^^^^^^^^

.. autoclass::
    tablelinker.convertors.extras.date_extract.DateExtractConvertor

.. autoclass::
    tablelinker.convertors.extras.date_extract.DatetimeExtractConvertor

.. autoclass::
    tablelinker.convertors.extras.wareki.ToSeirekiConvertor

.. autoclass::
    tablelinker.convertors.extras.wareki.ToWarekiConvertor

住所ジオコーダ
^^^^^^^^^^^^^^

.. autoclass::
    tablelinker.convertors.extras.geocoder.ToCodeConvertor

.. autoclass::
    tablelinker.convertors.extras.geocoder.ToLatLongConvertor

.. autoclass::
    tablelinker.convertors.extras.geocoder.ToMunicipalityConvertor

.. autoclass::
    tablelinker.convertors.extras.geocoder.ToNodeIdConvertor

.. autoclass::
    tablelinker.convertors.extras.geocoder.ToPostcodeConvertor

.. autoclass::
    tablelinker.convertors.extras.geocoder.ToPrefectureConvertor

MTab アノテーション
^^^^^^^^^^^^^^^^^^^

.. autoclass::
    tablelinker.convertors.extras.mtab.MtabColumnAnnotationConvertor

.. autoclass::
    tablelinker.convertors.extras.mtab.MtabWikilinkConvertor

列の自動マッピング
^^^^^^^^^^^^^^^^^^

.. autoclass::
    tablelinker.convertors.extras.mapping_col.AutoMappingColsConvertor

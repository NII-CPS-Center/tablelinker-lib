from pathlib import Path
import re

import pytest

from tablelinker import Table

sample_dir = Path(__file__).parent.parent / "sample/datafiles"


def test_calc_col():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="calc",
        params={
            "input_col_idx1": "出生数",
            "input_col_idx2": "人口",
            "operator": "/",
            "output_col_name": "出生率（計算）",
            "overwrite": False
        },
    )

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 16
            if lineno == 0:
                # ヘッダに「出生率（計算）」が追加されていることを確認
                assert ",".join(row) == (
                    ',人口,出生数,死亡数,（再掲）,,自　然,死産数,,,'
                    '周産期死亡数,,,婚姻件数,離婚件数,出生率（計算）')

            elif lineno == 4:
                # 計算結果が正しいことを確認
                assert abs(float(row[-1]) - 0.00569) < 1.0e-6


def test_concat_col():
    table = Table(sample_dir / "yanai_tourism_sjis.csv")
    table = table.convert(
        convertor="concat_col",
        params={
            "input_col_idx1": "都道府県名",
            "input_col_idx2": "市区町村名",
            "output_col_name": "自治体名",
            "output_col_idx": "名称",
            "separator": " "
        },
    )

    with table.open(as_dict=True) as dictreader:
        for lineno, row in enumerate(dictreader):
            assert len(row) == 31
            if lineno == 0:
                # ヘッダの「名称」列の前に「自治体名」が追加される
                assert ",".join(row) == (
                    "市区町村コード,NO,都道府県名,市区町村名,自治体名,名称,"
                    "名称_カナ,名称_英語,POIコード,住所,方書,緯度,経度,"
                    "利用可能曜日,開始時間,終了時間,利用可能日時特記事項,"
                    "料金(基本),料金(詳細),説明,説明_英語,アクセス方法,"
                    "駐車場情報,バリアフリー情報,連絡先名称,連絡先電話番号,"
                    "連絡先内線番号,画像,画像_ライセンス,URL,備考"
                )

            elif lineno > 0:
                # 結合結果を確認
                assert row["自治体名"] == "山口県 柳井市"


def test_concat_cols():
    table = Table(sample_dir / "yanai_tourism_sjis.csv")
    table = table.convert(
        convertor="concat_cols",
        params={
            "input_col_idxs": [
                "連絡先名称", "連絡先電話番号", "連絡先内線番号"
            ],
            "output_col_name": "連絡先情報",
            "output_col_idx": "画像",
            "separator": ";"
        },
    )

    with table.open(as_dict=True) as dictreader:
        for lineno, row in enumerate(dictreader):
            assert len(row) == 31
            if lineno == 0:
                # ヘッダの「画像」列の前に「連絡先情報」が追加される
                assert ",".join(row) == (
                    "市区町村コード,NO,都道府県名,市区町村名,名称,"
                    "名称_カナ,名称_英語,POIコード,住所,方書,緯度,経度,"
                    "利用可能曜日,開始時間,終了時間,利用可能日時特記事項,"
                    "料金(基本),料金(詳細),説明,説明_英語,アクセス方法,"
                    "駐車場情報,バリアフリー情報,連絡先名称,連絡先電話番号,"
                    "連絡先内線番号,連絡先情報,画像,画像_ライセンス,URL,備考"
                )

            elif lineno > 0:
                # 結合結果を確認
                assert row["連絡先情報"] == ";".join([
                    row["連絡先名称"],
                    row["連絡先電話番号"],
                    row["連絡先内線番号"]])


def test_concat_title():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="concat_title",
        params={
            "title_lines": 3,
            "empty_value": "",
            "separator": "",
            "hierarchical_heading": True,
        },
    )

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 15
            if lineno == 0:
                # ヘッダ確認
                assert ",".join(row) == (
                    ",人口,出生数,死亡数,（再掲）乳児死亡数,"
                    "（再掲）新生児死亡数,自　然増減数,"
                    "死産数総数,死産数自然死産,死産数人工死産,"
                    "周産期死亡数総数,周産期死亡数22週以後の死産数,"
                    "周産期死亡数早期新生児死亡数,婚姻件数,離婚件数")
            elif lineno == 1:
                # 最初のデータ行を確認
                assert ",".join(row) == (
                    "全　国,123398962,840835,1372755,1512,704,"
                    "-531920,17278,8188,9090,2664,2112,552,525507,193253")


def test_concat_title_data_from():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="concat_title",
        params={
            "data_from": "全　国",
            "empty_value": "",
            "separator": "",
            "hierarchical_heading": True,
        },
    )

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 15
            if lineno == 0:
                # ヘッダ確認
                assert ",".join(row) == (
                    ",人口,出生数,死亡数,（再掲）乳児死亡数,"
                    "（再掲）新生児死亡数,自　然増減数,"
                    "死産数総数,死産数自然死産,死産数人工死産,"
                    "周産期死亡数総数,周産期死亡数22週以後の死産数,"
                    "周産期死亡数早期新生児死亡数,婚姻件数,離婚件数")
            elif lineno == 1:
                # 最初のデータ行を確認
                assert ",".join(row) == (
                    "全　国,123398962,840835,1372755,1512,704,"
                    "-531920,17278,8188,9090,2664,2112,552,525507,193253")


def test_delete_col():
    table = Table(sample_dir / "hachijo_sightseeing.csv")
    table = table.convert(
        convertor="delete_col",
        params={
            "input_col_idx": "座標系",
        },
    )

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 6
            if lineno == 0:
                # ヘッダに「座標系」が存在しないことを確認
                assert ",".join(row) == (
                    "観光スポット名称,所在地,緯度,経度,"
                    "説明,八丈町ホームページ記載")

            elif lineno == 1:
                # レコードから座標系列が削除されていることを確認
                assert ",".join(row[0:4]) == "ホタル水路,,33.108218,139.80102"
                assert row[4].startswith("八丈島は伊豆諸島で唯一、")
                assert row[5] == (
                    "http://www.town.hachijo.tokyo.jp/kankou_spot/"
                    "mitsune.html#01")


def test_delete_row_match():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="delete_row_match",
        params={
            "input_col_idx": 0,
            "query": "",
        },
    )

    with table.open() as reader:
        lines = 0
        for row in reader:
            assert len(row) == 15  # 列数チェック
            if lines > 0:
                assert row[0] != ""   # "" の行は削除

            lines += 1

        # 出力行数をチェック
        assert lines == 72


def test_delete_row_contains():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="delete_row_contains",
        params={
            "input_col_idx": 0,
            "query": "市",
        },
    )

    with table.open() as reader:
        lines = 0
        for row in reader:
            assert len(row) == 15
            if lines > 0:
                assert "市" not in row[0]

            lines += 1

    # 出力行数をチェック
    assert lines == 54


def test_delete_row_pattern():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="delete_row_pattern",
        params={
            "input_col_idx": 0,
            "query": "(^$|.+区部$|.+市$)",
        },
    )

    with table.open() as reader:
        lines = 0
        for row in reader:
            assert len(row) == 15
            if lines > 0:
                assert row[0] != ""
                assert not row[0].endswith("区部")
                assert not row[0].endswith("市")

            lines += 1

    # 出力行数をチェック
    assert lines == 51


def test_generate_pk():
    table = Table(sample_dir / "hachijo_sightseeing.csv")
    table = table.convert(
        convertor="generate_pk",
        params={
            "input_col_idx": "観光スポット名称",
            "output_col_name": "pk",
            "output_col_idx": 0,
        },
    )

    with table.open() as reader:
        keys = {}
        for lineno, row in enumerate(reader):
            assert len(row) == 8
            if lineno == 0:
                # 先頭列に「pk」が追加されていることを確認
                assert ",".join(row) == (
                    "pk,観光スポット名称,所在地,緯度,経度,"
                    "座標系,説明,八丈町ホームページ記載")

            else:
                # pk 欄には一意のキー文字列
                assert len(row[0]) == 6
                assert row[0] not in keys
                keys[row[0]] = True


def test_generate_pk_not_unique():
    table = Table(sample_dir / "hachijo_sightseeing.csv")

    with pytest.raises(ValueError):
        table = table.convert(
            convertor="generate_pk",
            params={
                "input_col_idx": "座標系",
                "output_col_name": "pk",
                "output_col_idx": 0,
            },
        )

    table = table.convert(
        convertor="generate_pk",
        params={
            "input_col_idx": "座標系",
            "output_col_name": "pk",
            "output_col_idx": 0,
            "error_if_not_unique": False,
            "skip_if_not_unique": True,
        },
    )

    with table.open() as reader:
        keys = {}
        for lineno, row in enumerate(reader):
            assert len(row) == 8
            if lineno == 0:
                # 先頭列に「pk」が追加されていることを確認
                assert ",".join(row) == (
                    "pk,観光スポット名称,所在地,緯度,経度,"
                    "座標系,説明,八丈町ホームページ記載")

            else:
                # pk 欄には一意のキー文字列
                assert len(row[0]) == 6
                assert row[0] not in keys
                keys[row[0]] = True

        assert lineno == 1  # 先頭の行以外はスキップされる


def test_insert_col():
    table = Table(sample_dir / "hachijo_sightseeing.csv")
    table = table.convert(
        convertor="insert_col",
        params={
            "output_col_idx": "所在地",
            "output_col_name": "都道府県名",
            "value": "東京都",
        },
    )

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 8
            if lineno == 0:
                # 「所在地」の前に「都道府県名」が追加されていることを確認
                assert ",".join(row) == (
                    "観光スポット名称,都道府県名,所在地,緯度,経度,"
                    "座標系,説明,八丈町ホームページ記載")

            else:
                # 都道府県名欄に「東京都」が追加されていることを確認
                assert row[1] == "東京都"


def test_insert_cols():
    table = Table(sample_dir / "hachijo_sightseeing.csv")
    table = table.convert(
        convertor="insert_cols",
        params={
            "output_col_idx": "所在地",
            "output_col_names": ["都道府県名", "市区町村名"],
            "values": ["東京都", "八丈町"],
        },
    )

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 9
            if lineno == 0:
                # 「所在地」の前に「都道府県名」「市区町村名」が
                # 追加されていることを確認
                assert ",".join(row) == (
                    "観光スポット名称,都道府県名,市区町村名,所在地,"
                    "緯度,経度,座標系,説明,八丈町ホームページ記載")

            else:
                # 都道府県名欄に「東京都」が追加されていることを確認
                assert row[1] == "東京都"
                # 市区町村名に「八丈町」が追加されていることを確認
                assert row[2] == "八丈町"


def test_mapping_cols():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="mapping_cols",
        params={
            "column_map": {
                "都道府県": 0,
                "人口": "人口",
                "婚姻件数": "婚姻件数",
                "離婚件数": "離婚件数",
            },
        },
    )

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 4
            if lineno == 0:
                # ヘッダを確認
                assert ",".join(row) == "都道府県,人口,婚姻件数,離婚件数"

            elif lineno == 4:
                # 列の値が正しくマップされていることを確認
                assert row == ["01 北海道", "5188441", "20904", "9070"]
                break


def test_move_col():
    table = Table(sample_dir / "hachijo_sightseeing.csv")
    table = table.convert(
        convertor="move_col",
        params={
            "input_col_idx": "経度",
            "output_col_idx": "緯度"
        },
    )

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 7
            if lineno == 0:
                # ヘッダの順番が「経度」「緯度」に入れ替わっていることを確認
                assert ",".join(row) == (
                    "観光スポット名称,所在地,経度,緯度,"
                    "座標系,説明,八丈町ホームページ記載")

            elif lineno == 1:
                # 緯度と経度が入れ替わっていることを確認
                assert row[2] == "139.80102"
                assert row[3] == "33.108218"


def test_rename_col():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="rename_col",
        params={
            "input_col_idx": 0,
            "output_col_name": "都道府県名",
        },
    )

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 15
            if lineno == 0:
                # 0列目のヘッダが「都道府県名」に変更されていることを確認
                assert ",".join(row) == (
                    "都道府県名,人口,出生数,死亡数,（再掲）,,自　然,死産数,,,"
                    "周産期死亡数,,,婚姻件数,離婚件数")


def test_reorder_cols():
    table = Table(sample_dir / "hachijo_sightseeing.csv")
    table = table.convert(
        convertor="reorder_cols",
        params={
            "column_list": [
                "所在地",
                "経度",
                "緯度",
                "説明"
            ]
        },
    )

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 4
            if lineno == 0:
                assert row == ["所在地", "経度", "緯度", "説明"]


def test_select_row_match():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="select_row_match",
        params={
            "input_col_idx": 0,
            "query": "13 東京都"
        },
    )

    with table.open() as reader:
        lines = 0
        for row in reader:
            assert len(row) == 15
            if lines > 0:
                assert row[0] == "13 東京都"

            lines += 1

        assert lines == 2


def test_select_row_contains():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="select_row_contains",
        params={
            "input_col_idx": 0,
            "query": "東京都"
        },
    )

    with table.open() as reader:
        lines = 0
        for row in reader:
            assert len(row) == 15
            if lines > 0:
                assert row[0] in ("13 東京都", "50 東京都の区部",)

            lines += 1

        assert lines == 3


def test_select_row_pattern():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="select_row_pattern",
        params={
            "input_col_idx": 0,
            "query": ".*東京都?$"
        },
    )

    with table.open() as reader:
        lines = 0
        for row in reader:
            assert len(row) == 15
            if lines > 0:
                assert row[0] == "13 東京都"

            lines += 1

        assert lines == 2


def test_split_col():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="split_col",
        params={
            "input_col_idx": 0,
            "output_col_names": ["コード", "地域名"],
            "separator": r"\s+",
        },
    )

    with table.open(as_dict=True) as dictreader:
        """
        as_dict == True をセットした場合、列名が同じ列は
        最初の列にしかアクセスできない点に注意。
        列数もその分減少する（15 -> 10）。
        """
        lines = 0
        for row in dictreader:
            assert len(row) == 12  # "コード", "地域名" の2列追加
            if lines > 0:
                assert " " not in row["コード"]

            lines += 1


def test_split_row():
    table = Table(sample_dir / "yanai_tourism_sjis.csv")
    table = table.convert(
        convertor="split_row",
        params={
            "input_col_idx": "アクセス方法",
            "separator": "。"
        }
    )

    with table.open(as_dict=True) as dictreader:
        lines = 0
        for row in dictreader:
            assert len(row) == 30  # 列数は変わらない
            assert "。" not in row["アクセス方法"]
            lines += 1

        assert lines == 51  # 列に分割するので増える


def test_truncate():
    table = Table(sample_dir / "hachijo_sightseeing.csv")
    table = table.convert(
        convertor="truncate",
        params={
            "input_col_idx": "説明",
            "length": 20,
            "ellipsis": "...",
            "overwrite": True
        },
    )

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 7
            if lineno == 0:
                # 「説明」列は overwrite するので元の位置
                assert ",".join(row) == (
                    "観光スポット名称,所在地,緯度,経度,座標系,"
                    "説明,八丈町ホームページ記載")
                continue

            # レコードの最後列が切り詰められていることを確認
            value = row[5]
            if len(value) > 20:
                assert value.endswith("...")


def test_truncate_replace():
    table = Table(sample_dir / "hachijo_sightseeing.csv")
    table = table.convert(
        convertor="truncate",
        params={
            "input_col_idx": "説明",
            "output_col_idx": "説明",
            "length": 20,
            "ellipsis": "...",
            "overwrite": True
        },
    )

    with table.open(as_dict=True) as dictreader:
        for lineno, row in enumerate(dictreader):
            assert len(row) == 7
            if lineno == 0:
                # 「説明」列は元の場所に残る
                assert ",".join(row) == (
                    "観光スポット名称,所在地,緯度,経度,座標系,"
                    "説明,八丈町ホームページ記載")
                continue

            # 説明列が切り詰められていることを確認
            value = row["説明"]
            if len(value) > 20:
                assert value.endswith("...")


def test_update_row_match():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="update_col_match",
        params={
            "input_col_idx": 0,
            "query": "全　国",
            "new": "全国"
        },
    )

    with table.open() as reader:
        lines = 0
        for lineno, row in enumerate(reader):
            assert len(row) == 15
            lines += 1
            if lineno == 3:
                assert row[0] == "全国"

        assert lines == 74


def test_update_row_contains():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="update_col_contains",
        params={
            "input_col_idx": 0,
            "query": "　",
            "new": ""
        },
    )

    with table.open() as reader:
        lines = 0
        for row in reader:
            assert len(row) == 15
            if lines > 0:
                assert "　" not in row[0]

            lines += 1

        assert lines == 74


def test_update_row_pattern():
    table = Table(sample_dir / "ma030000.csv")
    table = table.convert(
        convertor="update_col_pattern",
        params={
            "input_col_idx": 0,
            "query": r"^\d\d\s",
            "new": ""
        },
    )

    with table.open() as reader:
        lines = 0
        for row in reader:
            assert len(row) == 15
            if lines > 0:
                assert row[0] == '' or row[0][0] not in '0123456789'

            lines += 1

        assert lines == 74


def test_to_hankaku():
    data = (
        "機関名,部署名,連絡先電話番号\n"
        "国立情報学研究所,総務チーム,０３－４２１２－２０００\n"
        "国立情報学研究所,広報チーム,０３－４２１２－２１６４\n")
    table = Table(data=data)
    table = table.convert(
        convertor="to_hankaku",
        params={
            "input_col_idx": "連絡先電話番号",
            "overwrite": True,
        },
    )

    with table.open(as_dict=True) as dictreader:
        for lineno, row in enumerate(dictreader):
            assert len(row) == 3
            if lineno > 0:
                # 「連絡先電話番号」列は半角文字に変換
                assert re.match(r'^[0-9\-]*$', row["連絡先電話番号"])


def test_to_zenkaku():
    data = (
        "機関名,所在地\n"
        "国立情報学研究所,千代田区一ツ橋2-1-2\n"
        "デジタル庁,\"千代田区紀尾井町1番3号 19階,20階\"\n")
    table = Table(data=data)
    table = table.convert(
        convertor="to_zenkaku",
        params={
            "input_col_idx": "所在地",
            "overwrite": True,
        },
    )

    with table.open(as_dict=True) as dictreader:
        for lineno, row in enumerate(dictreader):
            assert len(row) == 2
            if lineno > 0:
                # 「所在地」列は全角文字に変換
                assert re.match(r'^[^0-9\-]*$', row["所在地"])


def test_input_output_convertor1():
    """
    InputOutputConverter のテスト。

    出力列名も出力位置も指定しない場合は
    既存列の位置にそのまま上書きする。
    """
    data = (
        "col0,col1,col2,col3\n"
        "00,01,02,03\n"
        "10,11,12,13\n"
        "20,21,22,23\n")
    table = Table(data=data).convert(
        convertor="round",
        params={
            "input_col_idx": "col0",
            "overwrite": True,
        })

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 4
            if lineno == 0:
                assert row == ["col0", "col1", "col2", "col3"]


def test_input_output_convertor2():
    """
    InputOutputConverter のテスト。

    出力位置だけ指定した場合、既存列を削除して
    指定した位置に出力する。
    """
    data = (
        "col0,col1,col2,col3\n"
        "00,01,02,03\n"
        "10,11,12,13\n"
        "20,21,22,23\n")
    table = Table(data=data).convert(
        convertor="round",
        params={
            "input_col_idx": "col1",
            "overwrite": True,
            "output_col_idx": 3,
        })

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 4
            if lineno == 0:
                assert row == ["col0", "col2", "col1", "col3"]


def test_input_output_convertor3():
    """
    InputOutputConverter のテスト。

    出力位置だけ指定した場合、既存列を削除して
    指定した位置に出力する。
    出力位置を列数以上に指定した場合、最後尾に追加する。
    """
    data = (
        "col0,col1,col2,col3\n"
        "00,01,02,03\n"
        "10,11,12,13\n"
        "20,21,22,23\n")
    table = Table(data=data).convert(
        convertor="round",
        params={
            "input_col_idx": "col1",
            "overwrite": True,
            "output_col_idx": 99,
        })

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 4
            if lineno == 0:
                assert row == ["col0", "col2", "col3", "col1"]


def test_input_output_convertor4():
    """
    InputOutputConverter のテスト。

    出力列名を指定し、出力先を指定しない場合は、
    新規列を最後尾に追加する。
    """
    data = (
        "col0,col1,col2,col3\n"
        "00,01,02,03\n"
        "10,11,12,13\n"
        "20,21,22,23\n")
    table = Table(data=data).convert(
        convertor="round",
        params={
            "input_col_idx": "col1",
            "output_col_name": "col1+",
            "overwrite": False,
        })

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 5
            if lineno == 0:
                assert row == ["col0", "col1", "col2", "col3", "col1+"]


def test_input_output_convertor5():
    """
    InputOutputConverter のテスト。

    出力列名も出力先も指定した場合は、
    新規列を指定した位置に挿入する。
    """
    data = (
        "col0,col1,col2,col3\n"
        "00,01,02,03\n"
        "10,11,12,13\n"
        "20,21,22,23\n")
    table = Table(data=data).convert(
        convertor="round",
        params={
            "input_col_idx": "col1",
            "output_col_name": "col1+",
            "output_col_idx": "col2",
        })

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 5
            if lineno == 0:
                assert row == ["col0", "col1", "col1+", "col2", "col3"]

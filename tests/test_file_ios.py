import csv
import io
from pathlib import Path
import tempfile

import pytest

from tablelinker import Table

sample_dir = Path(__file__).parent.parent / "sample/datafiles"


def test_excel_open():
    # シート名を指定せずに Excel ファイルを開くと
    # 最初のシートが開く
    table = Table(
        file=sample_dir / "hachijo_sightseeing.xlsx",
        sheet=None)
    with table.open() as reader:
        for row in reader:
            assert ",".join(row) == (
                "観光スポット名称,所在地,緯度,経度,座標系,"
                "説明,八丈町ホームページ記載"
            )
            break

    # 存在しないシート名を指定して Excel ファイルを開くと
    # ValueError
    table = Table(
        file=sample_dir / "hachijo_sightseeing.xlsx",
        sheet="その他")
    with pytest.raises(ValueError):
        table.open()

    # 存在するシート名を指定して Excel ファイルを開く
    table = Table(
        file=sample_dir / "hachijo_sightseeing.xlsx",
        sheet="観光スポット")
    with table.open() as reader:
        for row in reader:
            assert ",".join(row) == (
                "観光スポット名称,所在地,緯度,経度,座標系,"
                "説明,八丈町ホームページ記載"
            )
            break


def test_excel_save():
    table = Table(sample_dir / "hachijo_sightseeing.xlsx")

    with tempfile.TemporaryDirectory() as tmpdir:
        temppath = Path(tmpdir) / "tmpfile.csv"
        table.save(temppath)

        with open(temppath, "r", newline="") as f:
            reader = csv.reader(f)
            for lineno, row in enumerate(reader):
                assert len(row) == 7
                if lineno == 0:
                    assert ",".join(row) == (
                        "観光スポット名称,所在地,緯度,経度,座標系,"
                        "説明,八丈町ホームページ記載"
                    )


def test_excel_write():
    table = Table(sample_dir / "hachijo_sightseeing.xlsx")

    # write() の出力をテキストバッファに保存
    buf = io.StringIO()
    table.write(lines=5, file=buf)

    # バッファの内容を csv reader で読み込んで検証
    with io.StringIO(buf.getvalue()) as f:
        reader = csv.reader(f)
        for lineno, row in enumerate(reader):
            assert len(row) == 7
            if lineno == 0:
                assert ",".join(row) == (
                    "観光スポット名称,所在地,緯度,経度,座標系,"
                    "説明,八丈町ホームページ記載"
                )

            assert lineno < 5


def test_excel_convert():
    table = Table(sample_dir / "hachijo_sightseeing.xlsx")
    table = table.convert(
        convertor="move_col",
        params={
            "input_col_idx": "座標系",
        },
    )

    with table.open() as csv:
        for lineno, row in enumerate(csv):
            assert len(row) == 7
            if lineno == 0:
                # ヘッダ「座標系」が最後尾に移動していることを確認
                assert ",".join(row) == (
                    "観光スポット名称,所在地,緯度,経度,"
                    "説明,八丈町ホームページ記載,座標系")

            elif lineno == 1:
                # レコードから座標系列が削除されていることを確認
                assert ",".join(row[0:4]) == "ホタル水路,,33.108218,139.80102"
                assert row[4].startswith("八丈島は伊豆諸島で唯一、")
                assert row[5] == (
                    "http://www.town.hachijo.tokyo.jp/kankou_spot/"
                    "mitsune.html#01")


def test_read_sjis():
    """
    シフトJIS CSV ファイルを読み込めることを確認。
    """
    table = Table(sample_dir / "yanai_tourism_sjis.csv")
    correct_headers = (
        "市区町村コード,NO,都道府県名,市区町村名,名称,名称_カナ,名称_英語,"
        "POIコード,住所,方書,緯度,経度,利用可能曜日,開始時間,終了時間,"
        "利用可能日時特記事項,料金(基本),料金(詳細),説明,説明_英語,"
        "アクセス方法,駐車場情報,バリアフリー情報,連絡先名称,連絡先電話番号,"
        "連絡先内線番号,画像,画像_ライセンス,URL,備考"
    )
    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == len(correct_headers.split(","))
            if lineno == 0:
                assert ",".join(row) == correct_headers


def test_read_tsv():
    """
    タブ区切り CSV ファイルを読めることを確認。
    """
    table = Table(sample_dir / "yanai_tourism_tsv.txt")
    correct_headers = (
        "市区町村コード,NO,都道府県名,市区町村名,名称,名称_カナ,名称_英語,"
        "POIコード,住所,方書,緯度,経度,利用可能曜日,開始時間,終了時間,"
        "利用可能日時特記事項,料金(基本),料金(詳細),説明,説明_英語,"
        "アクセス方法,駐車場情報,バリアフリー情報,連絡先名称,連絡先電話番号,"
        "連絡先内線番号,画像,画像_ライセンス,URL,備考"
    )
    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == len(correct_headers.split(","))
            if lineno == 0:
                assert ",".join(row) == correct_headers


def test_skip_csv_comments():
    """
    CSV ファイルのコメント行を正しくスキップできることを確認。
    """
    table = Table(sample_dir / "kyotenbyoinlist20220101.csv")
    correct_headers = (
        "二次保健医療圏,,施設名,所在地,電話番号,病床数,三次\n救急"
    )
    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == len(correct_headers.split(","))
            if lineno == 0:
                assert ",".join(row) == correct_headers


def test_datatype_adjustment():
    """
    CSV ファイルのデータ型を正しく判定できていることを確認。
    """
    table = Table(sample_dir / "major_results_2020.xlsx")
    with table.open(adjust_datatype=True) as reader:
        for row in reader:
            if row[0] == "00_全国":
                assert row[4] == 126146099
                assert row[8] == -948646
                assert row[9] == -0.74641
            elif row[1] == "01463_占冠村":
                assert row[37] == "-"  # 文字列はそのまま


def test_datatype_adjustment_dict():
    """
    CSV ファイルのデータ型を dict リーダーでも
    正しく判定できていることを確認。
    """
    table = Table(sample_dir / "yanai_tourism_sjis.csv")
    with table.open(as_dict=True, adjust_datatype=True) as dictreader:
        for lineno, row in enumerate(dictreader):
            assert len(row) == 30
            if lineno > 0:
                assert isinstance(row["緯度"], float) or row["緯度"] == ""
                assert isinstance(row["経度"], float) or row["経度"] == ""

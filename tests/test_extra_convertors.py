from pathlib import Path
import re

from tablelinker import Table

sample_dir = Path(__file__).parent.parent / "sample/datafiles"


def test_date_extract():
    # 東京国立博物館「展示・催し物」より作成
    # https://www.tnm.jp/modules/r_calender/index.php
    data = (
        "展示名,会場,期間\n"
        "令和5年 新指定 国宝・重要文化財,平成館 企画展示室,"
        "2023年1月31日（火） ～ 2023年2月19日（日）\n"
        "特別企画「大安寺の仏像」,本館 11室,"
        "2023年1月2日（月・休） ～ 2023年3月19日（日）\n"
        "未来の国宝―東京国立博物館　書画の逸品―,本館 2室,"
        "2023年1月31日（火） ～ 2023年2月26日（日）\n"
        "創立150年記念特集　王羲之と蘭亭序,東洋館 8室,"
        "2023年1月31日（火） ～ 2023年4月23日（日）\n"
        "創立150年記念特集　近世能狂言面名品選 ー「天下一」号を授かった面打ー,"
        "本館 14室,2023年1月2日（月・休） ～ 2023年2月26日（日）\n"
    )
    table = Table(data=data)
    table = table.convert(
        convertor="date_extract",
        params={
            "input_col_idx": "期間",
            "output_col_name": "開始日",
            "overwrite": True,
        },
    )

    with table.open(as_dict=True) as dictreader:
        for lineno, row in enumerate(dictreader):
            assert len(row) == 4
            if lineno > 0:
                assert re.match(r'^\d{4}\-\d{2}-\d{2}', row["開始日"])


def test_datetime_extract():
    data = (
        "発生時刻,震源地,マグニチュード,最大震度\n"
        "2023年1月31日 4時15分ごろ,宮城県沖,4.3,2\n"
        "2023年1月30日 18時16分ごろ,富山県西部,3.4,2\n"
        "2023年1月30日 9時32分ごろ,栃木県南部,3.5,1\n"
        "2023年1月29日 21時20分ごろ,神奈川県西部,4.8,3\n"
        "2023年1月29日 12時07分ごろ,茨城県北部,2.9,1\n"
        "2023年1月29日 9時18分ごろ,和歌山県北部,2.7,1\n"
        "2023年1月27日 15時03分ごろ,福島県沖,4.2,2\n"
        "2023年1月27日 13時51分ごろ,岐阜県美濃中西部,2.7,1\n"
        "2023年1月27日 13時49分ごろ,岐阜県美濃中西部,3.0,1\n"
        "2023年1月27日 13時28分ごろ,福島県沖,3.6,1\n"
    )
    table = Table(data=data)
    table = table.convert(
        convertor="datetime_extract",
        params={
            "input_col_idx": "発生時刻",
            "output_col_name": "正規化日時",
            "format": "%Y-%m-%dT%H:%M:00+0900",
        },
    )

    with table.open(as_dict=True) as dictreader:
        for lineno, row in enumerate(dictreader):
            assert len(row) == 5
            if lineno == 0:
                assert row["正規化日時"] == "2023-01-31T04:15:00+0900"

            if lineno > 0:
                assert re.match(
                    r'^\d{4}\-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
                    row["正規化日時"])


def test_to_seireki():
    # 気象庁「過去に発生した火山災害」より作成
    # https://www.data.jma.go.jp/vois/data/tokyo/STOCK/kaisetsu/volcano_disaster.htm
    data = (
        "噴火年月日,火山名,犠牲者（人）,備考\n"
        "享保6年6月22日,浅間山,15,噴石による\n"
        "寛保元年8月29日,渡島大島,1467,岩屑なだれ・津波による\n"
        "明和元年7月,恵山,多数,噴気による\n"
        "安永8年11月8日,桜島,150余,噴石・溶岩流などによる「安永大噴火」\n"
        "天明元年4月11日,桜島,8、不明7,高免沖の島で噴火、津波による\n"
        "天明3年8月5日,浅間山,1151,火砕流、土石なだれ、吾妻川・利根川の洪水による\n"
        "天明5年4月18日,青ヶ島,130～140,当時327人の居住者のうち130～140名が死亡と推定され、残りは八丈島に避難\n"
        "寛政4年5月21日,雲仙岳,約15000,地震及び岩屑なだれによる「島原大変肥後迷惑」\n"
        "文政5年3月23日,有珠山,103,火砕流による\n"
        "天保12年5月23日,口永良部島,多数,噴火による、村落焼亡\n"
        "安政3年9月25日,北海道駒ヶ岳,19～27,噴石、火砕流による\n"
        "明治21年7月15日,磐梯山,461（477とも）,岩屑なだれにより村落埋没\n"
        "明治33年7月17日,安達太良山,72,火口の硫黄採掘所全壊\n"
        "明治35年8月上旬(7日～9日のいつか),伊豆鳥島,125,全島民死亡。\n"
        "大正3年1月12日,桜島,58～59,噴火・地震による「大正大噴火」\n"
        "大正15年5月24日,十勝岳,144（不明を含む）,融雪型火山泥流による「大正泥流」\n"
        "昭和15年7月12日,三宅島,11,火山弾・溶岩流などによる\n"
        "昭和27年9月24日,ベヨネース列岩,31,海底噴火（明神礁）、観測船第5海洋丸遭難により全員殉職\n"
        "昭和33年6月24日,阿蘇山,12,噴石による\n"
        "平成3年6月3日,雲仙岳,43（不明を含む）,火砕流による「平成3年(1991年)雲仙岳噴火」\n"
        "平成26年9月27日,御嶽山,63（不明を含む）,噴石等による\n"
    )
    table = Table(data=data)
    table = table.convert(
        convertor="to_seireki",
        params={
            "input_col_idx": "噴火年月日",
            "output_col_idx": 0,
            "overwrite": True,
        },
    )

    with table.open(as_dict=True) as dictreader:
        for lineno, row in enumerate(dictreader):
            assert len(row) == 4
            if lineno > 0:
                # 「噴火年月日」列は西暦に変換
                assert re.match(r'^[0-9]{4}', row["噴火年月日"])


def test_to_wareki():
    # 統計局「人口推計 / 長期時系列データ 長期時系列データ
    # （平成12年～令和２年）」より作成
    # https://www.e-stat.go.jp/stat-search/files?page=1&layout=datalist&toukei=00200524&tstat=000000090001&cycle=0&tclass1=000000090004&tclass2=000001051180&tclass3val=0
    data = (
        "年次,総人口（千人）\n"
        "2000,126926\n"
        "2005,127768\n"
        "2010,128057\n"
        "2015,127095\n"
        "2020,126146\n"
    )
    table = Table(data=data)
    table = table.convert(
        convertor="to_wareki",
        params={
            "input_col_idx": "年次",
            "output_col_name": "和暦",
            "output_col_idx": 1,
        },
    )

    with table.open(as_dict=True) as dictreader:
        for lineno, row in enumerate(dictreader):
            assert len(row) == 3
            if lineno == 0:
                assert ",".join(row) == "年次,和暦,総人口（千人）"
            elif int(row["年次"]) == 2019:
                assert re.match(r'^(平成|令和)', row["和暦"])
            elif int(row["年次"]) < 2019:
                assert re.match(r'^平成', row["和暦"])
            else:
                assert re.match(r'^令和', row["和暦"])


def test_geocoder_code():
    table = Table(sample_dir / "hachijo_sightseeing.csv")
    table = table.convert(
        convertor="geocoder_code",
        params={
            "input_col_idx": "所在地",
            "output_col_name": "市区町村コード",
            "output_col_idx": 0,
            "within": ["東京都"],
            "default": "0"
        }
    )

    with table.open() as csv:
        for lineno, row in enumerate(csv):
            assert len(row) == 8
            if lineno == 0:
                # ヘッダに「市区町村コード」が追加されていることを確認
                assert ",".join(row) == (
                    '市区町村コード,観光スポット名称,所在地,'
                    '緯度,経度,座標系,説明,八丈町ホームページ記載')
            elif row[2] == "":
                assert row[0] == "0"
            elif "八丈町" in row[2]:
                assert row[0] == "13401"  # 八丈町コード


def test_geocoder_latlong():
    table = Table(sample_dir / "hachijo_sightseeing.csv")
    table = table.convert(
        convertor="geocoder_latlong",
        params={
            "input_col_idx": "所在地",
            "output_col_names": ["緯度", "経度", "レベル"],
            "output_col_idx": "説明",
            "within": ["東京都"],
            "default": "",
        }
    )

    with table.open() as csv:
        for lineno, row in enumerate(csv):
            assert len(row) == 8
            if lineno == 0:
                # ヘッダの「説明」列の前に「緯度」「経度」「レベル」列が
                # 追加されていることを確認
                assert ",".join(row) == (
                    "観光スポット名称,所在地,座標系,"
                    "緯度,経度,レベル,説明,八丈町ホームページ記載")
            elif row[1] == "":
                assert row[5] == ""
            else:
                assert int(row[5]) >= 3  # 町以上まで一致している


def test_geocoder_municipality():
    table = Table(sample_dir / "hachijo_sightseeing.csv")
    table = table.convert(
        convertor="geocoder_municipality",
        params={
            "input_col_idx": "所在地",
            "output_col_names": ["市区町村名"],
            "output_col_idx": 0,
            "within": ["東京都"],
            "default": "不明"
        }
    )

    with table.open() as csv:
        for lineno, row in enumerate(csv):
            assert len(row) == 8
            if lineno == 0:
                # ヘッダに「市区町村名」が追加されていることを確認
                assert ",".join(row) == (
                    '市区町村名,観光スポット名称,所在地,'
                    '緯度,経度,座標系,説明,八丈町ホームページ記載')
            elif row[2] == "":
                assert row[0] == "不明"
            else:
                assert row[0] == "八丈町"


def test_geocoder_municipality_seirei():
    # https://www.library.city.chiba.jp/facilities/index.html より作成
    data = (
        "施設名,所在地,連絡先電話番号\n"
        "中央図書館,中央区弁天3-7-7,043-287-3980\n"
        "みやこ図書館白旗分館,中央区白旗1-3-16,043-264-8566\n"
        "稲毛図書館,稲毛区小仲台5-1-1,043-254-1845\n"
        "若葉図書館泉分館,若葉区野呂町622-10,043-228-2982\n"
        "緑図書館土気図書室,緑区土気町1634,043-294-1666\n"
        "みずほハスの花図書館,花見川区瑞穂1-1花見川区役所１階,043-275-6330\n"
        "花見川図書館,花見川区こてはし台5-9-7,043-250-2851\n"
        "若葉図書館,若葉区千城台西2-1-1,043-237-9361\n"
        "緑図書館,緑区おゆみ野3-15-2,043-293-5080\n"
        "美浜図書館,美浜区高洲3-12-1,043-277-3003\n"
        "みやこ図書館,中央区都町3-11-3,043-233-8333\n"
        "花見川図書館花見川団地分館,花見川区花見川3-31-101,043-250-5111\n"
        "若葉図書館西都賀分館,若葉区西都賀2-8-8,043-254-8681\n"
        "緑図書館あすみが丘分館,緑区あすみが丘7-2-4,043-295-0200\n"
        "美浜図書館打瀬分館,美浜区打瀬2丁目13番地（幕張ベイタウン・コア内）,043-272-4646\n"
    )
    table = Table(data=data)
    table = table.convert(
        convertor="geocoder_municipality",
        params={
            "input_col_idx": "所在地",
            "output_col_names": ["市町村名", "区名"],
            "default": ""
        }
    )

    with table.open(as_dict=True) as dictreader:
        for lineno, row in enumerate(dictreader):
            assert len(row) == 5
            if lineno == 0:
                # ヘッダに市町村名と区名が追加されていることを確認
                assert ",".join(row) == \
                    '施設名,所在地,連絡先電話番号,市町村名,区名'
            else:
                assert row["市町村名"] == "千葉市"
                assert row["区名"].endswith("区")


def test_geocoder_nodeid():
    data = (
        "機関名,部署名,所在地,連絡先電話番号\n"
        "国立情報学研究所,総務チーム,千代田区一ツ橋２－１－２,03-4212-2000\n"
        "国立情報学研究所,広報チーム,一ッ橋二丁目1-2,03-4212-2164\n")
    table = Table(data=data)
    table = table.convert(
        convertor="geocoder_nodeid",
        params={
            "input_col_idx": "所在地",
            "output_col_name": "ノードID"
        }
    )

    with table.open(as_dict=True) as dictreader:
        for lineno, row in enumerate(dictreader):
            assert len(row) == 5
            if lineno == 0:
                # ヘッダに「ノードID」が追加されていることを確認
                assert ",".join(row) == \
                    '機関名,部署名,所在地,連絡先電話番号,ノードID'
            else:
                assert re.match(r'^\d+$', row["ノードID"])


def test_geocoder_postcode():
    data = (
        "機関名,部署名,所在地,連絡先電話番号\n"
        "国立情報学研究所,総務チーム,千代田区一ツ橋２－１－２,03-4212-2000\n"
        "国立情報学研究所,広報チーム,一ッ橋二丁目1-2,03-4212-2164\n")
    table = Table(data=data)
    table = table.convert(
        convertor="geocoder_postcode",
        params={
            "input_col_idx": "所在地",
            "output_col_name": "郵便番号",
            "output_col_idx": "所在地",
            "hiphen": True,
            "default": ""
        }
    )

    with table.open(as_dict=True) as dictreader:
        for lineno, row in enumerate(dictreader):
            assert len(row) == 5
            if lineno == 0:
                # ヘッダに「郵便番号」が追加されていることを確認
                assert ",".join(row) == \
                    '機関名,部署名,郵便番号,所在地,連絡先電話番号'
            else:
                assert row["郵便番号"] == "101-0003"


def test_geocoder_prefecture():
    table = Table(sample_dir / "hachijo_sightseeing.csv")
    table = table.convert(
        convertor="geocoder_prefecture",
        params={
            "input_col_idx": "所在地",
            "output_col_name": "都道府県名",
            "output_col_idx": 0,
            "default": "東京都"
        }
    )

    with table.open() as csv:
        for lineno, row in enumerate(csv):
            assert len(row) == 8
            if lineno == 0:
                # ヘッダに「都道府県名」が追加されていることを確認
                assert ",".join(row) == (
                    '都道府県名,観光スポット名称,所在地,'
                    '緯度,経度,座標系,説明,八丈町ホームページ記載')
            else:
                assert row[0] == "東京都"


def test_mtab_wikilink():
    data = (
        "col0,col1,col2,col3\n"
        "2MASS J10540655-0031018,-5.7,19.3716366,13.635635128508735\n"
        "2MASS J0464841+0715177,-2.7747499999999996,26.671235999999997,"
        "11.818755055646479\n"
        "2MAS J08351104+2006371,72.216,3.7242887999999996,128.15196099865955\n"
        "2MASS J08330994+186328,-6.993,6.0962562,127.64996294136303\n"
    )
    table = Table(data=data)
    table = table.convert(
        convertor="mtab_wikilink",
        params={
            "input_col_idx": "col0",
            "output_col_name": "Wikilink",
            "overwrite": True,
        },
    )

    with table.open() as csv:
        for lineno, row in enumerate(csv):
            assert len(row) == 5
            if lineno == 0:
                # 最後尾に "Wikilink" が追加されていることを確認
                assert ",".join(row) == "col0,col1,col2,col3,Wikilink"
            else:
                assert row[4].startswith("http://www.wikidata.org/entity/")


def test_mtab_cta():
    # 気象庁「過去に発生した火山災害」より作成
    # https://www.data.jma.go.jp/vois/data/tokyo/STOCK/kaisetsu/volcano_disaster.htm
    data = (
        "噴火年月日,火山名,犠牲者（人）,備考\n"
        "享保6年6月22日,浅間山,15,噴石による\n"
        "寛保元年8月29日,渡島大島,1467,岩屑なだれ・津波による\n"
        "明和元年7月,恵山,多数,噴気による\n"
        "安永8年11月8日,桜島,150余,噴石・溶岩流などによる「安永大噴火」\n"
        "天明元年4月11日,桜島,8、不明7,高免沖の島で噴火、津波による\n"
        "天明3年8月5日,浅間山,1151,火砕流、土石なだれ、吾妻川・利根川の洪水による\n"
        "天明5年4月18日,青ヶ島,130～140,当時327人の居住者のうち130～140名が死亡と推定され、残りは八丈島に避難\n"
        "寛政4年5月21日,雲仙岳,約15000,地震及び岩屑なだれによる「島原大変肥後迷惑」\n"
        "文政5年3月23日,有珠山,103,火砕流による\n"
        "天保12年5月23日,口永良部島,多数,噴火による、村落焼亡\n"
        "安政3年9月25日,北海道駒ヶ岳,19～27,噴石、火砕流による\n"
        "明治21年7月15日,磐梯山,461（477とも）,岩屑なだれにより村落埋没\n"
        "明治33年7月17日,安達太良山,72,火口の硫黄採掘所全壊\n"
        "明治35年8月上旬(7日～9日のいつか),伊豆鳥島,125,全島民死亡。\n"
        "大正3年1月12日,桜島,58～59,噴火・地震による「大正大噴火」\n"
        "大正15年5月24日,十勝岳,144（不明を含む）,融雪型火山泥流による「大正泥流」\n"
        "昭和15年7月12日,三宅島,11,火山弾・溶岩流などによる\n"
        "昭和27年9月24日,ベヨネース列岩,31,海底噴火（明神礁）、観測船第5海洋丸遭難により全員殉職\n"
        "昭和33年6月24日,阿蘇山,12,噴石による\n"
        "平成3年6月3日,雲仙岳,43（不明を含む）,火砕流による「平成3年(1991年)雲仙岳噴火」\n"
        "平成26年9月27日,御嶽山,63（不明を含む）,噴石等による\n"
    )
    table = Table(data=data)
    table = table.convert(
        convertor="mtab_cta",
        params={"lines": 10},
    )

    with table.open() as reader:
        for lineno, row in enumerate(reader):
            assert len(row) == 4
            if lineno == 1:
                assert row[1].lower() in ("火山", "stratovolcano", "volcano")


def test_auto_mapping_cols():
    table = Table(sample_dir / "hachijo_sightseeing.csv")
    table = table.convert(
        convertor="auto_mapping_cols",
        params={
            "column_list": ["名称", "所在地", "経度", "緯度", "説明"],
            "keep_colname": True,
        }
    )

    with table.open(as_dict=True) as dictreader:
        for lineno, row in enumerate(dictreader):
            assert len(row) == 5
            if lineno == 0:
                # マッピングの結果を確認
                assert ",".join(row) == (
                    "名称 / 観光スポット名称,所在地,経度,緯度,説明")
            else:  # 経度列と緯度列が入れ替わっていることを確認
                assert float(row["緯度"]) > 25.0 and \
                    float(row["緯度"]) < 50.0
                assert float(row["経度"]) > 120.0 and \
                    float(row["経度"]) < 150.0

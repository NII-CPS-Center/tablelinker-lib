from logging import getLogger

from tablelinker import Table

logger = getLogger(__name__)


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)

    input_path = "sample/datafiles/2311.xlsx"  # 柳井市観光施設一覧
    output_path = "output.csv"

    table = Table(input_path)

    table = table.convert(
        convertor='geocoder_code',
        params={
            "input_col_idx": "住所",
            "output_col_name": "都道府県コード又は市区町村コード",
            "with_check_digit": False,
            "output_col_idx": 1,
        })
    table = table.convert(
        convertor='geocoder_latlong',
        params={
            "input_col_idx": "住所",
            "output_col_names": ["緯度", "経度", "ジオコーディングレベル"],
            "overwrite": False,
        })
    column_map = table.mapping_with_headers([  # 推奨データセット - 観光
        '都道府県コード又は市区町村コード', 'NO', '都道府県名',
        '市区町村名', '名称', '名称_カナ', '名称_英語',
        'POIコード', '住所', '方書', '緯度', '経度',
        '利用可能曜日', '開始時間', '終了時間', '利用可能日時特記事項',
        '料金（基本）', '料金（詳細）', '説明', '説明_英語',
        'アクセス方法', '駐車場情報', 'バリアフリー情報',
        '連絡先名称', '連絡先電話番号', '連絡先内線番号',
        '画像', '画像_ライセンス', 'URL', '備考',
    ])
    table = table.convert(
        convertor='mapping_cols',
        params={"column_map": column_map},
    )

    table.save(output_path, encoding="utf-8-sig")  # BOM 付き UTF-8

    # Pandas DataFrame を利用して JSON にエクスポート
    table.toPandas().to_json(
        "output.json", orient="records", indent=2, force_ascii=False)

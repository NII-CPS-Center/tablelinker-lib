from tablelinker.core import convertors, params


class MappingColsConvertor(convertors.Convertor):
    r"""
    概要
        既存の列名と新しい列名のマッピングテーブルを利用して、
        既存の表を新しい表に変換します。

    コンバータ名
        "mapping_cols"

    パラメータ
        * "column_map": 列名のマッピングテーブル [必須]

    注釈
        - マッピングテーブルの左側（キー）は出力される新しい列名、
          右側（値）は既存の表に含まれる列番号または列名です。
        - 既存の列名でマッピングテーブルに含まれないものは削除されます。
        - 新しい列名で対応する列名が null のもの新規に追加される列で、
          値は空（""）になります。


    サンプル
        「」（0列目）「人口」「出生数」「死亡数」…「婚姻件数」「離婚件数」のうち、
        「」「人口」「婚姻件数」「離婚件数」の列だけを選択し、
        「都道府県」「人口」「婚姻件数」「離婚件数」にマップします。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "mapping_cols",
                "params": {
                    "column_map": {
                        "都道府県": 0,
                        "人口": "人口",
                        "婚姻件数": "婚姻件数",
                        "離婚件数": "離婚件数"
                    }
                }
            }

        - コード例

        .. code-block:: python

            >>> # 「人口動態調査(2020年)上巻_3-3-1_都道府県（特別区－指定都市再掲）
            >>> # 別にみた人口動態総覧」（厚生労働省）より作成
            >>> # https://www.data.go.jp/data/dataset/mhlw_20211015_0019
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     ',人口,出生数,死亡数,（再掲）乳児死亡数,（再掲）新生児死亡数,自　然増減数,死産数総数,死産数自然死産,死産数人工死産,周産期死亡数総数,周産期死亡数22週以後の死産数,周産期死亡数早期新生児死亡数,婚姻件数,離婚件数\n'
            ...     '全　国,123398962,840835,1372755,1512,704,-531920,17278,8188,9090,2664,2112,552,525507,193253\n'
            ...     '01 北海道,5188441,29523,65078,59,25,-35555,728,304,424,92,75,17,20904,9070\n'
            ...     '02 青森県,1232227,6837,17905,18,15,-11068,145,87,58,32,17,15,4032,1915\n'
            ...     '03 岩手県,1203203,6718,17204,8,3,-10486,150,90,60,21,19,2,3918,1679\n'
            ...     '04 宮城県,2280203,14480,24632,27,15,-10152,311,141,170,56,41,15,8921,3553\n'
            ...     '05 秋田県,955659,4499,15379,9,4,-10880,98,63,35,18,15,3,2686,1213\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="mapping_cols",
            ...     params={
            ...         "column_map": {
            ...             "都道府県": 0,
            ...             "人口": "人口",
            ...             "婚姻件数": "婚姻件数",
            ...             "離婚件数": "離婚件数",
            ...         },
            ...     },
            ... )
            >>> table.write()
            都道府県,人口,婚姻件数,離婚件数
            全　国,123398962,525507,193253
            ...

    """  # noqa: E501

    class Meta:
        key = "mapping_cols"
        name = "カラムマッピング"
        description = "カラムを指定した通りにマッピングします"
        help_text = None

        params = params.ParamSet(
            params.DictParam(
                "column_map",
                label="カラムマップ",
                description="マッピング先のカラムをキー、元のカラムを値とする辞書",
                required=True),
        )

    def process_header(self, headers, context):
        column_map = context.get_param("column_map")
        self.mapping = []
        new_headers = []
        for output, header in column_map.items():
            if header is None:
                self.mapping.append(None)
                new_headers.append(output)
                continue

            if isinstance(header, str):
                try:
                    idx = headers.index(header)
                except ValueError:
                    raise RuntimeError((
                        "出力列 '{}' にマップされた列 '{}' は"
                        "有効な列名ではありません。有効な列名は次の通り; {}"
                    ).format(output, header, ",".join(headers)))

            elif isinstance(header, int):
                idx = header
            else:
                raise RuntimeError((
                    "出力列 '{}' にマップされた列 '{}' には"
                    "列名か位置を表す数字を指定してください。"
                ).format(output, header))

            self.mapping.append(idx)
            new_headers.append(output)

        context.output(new_headers)

    def process_record(self, record, context):
        context.output(self.reorder(record))

    def reorder(self, fields):
        new_fields = []
        for idx in self.mapping:
            if idx is None:
                new_fields.append('')
            else:
                new_fields.append(fields[idx])

        return new_fields

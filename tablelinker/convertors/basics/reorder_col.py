from tablelinker.core import convertors, params


class ReorderColsConvertor(convertors.Convertor):
    r"""
    概要
        指定した順番に列を並べ替えます。

    コンバータ名
        "reorder_cols"

    パラメータ
        * "column_list": 並び替えた列番号または列名のリスト [必須]

    注釈
        - ``column_list`` に指定した列が存在しない場合は
          `ValueError` を送出します。
        - ``column_list`` に指定されなかった列は削除されます。

    サンプル
        列を選択して並び替えます。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "reorder_cols",
                "params": {
                    "column_list": [
                        "施設名",
                        "所在地",
                        "経度",
                        "緯度"
                    ]
                }
            }

        - コード例

        .. code-block:: python

            >>> # 「八丈町営温泉一覧」より作成
            >>> # https://catalog.data.metro.tokyo.lg.jp/dataset/t134015d0000000001
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '施設名,所在地,緯度,経度,座標系,営業開始時間,営業終了時間\n'
            ...     '樫立向里温泉「ふれあいの湯」,東京都八丈島八丈町樫立1812?3,33.075843 ,139.790328 ,JGD2011,10:00,22:00\n'
            ...     '裏見ヶ滝温泉,東京都八丈島八丈町中之郷無番地,33.063743 ,139.816513 ,JGD2011,9:00,21:00\n'
            ...     'ブルーポート・スパ　ザ・BOON,東京都八丈島八丈町中之郷1448-1,33.060855 ,139.816199 ,JGD2011,10:00,21:00\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="reorder_cols",
            ...     params={
            ...         "column_list": ["施設名", "所在地", "経度", "緯度"],
            ...     },
            ... )
            >>> table.write()
            施設名,所在地,経度,緯度
            樫立向里温泉「ふれあいの湯」,東京都八丈島八丈町樫立1812?3,139.790328 ,33.075843 
            裏見ヶ滝温泉,東京都八丈島八丈町中之郷無番地,139.816513 ,33.063743 
            ...

    """  # noqa: E501, W291

    class Meta:
        key = "reorder_cols"
        name = "カラム並べ替え"
        description = "カラムを指定した順番に並べ替えます"
        help_text = None

        params = params.ParamSet(
            params.StringListParam(
                "column_list",
                label="カラムリスト",
                description="並べ替えた後のカラムのリスト",
                required=True),
        )

    def preproc(self, context):
        super().preproc(context)

        output_headers = context.get_param("column_list")
        missed_headers = []
        for idx in output_headers:
            if isinstance(idx, str) and idx not in self.headers:
                missed_headers.append(idx)
            elif isinstance(idx, int) and (
                    idx < 0 or idx >= len(self.headers)):
                missed_headers.append(str(idx))

        if len(missed_headers) > 0:
            if len(missed_headers) == 1:
                msg = "'{}' is ".format(missed_headers[0])
            else:
                msg = "'{}' are ".format(",".join(missed_headers))

            raise ValueError(
                "{} not in the original headers.".format(msg))

        self.mapping = []
        for idx in output_headers:
            if isinstance(idx, str):
                idx = self.headers.index(idx)
            self.mapping.append(idx)

    def process_header(self, headers, context):
        context.output(self.reorder(headers))

    def process_record(self, record, context):
        context.output(self.reorder(record))

    def reorder(self, fields):
        return [fields[idx] for idx in self.mapping]

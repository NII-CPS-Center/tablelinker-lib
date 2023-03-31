from tablelinker.core import convertors, params


class MoveColConvertor(convertors.Convertor):
    r"""
    概要
        列の位置を移動します。

    コンバータ名
        "move_col"

    パラメータ
        * "input_col_idx": 移動する列の列番号または列名 [必須]
        * "output_col_idx": 移動先の列番号または列名 [最後尾]

    注釈
        - 移動先の位置を列名で指定した場合、その列の直前に挿入します。
        - 移動する位置を省略した場合、最後尾に追加します。

    サンプル
        「経度」列を「緯度」列の前に移動します。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "move_col",
                "params": {
                    "input_col_idx": "経度",
                    "output_col_idx": "緯度"
                }
            }

        - コード例

        .. code-block:: python

            >>> # 「八丈町営温泉一覧」より作成
            >>> # https://catalog.data.metro.tokyo.lg.jp/dataset/t134015d0000000001
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '施設名,所在地,緯度,経度,座標系,営業開始時間,営業終了時間\n'
            ...     '樫立向里温泉「ふれあいの湯」,東京都八丈島八丈町樫立1812-3,33.075843 ,139.790328 ,JGD2011,10:00,22:00\n'
            ...     '裏見ヶ滝温泉,東京都八丈島八丈町中之郷無番地,33.063743 ,139.816513 ,JGD2011,9:00,21:00\n'
            ...     'ブルーポート・スパ　ザ・BOON,東京都八丈島八丈町中之郷1448-1,33.060855 ,139.816199 ,JGD2011,10:00,21:00\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="move_col",
            ...     params={
            ...         "input_col_idx": "経度",
            ...         "output_col_idx": "緯度",
            ...     },
            ... )
            >>> table.write()
            施設名,所在地,経度,緯度,座標系,営業開始時間,営業終了時間
            樫立向里温泉「ふれあいの湯」,東京都八丈島八丈町樫立1812-3,139.790328 ,33.075843 ,JGD2011,10:00,22:00
            裏見ヶ滝温泉,東京都八丈島八丈町中之郷無番地,139.816513 ,33.063743 ,JGD2011,9:00,21:00
            ブルーポート・スパ　ザ・BOON,東京都八丈島八丈町中之郷1448-1,139.816199 ,33.060855 ,JGD2011,10:00,21:00

    """  # noqa: E501

    class Meta:
        key = "move_col"
        name = "列移動"
        description = "列を指定した位置に移動します"
        help_text = None

        params = params.ParamSet(
            params.InputAttributeParam(
                "input_col_idx",
                label="移動する列",
                description="処理をする対象の列",
                required=True),
            params.OutputAttributeParam(
                "output_col_idx",
                label="移動する列の移動先の位置",
                description="新しく列の挿入位置です。",
                label_suffix="の後",
                empty=True,
                empty_label="先頭",
                required=False,
            ),
        )

    def preproc(self, context):
        super().preproc(context)
        self.input_col_idx = context.get_param("input_col_idx")
        self.output_col_idx = context.get_param("output_col_idx") or \
            len(self.headers)
        if self.output_col_idx > self.input_col_idx:
            self.output_col_idx -= 1

    def process_header(self, headers, context):
        headers = self.move_list(
            self.input_col_idx, self.output_col_idx, headers)
        context.output(headers)

    def process_record(self, record, context):
        record = self.move_list(
            self.input_col_idx, self.output_col_idx, record)
        context.output(record)

    def move_list(self, input_col_idx, output_col_idx, target_list):
        col = target_list.pop(input_col_idx)
        target_list.insert(output_col_idx, col)
        return target_list

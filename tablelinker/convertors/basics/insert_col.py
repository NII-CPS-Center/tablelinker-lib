from logging import getLogger

from tablelinker.core import convertors, params

logger = getLogger(__name__)


class InsertColConvertor(convertors.Convertor):
    r"""
    概要
        新しい列を追加します。

    コンバータ名
        "insert_col"

    パラメータ
        * "output_col_idx": 新しい列を追加する列番号または列名 [最後尾]
        * "output_col_name": 追加する列名 [必須]
        * "value": 追加した列にセットする値 [""]

    注釈
        - 出力列名が元の表に存在していても同じ名前の列を追加します。
        - 追加する位置を既存の列名で指定した場合、その列の直前に
          新しい列を挿入します。
        - 追加する位置を省略した場合、最後尾に追加します。

    サンプル
        「所在地」列の前に「都道府県名」列を挿入し、その列の
        すべての値を「東京都」にセットします。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "insert_col",
                "params": {
                    "output_col_idx": "所在地",
                    "output_col_name": "都道府県名",
                    "value": "東京都"
                }
            }

        - コード例

        .. code-block:: python

            >>> # 「東京都災害拠点病院一覧」（東京都福祉局）より作成（令和4年1月1日現在）
            >>> # https://www.fukushihoken.metro.tokyo.lg.jp/iryo/kyuukyuu/saigai/kyotenbyouinlist.html
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...    '施設名,所在地,電話番号,病床数\n'
            ...    '日本大学病院,千代田区神田駿河台1-6,03－3293－1711,320\n'
            ...    '三井記念病院,千代田区神田和泉町１,03－3862－9111,482\n'
            ...    '聖路加国際病院,中央区明石町9-1,03－3541－5151,520\n'
            ...    '東京都済生会中央病院,港区三田1－4－17,03－3451－8211,535\n'
            ...    '東京慈恵会医科大学附属病院,港区西新橋3-19-18,03－3433－1111,"1,075"\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="insert_col",
            ...     params={
            ...         "output_col_idx": "所在地",
            ...         "output_col_name": "都道府県名",
            ...         "value": "東京都",
            ...     },
            ... )
            >>> table.write()
            施設名,都道府県名,所在地,電話番号,病床数
            日本大学病院,東京都,千代田区神田駿河台1-6,03－3293－1711,320
            三井記念病院,東京都,千代田区神田和泉町１,03－3862－9111,482
            ...

    """  # noqa: E501

    class Meta:
        key = "insert_col"
        name = "新規列追加"

        description = """
        新規列を指定した場所に追加します。
        """

        message = "{new_name}を追加しました。"

        help_text = None

        params = params.ParamSet(
            params.StringParam(
                "output_col_name",
                label="出力列名",
                description="新しく追加する列名です。",
                help_text="既存の名前が指定された場合も同じ名前の列が追加されます。",
                required=True,
            ),
            params.OutputAttributeParam(
                "output_col_idx",
                label="出力列の位置",
                description="新しい列の挿入位置です。",
                label_suffix="の後",
                empty=True,
                empty_label="先頭",
                required=False,
            ),
            params.StringParam(
                "value",
                label="新しい値",
                required=False,
                default_value="",
            ),
        )

    def preproc(self, context):
        super().preproc(context)
        self.output_col_name = context.get_param("output_col_name")
        self.output_col_idx = context.get_param("output_col_idx")
        self.value = context.get_param("value")
        if self.output_col_idx is None:
            self.output_col_idx = len(self.headers)

    def process_header(self, headers, context):
        headers.insert(self.output_col_idx, self.output_col_name)
        context.output(headers)

    def process_record(self, record, context):
        record.insert(self.output_col_idx, self.value)
        context.output(record)


class InsertColsConvertor(convertors.Convertor):
    r"""
    概要
        新しい複数の列を追加します。

    コンバータ名
        "insert_cols"

    パラメータ
        * "output_col_idx": 新しい列を追加する列番号または列名 [最後尾]
        * "output_col_names": 追加する列名のリスト [必須]
        * "values": 追加した列にセットする値のリスト [""]

    注釈
        - 出力列名が元の表に存在していても同じ名前の列を追加します。
        - 追加する位置を既存の列名で指定した場合、その列の直前に
          新しい列を挿入します。
        - 追加する位置を省略した場合、最後尾に追加します。
        - ``values`` に単一の値を指定した場合はすべての列にその値をセットします。
        - ``values`` にリストを指定する場合、追加する列数と
          長さが同じである必要があります。

    サンプル
        「所在地」列の前に「都道府県名」「市区町村名」列を挿入し、
        その列のすべての値を「東京都」「八丈町」にセットします。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "insert_cols",
                "params": {
                    "output_col_idx": "所在地",
                    "output_col_names": ["都道府県名", "市区町村名"],
                    "values": ["東京都", "八丈町"]
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
            ...     convertor="insert_cols",
            ...     params={
            ...         "output_col_idx": "所在地",
            ...         "output_col_names": ["都道府県名", "市区町村名"],
            ...         "values": ["東京都", "八丈町"],
            ...     },
            ... )
            >>> table.write()
            施設名,都道府県名,市区町村名,所在地,緯度,経度,座標系,営業開始時間,営業終了時間
            樫立向里温泉「ふれあいの湯」,東京都,八丈町,東京都八丈島八丈町樫立1812?3,33.075843 ,139.790328 ,JGD2011,10:00,22:00
            裏見ヶ滝温泉,東京都,八丈町,東京都八丈島八丈町中之郷無番地,33.063743 ,139.816513 ,JGD2011,9:00,21:00
            ...

    """  # noqa: E501

    class Meta:
        key = "insert_cols"
        name = "新規列追加（複数）"

        description = """
        新規列を複数指定した場所に追加します。
        """

        help_text = None

        params = params.ParamSet(
            params.OutputAttributeParam(
                "output_col_idx",
                label="新規列を追加する位置",
                description="新規列の挿入位置です。",
                required=False,
            ),
            params.StringListParam(
                "output_col_names",
                label="新しい列名のリスト",
                required=True
            ),
            params.StringListParam(
                "values",
                label="新しい列にセットする値のリスト",
                required=False,
                default_value=""
            ),
        )

    def preproc(self, context):
        super().preproc(context)
        self.output_col_idx = context.get_param("output_col_idx")
        self.new_names = context.get_param("output_col_names")
        self.new_values = context.get_param("values")

        if isinstance(self.new_values, str):
            self.new_values = [self.new_values] * len(self.new_names)
        elif len(self.new_values) != len(self.new_names):
            logger.error("追加する列数と、値の列数が一致しません。")
            raise ValueError((
                "The length of 'values' must be equal to "
                "the length of 'output_col_names'."))

    def process_header(self, headers, context):
        if self.output_col_idx is None:
            self.output_col_idx = len(headers)

        headers = self.insert_list(
            self.output_col_idx, self.new_names, headers)
        context.output(headers)

    def process_record(self, record, context):
        record = self.insert_list(
            self.output_col_idx, self.new_values, record)
        context.output(record)

    def insert_list(self, output_col_idx, value_list, target_list):
        new_list = target_list[0:output_col_idx] + value_list \
            + target_list[output_col_idx:]
        return new_list

import re

from tablelinker.core import convertors, params


class SplitColConvertor(convertors.Convertor):
    r"""
    概要
        指定した列を区切り文字で複数列に分割します。

    コンバータ名
        "split_col"

    パラメータ
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_names": 分割した結果を出力する列名のリスト [必須]
        * "output_col_idx": 出力列の直後にくる列名、または列番号 [最後尾]
        * "separator": 区切り文字（正規表現） [","]

    注釈
        - 分割した列の数が ``output_col_names`` よりも少ない場合は
          足りない列の値が "" になります。
        - 分割した列の数が ``output_col_names`` よりも多い場合は
          最後の列に残りのすべての文字列が出力されます。

    サンプル
        「姓名」列を空白で区切り、「姓」列と「名」列に分割し、
        「生年月日」列の前に出力します。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "split_col",
                "params": {
                    "input_col_idx": "姓名",
                    "output_col_names": ["姓", "名"],
                    "output_col_idx": "生年月日",
                    "separator": " "
                }
            }

        - コード例

        .. code-block:: python

            >>> # データはランダム生成
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '"姓名","生年月日","性別"\n'
            ...     '"生田 直樹","1930年08月11日","男"\n'
            ...     '"石橋 絵理","1936年01月28日","女"\n'
            ...     '"菊池 浩二","1985年12月17日","男"\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="split_col",
            ...     params={
            ...         "input_col_idx": "姓名",
            ...         "output_col_names": ["姓", "名"],
            ...         "output_col_idx": "生年月日",
            ...         "separator": " ",
            ...     },
            ... )
            >>> table.write()
            姓名,姓,名,生年月日,性別
            生田 直樹,生田,直樹,1930年08月11日,男
            石橋 絵理,石橋,絵理,1936年01月28日,女
            菊池 浩二,菊池,浩二,1985年12月17日,男

    """

    class Meta:
        key = "split_col"
        name = "列の分割"
        description = """
        列を指定された文字列で分割して、複数の列を生成します
        """
        help_text = """
        生成した列は、最後尾に追加されます。
        """

        params = params.ParamSet(
            params.InputAttributeParam(
                "input_col_idx",
                label="入力列",
                description="処理をする対象の列を選択してください。",
                required=True),
            params.StringListParam(
                "output_col_names",
                label="分割後に出力する列名のリスト",
                description="変換結果を出力する列名です。",
                required=True,
            ),
            params.OutputAttributeParam(
                "output_col_idx",
                label="分割後に出力する列の位置",
                description="列を出力する列の位置、または直後にくる列名です。",
                required=False,
            ),
            params.StringParam(
                "separator",
                label="区切り文字",
                default_value=",",
                required=True,
                description="文字列を分割する区切り文字を指定します。",
                help_text="「東京都,千葉県」の場合は、「,」になります。",
            ),
        )

    def preproc(self, context):
        super().preproc(context)
        self.re_separator = re.compile(context.get_param("separator"))
        self.input_col_idx = context.get_param("input_col_idx")
        self.output_col_names = context.get_param("output_col_names")
        self.output_col_idx = context.get_param("output_col_idx")

    def process_header(self, headers, context):
        headers = headers[0:self.output_col_idx] + self.output_col_names \
            + headers[self.output_col_idx:]
        context.output(headers)

    def process_record(self, record, context):
        original = record[self.input_col_idx]
        splits = self.re_separator.split(
            original, maxsplit=len(self.output_col_names) - 1)
        record = record[0:self.output_col_idx] + splits \
            + record[self.output_col_idx:]
        context.output(record)


class SplitRowConvertor(convertors.Convertor):
    r"""
    概要
        指定した列を区切り文字で複数行に分割します。

    コンバータ名
        "split_row"

    パラメータ
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "separator": 区切り文字（正規表現） [","]

    注釈
        - 分割前の行は削除されます。
        - 区切り文字が末尾の場合、対象列が空欄の行も出力されます。

    サンプル
        「診療科目」列を「;」で区切り、複数行に分割します。

        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "split_row",
                "params": {
                    "input_col_idx": "診療科目",
                    "separator": ";"
                }
            }

        - コード例

        .. code-block:: python

            >>> #「札幌市内の医療機関一覧」より作成
            >>> # https://ckan.pf-sapporo.jp/dataset/sapporo_hospital
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '名称,診療科目\n'
            ...     '特定医療法人平成会平成会病院,外;リハ;放;形;麻;消内;呼内\n'
            ...     '時計台記念病院,内;循内;消内;糖尿病内科;整;リハ;形;婦;脳外;眼;精;麻;放;リウ;外;緩和ケア内科;血管外科;腎臓内科;泌\n'
            ...     'JR札幌病院,内;精;小;外;整;皮;泌;肛門外科;産婦;眼;耳;放;歯外;麻;リウ;呼内;呼吸器外科;循内;血管外科;消内;腎臓内科;乳腺外科;病理診断科;糖尿病内科\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="split_row",
            ...     params={
            ...         "input_col_idx": "診療科目",
            ...         "separator": ";",
            ...     },
            ... )
            >>> table.write()
            名称,診療科目
            特定医療法人平成会平成会病院,外
            特定医療法人平成会平成会病院,リハ
            特定医療法人平成会平成会病院,放
            特定医療法人平成会平成会病院,形
            特定医療法人平成会平成会病院,麻
            特定医療法人平成会平成会病院,消内
            特定医療法人平成会平成会病院,呼内
            時計台記念病院,内
            時計台記念病院,循内
            時計台記念病院,消内
            時計台記念病院,糖尿病内科
            時計台記念病院,整
            時計台記念病院,リハ
            時計台記念病院,形
            時計台記念病院,婦
            時計台記念病院,脳外
            時計台記念病院,眼
            時計台記念病院,精
            時計台記念病院,麻
            時計台記念病院,放
            時計台記念病院,リウ
            時計台記念病院,外
            時計台記念病院,緩和ケア内科
            時計台記念病院,血管外科
            時計台記念病院,腎臓内科
            時計台記念病院,泌
            JR札幌病院,内
            JR札幌病院,精
            JR札幌病院,小
            JR札幌病院,外
            JR札幌病院,整
            JR札幌病院,皮
            JR札幌病院,泌
            JR札幌病院,肛門外科
            JR札幌病院,産婦
            JR札幌病院,眼
            JR札幌病院,耳
            JR札幌病院,放
            JR札幌病院,歯外
            JR札幌病院,麻
            JR札幌病院,リウ
            JR札幌病院,呼内
            JR札幌病院,呼吸器外科
            JR札幌病院,循内
            JR札幌病院,血管外科
            JR札幌病院,消内
            JR札幌病院,腎臓内科
            JR札幌病院,乳腺外科
            JR札幌病院,病理診断科
            JR札幌病院,糖尿病内科

    """  # noqa: E501

    class Meta:
        key = "split_row"
        name = "列を分割して行に展開"
        description = """
        列を指定された文字列で分割して、複数の行を生成します。
        """
        help_text = None

        params = params.ParamSet(
            params.InputAttributeParam(
                "input_col_idx",
                label="入力列",
                description="処理をする対象の列",
                required=True
            ),
            params.StringParam(
                "separator",
                label="区切り文字",
                required=True,
                default_value=","
            ),
        )

    def preproc(self, context):
        super().preproc(context)
        self.re_separator = re.compile(context.get_param("separator"))
        self.input_col_idx = context.get_param("input_col_idx")

    def process_record(self, record, context):
        splits = self.re_separator.split(record[self.input_col_idx])

        for value in splits:
            new_record = record[:]  # 元のレコードを複製
            new_record[self.input_col_idx] = value
            context.output(new_record)

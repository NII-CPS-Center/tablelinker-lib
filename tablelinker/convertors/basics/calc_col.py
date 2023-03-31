from enum import Enum

from tablelinker.core import convertors, params


class Calculation(Enum):
    Add = "+"
    Sub = "-"
    Mul = "*"
    Div = "/"


CalculationLabels = {
    Calculation.Add: "和",
    Calculation.Sub: "差",
    Calculation.Mul: "積",
    Calculation.Div: "商",
}


def calc(valueA, valueB, calculation):
    """文字列を結合します。
    valueA: 数値A
    valueB: 数値B
    separator: 区切り文字
    """
    valueA = params.Param.eval_number(valueA)
    valueB = params.Param.eval_number(valueB)

    if calculation == Calculation.Add:
        return valueA + valueB
    elif calculation == Calculation.Sub:
        return valueA - valueB
    elif calculation == Calculation.Mul:
        return valueA * valueB
    elif calculation == Calculation.Div:
        return valueA / valueB
    else:
        raise "Unknown Calculation"


class CalcColConvertor(convertors.Convertor):
    r"""
    概要
        2つの入力列に対して四則演算を実行し、結果を出力列に保存します。

    コンバータ名
        "calc"

    パラメータ
        * "input_col_idx1": 入力列1の列番号または列名 [必須]
        * "input_col_idx2": 入力列2の列番号または列名 [必須]
        * "output_col_name": 出力列名 [必須]
        * "operator": 演算子（"+", "-", "*", "/"） ["*"]
        * "delete_col": 入力列を削除するか （true/false） [false]

    注釈
        - 出力列名が元の表に存在している場合、その列に上書きします。
        - 存在していなかった場合、最後に新しい列が追加されます。

    サンプル
        表の「人口」列の値を「面積」列の値で割った商を「人口密度」列に
        出力します。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "calc",
                "params": {
                    "input_col_idx1": "人口",
                    "input_col_idx2": "面積",
                    "operator": "/",
                    "output_col_name": "人口密度",
                    "delete_col": false
                }
            }

        - コード例

        .. code-block:: python

            >>> # 「国勢調査（令和２）都道府県・市区町村別の主な結果」
            >>> # https://www.e-stat.go.jp/stat-search/files?layout=datalist&cycle=0&toukei=00200521&tstat=000001049104&tclass1=000001049105&tclass2val=0&stat_infid=000032143614
            >>> # および「これまでに公表した面積調／令和4年10月1日」（国土地理院）より作成
            >>> # https://www.gsi.go.jp/KOKUJYOHO/OLD-MENCHO-title.htm
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '都道府県名,人口,面積\n'
            ...     '北海道 ほっかいどう,"5,224,614","83423.81"\n'
            ...     '青森県 あおもりけん,"1,237,984","9645.95"\n'
            ...     '岩手県 いわてけん,"1,210,534","15275.01"\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="calc",
            ...     params={
            ...         "input_col_idx1": "人口",
            ...         "input_col_idx2": "面積",
            ...         "operator": "/",
            ...         "output_col_name": "人口密度",
            ...         "delete_col": False,
            ...     },
            ... )
            >>> table.write()
            都道府県名,人口,面積,人口密度
            北海道 ほっかいどう,"5,224,614",83423.81,62.6273...
            青森県 あおもりけん,"1,237,984",9645.95,128.3423...
            岩手県 いわてけん,"1,210,534",15275.01,79.2493...

    """  # noqa: E501

    class Meta:
        key = "calc"
        name = "列演算"

        description = """
        ２つの列を四則演算します。
        """

        help_text = None

        #
        params = params.ParamSet(
            params.InputAttributeParam(
                "input_col_idx1",
                label="対象列1",
                required=True
            ),
            params.InputAttributeParam(
                "input_col_idx2",
                label="対象列2",
                required=True
            ),
            params.StringParam(
                "output_col_name",
                label="新しい列名"
            ),
            params.EnumsParam(
                "operator",
                label="演算子",
                enums=Calculation,
                labels=CalculationLabels,
                default_value=Calculation.Add
            ),
            params.BooleanParam(
                "delete_col",
                label="元の列を消しますか？",
                default_value=False
            ),
        )

    def preproc(self, context):
        super().preproc(context)

        self.attr1 = context.get_param("input_col_idx1")
        self.attr2 = context.get_param("input_col_idx2")
        self.output_col_name = context.get_param("output_col_name")
        self.delete_col = context.get_param("delete_col")
        self.operator = context.get_param("operator")

        if self.output_col_name is None:
            self.output_col_name = "+".join([
                self.headers[self.attr1],
                self.headers[self.attr2]])

    def process_header(self, headers, context):
        if self.delete_col:
            headers.pop(self.attr1)
            if self.attr1 != self.attr2:
                headers.pop(self.attr2 - 1)

        headers = headers + [self.output_col_name]

        context.output(headers)

    def process_record(self, record, context):
        try:
            valueA = record[self.attr1]
            valueB = record[self.attr2]
            calc_value = calc(valueA, valueB, self.operator)
            record.append(calc_value)
        except ValueError:
            record.append(None)

        if self.delete_col:
            record.pop(self.attr1)
            if self.attr1 != self.attr2:
                record.pop(self.attr2)

        context.output(record)

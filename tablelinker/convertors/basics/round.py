from tablelinker.core import convertors, params, validators


class RoundConvertor(convertors.InputOutputConvertor):
    r"""
    概要
        指定した列の数値を丸めます。

    コンバータ名
        "round"

    パラメータ（InputOutputConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_idx": 分割した結果を出力する列番号または
          列名のリスト
        * "output_col_name": 結果を出力する列名
        * "overwrite": 既に値がある場合に上書きするかどうか [True]

    パラメータ（コンバータ固有）
        * "ndigits": 小数部の桁数。0を指定すると整数を返します。 [0]

    注釈（InputOutputConvertor 共通）
        - ``output_col_name`` が省略された場合、
          ``input_col_idx`` 列の列名が出力列名として利用されます。
        - ``output_col_idx`` が省略された場合、
          出力列名が存在する列名ならばその列の位置に出力し、
          存在しないならば最後尾に追加します。

    注釈
        - 丸め処理は列名には適用されません。
        - 数値と解釈できない行には適用されません。

    サンプル
        「人口密度」列を小数点以下3桁で丸めます。

        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "round",
                "params": {
                    "input_col_idx": "人口密度",
                    "ndigits": 3,
                    "overwrite": true
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
            ...     '都道府県名,人口,面積,人口密度\n'
            ...     '北海道 ほっかいどう,"5,224,614",83423.81,62.627372209444765\n'
            ...     '青森県 あおもりけん,"1,237,984",9645.95,128.34236130189353\n'
            ...     '岩手県 いわてけん,"1,210,534",15275.01,79.2493098204191\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="round",
            ...     params={
            ...         "input_col_idx": "人口密度",
            ...         "ndigits": 3,
            ...         "overwrite": True,
            ...     },
            ... )
            >>> table.write()
            都道府県名,人口,面積,人口密度
            北海道 ほっかいどう,"5,224,614",83423.81,62.627
            青森県 あおもりけん,"1,237,984",9645.95,128.342
            岩手県 いわてけん,"1,210,534",15275.01,79.249

    """  # noqa: E501

    class Meta:
        key = "round"
        name = "数値を丸める"
        description = "数値の小数部を指定した桁数で丸めます"
        help_text = None
        params = params.ParamSet(
            params.IntParam(
                "ndigits",
                label="小数部の桁数",
                required=False,
                validators=(
                    validators.IntValidator(),
                    validators.RangeValidator(min=0, max=10),
                ),
                default_value=0,
            ),
        )

    def preproc(self, context):
        super().preproc(context)
        self.ndigits = context.get_param("ndigits")

    def process_convertor(self, record, context):
        value = record[self.input_col_idx]
        try:
            float_val = params.Param.eval_number(value)
        except ValueError:
            # 数値ではない場合はそのまま
            return value

        if self.ndigits <= 0:
            value = round(float_val)
        else:
            value = round(float_val, self.ndigits)

        return value

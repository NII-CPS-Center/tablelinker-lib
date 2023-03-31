from tablelinker.core import convertors, params, validators


class TruncateConvertor(convertors.InputOutputConvertor):
    r"""
    概要
        指定した列を指定文字数まで切り詰めます。

    コンバータ名
        "truncate"

    パラメータ（InputOutputConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_idx": 分割した結果を出力する列番号または
          列名のリスト
        * "output_col_name": 結果を出力する列名
        * "overwrite": 既に値がある場合に上書きするかどうか [True]

    パラメータ（コンバータ固有）
        * "length": 最大文字数 [10]
        * "ellipsis": 切り詰めた場合に追加される記号 ["…"]

    注釈（InputOutputConvertor 共通）
        - ``output_col_name`` が省略された場合、
          ``input_col_idx`` 列の列名が出力列名として利用されます。
        - ``output_col_idx`` が省略された場合、
          出力列名が存在する列名ならばその列の位置に出力し、
          存在しないならば最後尾に追加します。

    注釈
        - 切り詰め処理は列名には適用されません。
        - もともとの文字数が ``length`` 以下の場合は
          ``ellipsis`` は追加されません。

    サンプル
        「説明」列を 40 文字で切り詰めます。


        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "truncate",
                "params": {
                    "input_col_idx": "説明",
                    "length": 20,
                    "ellipsis": "...",
                    "overwrite": true
                }
            }

        - コード例

        .. code-block:: python

            >>> # 「八丈島の主な観光スポット一覧」より作成
            >>> # https://catalog.data.metro.tokyo.lg.jp/dataset/t134015d0000000002
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '観光スポット名称,説明\n'
            ...     'ホタル水路,八丈島は伊豆諸島で唯一、水田耕作がなされた島で鴨川に沿って水田が残っています。ホタル水路は、鴨川の砂防とともに平成元年につくられたもので、毎年6月から7月にかけてホタルの光が美しく幻想的です。\n'
            ...     '登龍峠展望,「ノボリュウトウゲ」または「ノボリョウトウゲ」といい、この道を下方から望むとあたかも龍が昇天するように見えるので、この名が付けられました。峠道の頂上近くの展望台は、八丈島で一、二を争う景勝地として名高く、新東京百景の一つにも選ばれました。眼前に八丈富士と神止山、八丈小島を、眼下には底土港や神湊港、三根市街を一望できます。\n'
            ...     '八丈富士,八丈島の北西部を占める山で、東の三原山に対して『西山』と呼ばれます。伊豆諸島の中では最も高い標高854.3メートル。1605年の噴火後、活動を停止している火山で火口は直径400メートル深さ50メートルで、 さらに火口底には中央火口丘がある二重式火山です。裾野が大きくのびた優雅な姿は、八丈島を代表する美しさのひとつです。\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="truncate",
            ...     params={
            ...         "input_col_idx": "説明",
            ...         "length": 20,
            ...         "ellipsis": "...",
            ...         "overwrite": True,
            ...     },
            ... )
            >>> table.write()
            観光スポット名称,説明
            ホタル水路,八丈島は伊豆諸島で唯一、水田耕作がなされ...
            登龍峠展望,「ノボリュウトウゲ」または「ノボリョウト...
            八丈富士,八丈島の北西部を占める山で、東の三原山に...

    """  # noqa: E501

    class Meta:
        key = "truncate"
        name = "文字列を切り詰める"
        description = "文字列を指定された文字数で切り取ります"
        help_text = None
        params = params.ParamSet(
            params.IntParam(
                "length",
                label="最大文字列長",
                required=True,
                validators=(
                    validators.IntValidator(),
                    validators.RangeValidator(min=1),),
                default_value="10",
            ),
            params.StringParam(
                "ellipsis",
                label="省略記号",
                default_value="…"
            ),
        )

    def preproc(self, context):
        super().preproc(context)
        self.length = context.get_param("length")
        self.ellipsis = context.get_param("ellipsis")

    def process_convertor(self, record, context):
        value = record[self.input_col_idx]
        if len(value) > self.length:
            value = value[:self.length] + self.ellipsis

        return value

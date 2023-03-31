from logging import getLogger

import jaconv

from tablelinker.core import convertors, params

logger = getLogger(__name__)


class ToHankakuConvertor(convertors.InputOutputConvertor):
    r"""
    概要
        全角文字を半角文字に変換します。

    コンバータ名
        "to_hankaku"

    パラメータ（InputOutputConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_idx": 変換した結果を出力する列番号または
          列名のリスト
        * "output_col_name": 結果を出力する列名
        * "overwrite": 既に値がある場合に上書きするかどうか [True]

    パラメータ（コンバータ固有）
        * "kana": カナ文字を変換対象に含める [True]
        * "ascii": アルファベットと記号を対象に含める [True]
        * "digit": 数字を対象に含める [True]
        * "ignore_chars": 対象に含めない文字 [""]

    注釈（InputOutputConvertor 共通）
        - ``output_col_name`` が省略された場合、
          ``input_col_idx`` 列の列名が出力列名として利用されます。
        - ``output_col_idx`` が省略された場合、
          出力列名が存在する列名ならばその列の位置に出力し、
          存在しないならば最後尾に追加します。

    注釈
        - 変換処理は列名には適用されません。

    サンプル
        「連絡先電話番号」列に含まれる全角数字と記号を半角に置き換えます。

        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "to_hankaku",
                "params": {
                    "input_col_idx": "電話番号",
                    "output_col_idx": "電話番号",
                    "kana": false,
                    "ascii": true,
                    "digit": true,
                    "overwrite": true
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
            ...     convertor="to_hankaku",
            ...     params={
            ...         "input_col_idx": "電話番号",
            ...         "output_col_idx": "電話番号",
            ...         "kana": False,
            ...         "ascii": True,
            ...         "digit": True,
            ...         "overwrite": True,
            ...     },
            ... )
            >>> table.write()
            施設名,所在地,電話番号,病床数
            日本大学病院,千代田区神田駿河台1-6,03-3293-1711,320
            三井記念病院,千代田区神田和泉町１,03-3862-9111,482
            聖路加国際病院,中央区明石町9-1,03-3541-5151,520
            東京都済生会中央病院,港区三田1－4－17,03-3451-8211,535
            東京慈恵会医科大学附属病院,港区西新橋3-19-18,03-3433-1111,"1,075"

    """  # noqa: E501

    class Meta:
        key = "to_hankaku"
        name = "全角→半角変換"
        description = """
          全角文字を半角文字に変換します
          """
        help_text = None
        params = params.ParamSet(
            params.BooleanParam(
                "kana",
                label="カナ文字を対象に含める",
                required=False,
                default_value=True,
            ),
            params.BooleanParam(
                "ascii",
                label="アルファベットと記号を対象に含める",
                required=False,
                default_value=True,
            ),
            params.BooleanParam(
                "digit",
                label="数字を対象に含める",
                required=False,
                default_value=True,
            ),
            params.StringParam(
                "ignore_chars",
                label="対象に含めない文字",
                required=False,
                default_value="",
            ),
        )

    def preproc(self, context):
        super().preproc(context)
        self.kana = context.get_param("kana")
        self.ascii = context.get_param("ascii")
        self.digit = context.get_param("digit")
        self.ignore_chars = context.get_param("ignore_chars")

    def process_convertor(self, record, context):
        return jaconv.z2h(
            record[self.input_col_idx],
            kana=self.kana,
            ascii=self.ascii,
            digit=self.digit,
            ignore=self.ignore_chars)


class ToZenkakuConvertor(convertors.InputOutputConvertor):
    r"""
    概要
        半角文字を全角文字に変換します。

    コンバータ名
        "to_zenkaku"

    パラメータ（InputOutputConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_idx": 分割した結果を出力する列番号または
          列名のリスト
        * "output_col_name": 結果を出力する列名
        * "overwrite": 既に値がある場合に上書きするかどうか [False]

    パラメータ（コンバータ固有）
        * "kana": カナ文字を変換対象に含める [True]
        * "ascii": アルファベットと記号を対象に含める [True]
        * "digit": 数字を対象に含める [True]
        * "ignore_chars": 対象に含めない文字 [""]

    注釈（InputOutputConvertor 共通）
        - ``output_col_name`` が省略された場合、
          ``input_col_idx`` 列の列名が出力列名として利用されます。
        - ``output_col_idx`` が省略された場合、
          出力列名が存在する列名ならばその列の位置に出力し、
          存在しないならば最後尾に追加します。

    注釈
        - 変換処理は列名には適用されません。

    サンプル
        「所在地」列に含まれる半角文字を全角文字に置き換えます。

        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "to_zenkaku",
                "params": {
                    "input_col_idx": "住所",
                    "output_col_idx": "住所",
                    "kana": true,
                    "ascii": true,
                    "digit": true,
                    "overwrite": true
                }
            }

        - コード例

        .. code-block:: python

            >>> #「札幌市内の医療機関一覧」より作成
            >>> # https://ckan.pf-sapporo.jp/dataset/sapporo_hospital
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     'ＮＯ,名称,住所\n'
            ...     '101100302,特定医療法人平成会平成会病院,北海道札幌市中央区北1条西18丁目1番1\n'
            ...     '101010421,時計台記念病院,北海道札幌市中央区北1条東1丁目2番地3\n'
            ...     '101010014,JR札幌病院,北海道札幌市中央区北3条東1丁目1番地\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="to_zenkaku",
            ...     params={
            ...         "input_col_idx": "住所",
            ...         "output_col_idx": "住所",
            ...         "kana": True,
            ...         "ascii": True,
            ...         "digit": True,
            ...         "overwrite": True,
            ...     },
            ... )
            >>> table.write()
            ＮＯ,名称,住所
            101100302,特定医療法人平成会平成会病院,北海道札幌市中央区北１条西１８丁目１番１
            101010421,時計台記念病院,北海道札幌市中央区北１条東１丁目２番地３
            101010014,JR札幌病院,北海道札幌市中央区北３条東１丁目１番地

    """

    class Meta:
        key = "to_zenkaku"
        name = "半角→全角変換"
        description = "半角文字を全角文字に変換します"
        help_text = None
        params = params.ParamSet(
            params.BooleanParam(
                "kana",
                label="カナ文字を対象に含める",
                required=False,
                default_value=True,
            ),
            params.BooleanParam(
                "ascii",
                label="アルファベットと記号を対象に含める",
                required=False,
                default_value=True,
            ),
            params.BooleanParam(
                "digit",
                label="数字を対象に含める",
                required=False,
                default_value=True,
            ),
            params.StringParam(
                "ignore_chars",
                label="対象に含めない文字",
                required=False,
                default_value="",
            ),
        )

    def preproc(self, context):
        super().preproc(context)
        self.kana = context.get_param("kana")
        self.ascii = context.get_param("ascii")
        self.digit = context.get_param("digit")
        self.ignore_chars = context.get_param("ignore_chars")

    def process_convertor(self, record, context):
        return jaconv.h2z(
            record[self.input_col_idx],
            kana=self.kana,
            ascii=self.ascii,
            digit=self.digit,
            ignore=self.ignore_chars)

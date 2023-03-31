import re

from tablelinker.core import convertors, params


class UpdateColConvertor(convertors.Convertor):
    r"""
    概要
        指定した列の値を新しい文字列に置き換えます。

    コンバータ名
        "update_col"

    パラメータ
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "new": 置き換える文字列 [必須]

    サンプル
        「性別」列を「－」に置き換えます。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "update_col",
                "params": {
                    "input_col_idx": "性別",
                    "new": "－"
                }
            }

        - コード例

        .. code-block:: python

            >>> # データはランダム生成
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '"氏名","生年月日","性別","クレジットカード"\n'
            ...     '"小室 友子","1990年06月20日","女","3562635454918233"\n'
            ...     '"江島 佳洋","1992年10月07日","男","376001629316609"\n'
            ...     '"三沢 大志","1995年02月13日","男","4173077927458449"\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="update_col",
            ...     params={
            ...         "input_col_idx": "性別",
            ...         "new": "－",
            ...     },
            ... )
            >>> table.write()
            氏名,生年月日,性別,クレジットカード
            小室 友子,1990年06月20日,－,3562635454918233
            江島 佳洋,1992年10月07日,－,376001629316609
            三沢 大志,1995年02月13日,－,4173077927458449

    """

    class Meta:
        key = "update_col"
        name = "列の値を変更（無条件）"
        description = """
        指定された列の値を変更します
        """
        help_text = """
        「対象列」の値を「新しい文字列」に変更します。
        """

        params = params.ParamSet(
            params.InputAttributeParam(
                "input_col_idx",
                label="対象列",
                required=True
            ),
            params.StringParam(
                "new",
                label="新しい文字列",
                required=True
            )
        )

    def preproc(self, context):
        super().preproc(context)
        self.idx = context.get_param("input_col_idx")
        self.new_value = context.get_param("new")

    def process_record(self, record, context):
        value = record[self.idx]
        record[self.idx] = self.new_value
        context.output(record)


class StringMatchUpdateColConvertor(convertors.Convertor):
    r"""
    概要
        指定した列の値が指定した文字列と完全に一致する場合、
        新しい文字列に置き換えます。部分一致は置き換えません。

    コンバータ名
        "update_col_match"

    パラメータ
        * "input_col_idx": 検索対象列の列番号または列名 [必須]
        * "query": 検索文字列 [必須]
        * "new": 置き換える文字列 [必須]

    サンプル
        「性別」列が「女」の場合、「F」に置き換えます。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "update_col_match",
                "params": {
                    "input_col_idx": "性別",
                    "query": "女",
                    "new": "F"
                }
            }

        - コード例

        .. code-block:: python

            >>> # データはランダム生成
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '"氏名","生年月日","性別","クレジットカード"\n'
            ...     '"小室 友子","1990年06月20日","女","3562635454918233"\n'
            ...     '"江島 佳洋","1992年10月07日","男","376001629316609"\n'
            ...     '"三沢 大志","1995年02月13日","男","4173077927458449"\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="update_col_match",
            ...     params={
            ...         "input_col_idx": "性別",
            ...         "query": "女",
            ...         "new": "F",
            ...     },
            ... )
            >>> table.write()
            氏名,生年月日,性別,クレジットカード
            小室 友子,1990年06月20日,F,3562635454918233
            江島 佳洋,1992年10月07日,男,376001629316609
            三沢 大志,1995年02月13日,男,4173077927458449

    """

    class Meta:
        key = "update_col_match"
        name = "列の値を変更（完全一致）"
        description = """
        指定された列の値が文字列と完全一致する場合に変更します
        """
        help_text = """
        「対象列」の値が「文字列」と完全一致する場合、
        「新しい文字列」に変更します。
        """

        params = params.ParamSet(
            params.InputAttributeParam(
                "input_col_idx",
                label="対象列",
                required=True
            ),
            params.StringParam(
                "query",
                label="文字列",
                required=True
            ),
            params.StringParam(
                "new",
                label="新しい文字列",
                required=True
            )
        )

    def preproc(self, context):
        super().preproc(context)
        self.idx = context.get_param("input_col_idx")
        self.query = context.get_param("query")
        self.new_value = context.get_param("new")

    def process_record(self, record, context):
        value = record[self.idx]
        if self.query == value:
            record[self.idx] = self.new_value

        context.output(record)


class StringContainUpdateColConvertor(convertors.Convertor):
    r"""
    概要
        指定した列の値が指定した文字列を含む場合、
        その部分を新しい文字列に置き換えます。

    コンバータ名
        "update_col_contains"

    パラメータ
        * "input_col_idx": 検索対象列の列番号または列名 [必須]
        * "query": 検索文字列 [必須]
        * "new": 置き換える文字列 [必須]

    サンプル
        先頭列に「　」（全角空白）を含む場合、「」に置き換えます（削除）。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "update_col_contains",
                "params": {
                    "input_col_idx": 0,
                    "query": "　",
                    "new": ""
                }
            }

        - コード例

        .. code-block:: python

            >>> # 「人口動態調査(2020年)上巻_3-3-1_都道府県（特別区－指定都市再掲）
            >>> # 別にみた人口動態総覧」（厚生労働省）より作成
            >>> # https://www.data.go.jp/data/dataset/mhlw_20211015_0019
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     ',人口,出生数,死亡数\n'
            ...     '全　国,123398962,840835,1372755\n'
            ...     '01 北海道,5188441,29523,65078\n'
            ...     '02 青森県,1232227,6837,17905\n'
            ...     '03 岩手県,1203203,6718,17204\n'
            ...     '04 宮城県,2280203,14480,24632\n'
            ...     '05 秋田県,955659,4499,15379\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="update_col_contains",
            ...     params={
            ...         "input_col_idx": 0,
            ...         "query": "　",
            ...         "new": "",
            ...     },
            ... )
            >>> table.write()
            ,人口,出生数,死亡数
            全国,123398962,840835,1372755
            01 北海道,5188441,29523,65078
            ...

    """

    class Meta:
        key = "update_col_contains"
        name = "列の値を変更（部分一致）"
        description = """
        指定された列の値が文字列と部分一致する場合に変更します
        """
        help_text = """
        「対象列」の値の一部が「文字列」に一致する場合、
        一致した部分を「新しい文字列」に変更します。
        """

        params = params.ParamSet(
            params.InputAttributeParam(
                "input_col_idx",
                label="対象列",
                required=True
            ),
            params.StringParam(
                "query",
                label="文字列",
                required=True
            ),
            params.StringParam(
                "new",
                label="新しい文字列",
                required=True
            )
        )

    def preproc(self, context):
        super().preproc(context)
        self.idx = context.get_param("input_col_idx")
        self.query = context.get_param("query")
        self.new_value = context.get_param("new")

    def process_record(self, record, context):
        value = record[self.idx]
        if self.query in value:
            # すべての出現箇所を置換
            record[self.idx] = value.replace(
                self.query, self.new_value)

        context.output(record)


class PatternMatchUpdateColConvertor(convertors.Convertor):
    r"""
    概要
        指定した列の値が指定した正規表現と一致する場合、
        一致した部分を新しい文字列に置き換えます。
        正規表現は列の途中が一致しても対象となります（search）。

    コンバータ名
        "update_col_pattern"

    パラメータ
        * "input_col_idx": 検索対象列の列番号または列名 [必須]
        * "query": 正規表現 [必須]
        * "new": 置き換える文字列 [必須]

    サンプル
        先頭列が「01 北海道」のように数字に続く空白を含む場合、
        その部分を「」に置き換えます（削除）。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "update_col_pattern",
                "params": {
                    "input_col_idx": 0,
                    "query": "\d+\s+",
                    "new": ""
                }
            }

        - コード例

        .. code-block:: python

            >>> # 「人口動態調査(2020年)上巻_3-3-1_都道府県（特別区－指定都市再掲）
            >>> # 別にみた人口動態総覧」（厚生労働省）より作成
            >>> # https://www.data.go.jp/data/dataset/mhlw_20211015_0019
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     ',人口,出生数,死亡数\n'
            ...     '全　国,123398962,840835,1372755\n'
            ...     '01 北海道,5188441,29523,65078\n'
            ...     '02 青森県,1232227,6837,17905\n'
            ...     '03 岩手県,1203203,6718,17204\n'
            ...     '04 宮城県,2280203,14480,24632\n'
            ...     '05 秋田県,955659,4499,15379\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="update_col_pattern",
            ...     params={
            ...         "input_col_idx": 0,
            ...         "query": r"\d+\s+",
            ...         "new": "",
            ...     },
            ... )
            >>> table.write()
            ,人口,出生数,死亡数
            全　国,123398962,840835,1372755
            北海道,5188441,29523,65078
            青森県,1232227,6837,17905
            ...

    """

    class Meta:
        key = "update_col_pattern"
        name = "列の値を変更（正規表現）"
        description = """
        指定された列の値が指定した正規表現と一致する場合に変更します
        """
        help_text = """
        「対象列」の値の一部が「正規表現」に一致する場合、
        一致した部分を「新しい文字列」に変更します。
        """

        params = params.ParamSet(
            params.InputAttributeParam(
                "input_col_idx",
                label="対象列",
                required=True
            ),
            params.StringParam(
                "query",
                label="正規表現",
                required=True
            ),
            params.StringParam(
                "new",
                label="新しい文字列",
                required=True
            )
        )

    def preproc(self, context):
        super().preproc(context)
        self.idx = context.get_param("input_col_idx")
        self.re_pattern = re.compile(context.get_param('query'))
        self.new_value = context.get_param("new")

    def process_record(self, record, context):
        record[self.idx] = self.re_pattern.sub(
            self.new_value, record[self.idx])

        context.output(record)

from logging import getLogger

from tablelinker.core import convertors, params

logger = getLogger(__name__)


class RenameColConvertor(convertors.Convertor):
    r"""
    概要
        列名を変更します。

    コンバータ名
        "rename_col"

    パラメータ
        * "input_col_idx": 変更する列の列番号または列名 [必須]
        * "output_col_name": 新しい列名 [必須]

    注釈
        - 新しい列名が元の表に存在していても同じ名前の列を追加します。

    サンプル
        先頭列（0列目）の名称を「地域」に変更します。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "rename_col",
                "params": {
                    "input_col_idx": 0,
                    "output_col_name": "地域"
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
            ...     convertor="rename_col",
            ...     params={
            ...         "input_col_idx": 0,
            ...         "output_col_name": "地域",
            ...     },
            ... )
            >>> table.write()
            地域,人口,出生数,死亡数
            全　国,123398962,840835,1372755
            01 北海道,5188441,29523,65078
            ...


    """

    class Meta:
        key = "rename_col"
        name = "カラム名変更"

        description = """
        指定した列名を変更します
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
                "output_col_name",
                label="新しい列名",
                required=True
            ),
        )

    def process_header(self, headers, context):
        input_col_idx = context.get_param("input_col_idx")
        new_name = context.get_param("output_col_name")
        headers[input_col_idx] = new_name
        context.output(headers)


class RenameColsConvertor(convertors.Convertor):
    r"""
    概要
        すべての列名を一括変更します。

    コンバータ名
        "rename_cols"

    パラメータ
        * "column_list": 新しい列名のリスト [必須]

    注釈
        - ``column_list`` の列数が既存の列数と等しくないとエラーになります。

    サンプル
        列名を一括変換します。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "rename_cols",
                "params": {
                    "column_list": [
                        "Area",
                        "Population",
                        "Births",
                        "Deaths"
                    ]
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
            ...     convertor="rename_cols",
            ...     params={
            ...         "column_list": [
            ...             "Area",
            ...             "Population",
            ...             "Births",
            ...             "Deaths",
            ...         ],
            ...     },
            ... )
            >>> table.write()
            Area,Population,Births,Deaths
            全　国,123398962,840835,1372755
            01 北海道,5188441,29523,65078
            ...

    """

    class Meta:
        key = "rename_cols"
        name = "カラム名一括変更"
        description = "カラム名を一括で変更します"
        help_text = None

        params = params.ParamSet(
            params.StringListParam(
                "column_list",
                label="カラム名リスト",
                description="変更後のカラム名のリスト",
                required=True),
        )

    def process_header(self, headers, context):
        output_headers = context.get_param("column_list")
        if len(headers) != len(output_headers):
            logger.error("新しい列数と、既存の列数が一致しません。")
            raise ValueError((
                "The length of 'column_list' must be equal to "
                "the length of the original rows."))

        context.output(output_headers)

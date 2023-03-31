from tablelinker.core import convertors, params


class DeleteColConvertor(convertors.Convertor):
    r"""
    概要
        指定した列を削除します。

    コンバータ名
        "delete_col"

    パラメータ
        * "input_col_idx": 削除する入力列の列番号または列名 [必須]

    サンプル
        「クレジットカード」列を削除します。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "delete_col",
                "params": {
                    "input_col_idx": "クレジットカード"
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
            ...     convertor="delete_col",
            ...     params={
            ...         "input_col_idx": "クレジットカード",
            ...     },
            ... )
            >>> table.write()
            氏名,生年月日,性別
            小室 友子,1990年06月20日,女
            江島 佳洋,1992年10月07日,男
            三沢 大志,1995年02月13日,男

    """

    class Meta:
        key = "delete_col"
        name = "列を削除する"

        description = """
        指定した列を削除します
        """

        help_text = None

        params = params.ParamSet(
            params.InputAttributeParam(
                "input_col_idx",
                label="削除する列",
                description="削除する列",
                required=True
            ),
        )

    def preproc(self, context):
        super().preproc(context)
        self.input_col_idx = context.get_param("input_col_idx")

    def process_header(self, headers, context):
        headers = self.delete_col(self.input_col_idx, headers)
        context.output(headers)

    def process_record(self, record, context):
        record = self.delete_col(self.input_col_idx, record)
        context.output(record)

    def delete_col(self, input_col_idx, target_list):
        target_list.pop(input_col_idx)
        return target_list


class DeleteColsConvertor(convertors.Convertor):
    r"""
    概要
        指定した複数の列を削除します。

    コンバータ名
        "delete_cols"

    パラメータ
        * "input_col_idxs": 削除する入力列の列番号または列名のリスト [必須]

    サンプル
        「生年月日」「クレジットカード」列を削除します。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "delete_cols",
                "params": {
                    "input_col_idxs": ["生年月日", "クレジットカード"]
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
            ...     convertor="delete_cols",
            ...     params={
            ...         "input_col_idxs": ["生年月日", "クレジットカード"],
            ...     },
            ... )
            >>> table.write()
            氏名,性別
            小室 友子,女
            江島 佳洋,男
            三沢 大志,男

    """

    class Meta:
        key = "delete_cols"
        name = "列を削除する"

        description = """
        指定した列を削除します
        """

        help_text = None

        params = params.ParamSet(
            params.InputAttributeListParam(
                "input_col_idxs",
                label="削除する列",
                description="削除する列",
                required=True),
        )

    def process_header(self, headers, context):
        self.input_col_idxs = sorted(
            context.get_param("input_col_idxs"), reverse=True)
        headers = self.delete_cols(self.input_col_idxs, headers)
        context.output(headers)

    def process_record(self, record, context):
        record = self.delete_cols(self.input_col_idxs, record)
        context.output(record)

    def delete_cols(self, positions, target_list):
        for pos in positions:
            target_list.pop(pos)

        return target_list

import re

from tablelinker.core import convertors, params


def concat(value_list, separator=""):
    """文字列を結合します。
    value_list: 対象の文字列リスト
    separator: 区切り文字
    """

    if separator is None:
        separator = ""

    str_value_list = [str(value) for value in value_list]
    return separator.join(str_value_list)


class ConcatTitleConvertor(convertors.Convertor):
    r"""
    概要
        タイトル行が複数行に分割されている場合に結合して
        列見出しに設定します。列見出し中の改行は削除します。
        タイトル行以降のデータには影響しません。

    コンバータ名
        "concat_title"

    パラメータ
        * "title_from": タイトル行の開始行番号 [0]
        * "title_lines": タイトル行として利用する行数
        * "data_from": データ行の先頭行の行番号または含む文字列
        * "empty_value": 空欄の場合の文字列: ""
        * "separator": 区切り文字 ["/"]
        * "hierarchical_heading": 階層型見出しかどうか [False]

    注釈
        - ``title_lines`` と ``data_from`` はどちらかを指定してください。
          両方指定すると ``title_lines`` を優先します。
        - ``empty_value`` に "" を指定すると、空欄の行は無視されます。
        - ``hierarchical_heading`` に True を指定すると、上の列が
          空欄の場合にその左側の値を上位見出しとして利用します。

          eStat の表など、1行目に大項目、2行目に小項目が記載されている場合に
          このオプションを指定してください。

    サンプル

        国の集計表によく見られる、1行目に大項目、2行目と3行目に
        小項目が分割して記載されているタイトルを、
        ``hierarchical_heading`` を True にして階層見出しとして結合します。
        ``data_from`` で"全　国" を含む行からデータ行と指定することで、
        その前の行までをタイトル行と判断します。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "concat_title",
                "params": {
                    "data_from": "全　国",
                    "separator": "",
                    "hierarchical_heading": true
                }
            }

        - コード例

        .. code-block:: python

            >>> # 「人口動態調査(2020年)上巻_3-3-1_都道府県（特別区－指定都市再掲）
            >>> # 別にみた人口動態総覧」（厚生労働省）より作成
            >>> # https://www.data.go.jp/data/dataset/mhlw_20211015_0019
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     ',人口,出生数,死亡数,（再掲）,,自　然,死産数,,,周産期死亡数,,,婚姻件数,離婚件数\n'
            ...     ',,,,乳児死亡数,新生児,増減数,総数,自然死産,人工死産,総数,22週以後,早期新生児,,\n'
            ...     ',,,,,死亡数,,,,,,の死産数,死亡数,,\n'
            ...     '全　国,123398962,840835,1372755,1512,704,-531920,17278,8188,9090,2664,2112,552,525507,193253\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="concat_title",
            ...     params={
            ...         "data_from": "全　国",
            ...         "separator": "",
            ...         "hierarchical_heading": True,
            ...     },
            ... )
            >>> table.write()
            ,人口,出生数,死亡数,（再掲）乳児死亡数,（再掲）新生児死亡数,自　然増減数,死産数総数,死産数自然死産,死産数人工死産,周産期死亡数総数,周産期死亡数22週以後の死産数,周産期死亡数早期新生児死亡数,婚姻件数,離婚件数
            全　国,123398962,840835,1372755,1512,704,-531920,17278,8188,9090,2664,2112,552,525507,193253

    """  # noqa: E501

    class Meta:
        key = "concat_title"
        name = "タイトル結合"

        description = """
        指定した行数の列見出しを結合して新しいタイトルを生成します
        """

        help_text = ""

        params = params.ParamSet(
            params.IntParam(
                "title_from",
                label="タイトル行の開始行番号",
                required=False,
                default_value=0,
            ),
            params.IntParam(
                "title_lines",
                label="タイトル行の行数",
                required=False,
                default_value=0,
            ),
            params.StringParam(
                "data_from",
                label="データ行の開始行番号、または文字列",
                required=False,
                default_value="",
            ),
            params.StringParam(
                "empty_value",
                label="空欄表示文字",
                required=False,
                default_value="",
            ),
            params.StringParam(
                "separator",
                label="区切り文字",
                required=False,
                default_value="/",
            ),
            params.BooleanParam(
                "hierarchical_heading",
                label="階層型見出し",
                required=False,
                default_value=False,
            ),
        )

    def preproc(self, context):
        super().preproc(context)
        self.title_from = context.get_param("title_from")
        self.title_lines = context.get_param("title_lines")
        self.data_from = context.get_param("data_from")
        self.empty_value = context.get_param("empty_value")
        self.separator = context.get_param("separator")
        self.hierarchical = context.get_param("hierarchical_heading")

        if self.title_lines == 0 and self.data_from == "":
            raise ValueError(
                "title_lines か data_from のどちらかを指定してください。")
        elif self.title_lines > 0:
            # 指定された行数をタイトル行とする
            pass
        else:
            if re.match(r"^\d{1}$", self.data_from):
                # データ行が数値で指定されている場合
                self.title_lines = int(self.data_from) - self.title_from
            else:
                # 開始行までスキップ
                context.reset()
                rows = context.next()
                for _ in range(0, self.title_from):
                    rows = context.next()

                # 指定された文字列を含む行を探す
                for i in range(0, 10):
                    for row in rows:
                        if self.data_from in row:
                            self.title_lines = i
                            break

                    if self.title_lines > 0:
                        break

                    rows = context.next()

        if self.title_lines == 0:
            raise ValueError(
                "文字列 '{}' を含む行が見つかりません。".format(self.data_from))

    def process_header(self, headers, context):
        # 開始行までスキップ
        for _ in range(0, self.title_from):
            headers = context.next()

        new_headers = [[] for _ in range(len(headers))]
        for lineno in range(0, self.title_lines):
            for i, value in enumerate(headers):
                value = value.replace("\n", "")
                if value != "":
                    if self.hierarchical and i > 0 and \
                            "".join(new_headers[i]) == "":
                        new_headers[i] = new_headers[i - 1][: -1]

                    new_headers[i].append(value)
                else:
                    new_headers[i].append("")

            if lineno < self.title_lines - 1:
                headers = context.next()

        for i, values in enumerate(new_headers):
            if self.empty_value != "":
                values = filter(
                    None,
                    [v if v != "" else self.empty_value for v in values]
                )
            else:
                values = filter(None, values)

            headers[i] = concat(values, self.separator)

        context.output(headers)

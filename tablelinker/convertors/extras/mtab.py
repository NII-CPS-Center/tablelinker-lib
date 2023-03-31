import csv
import io

import requests

from tablelinker.core import convertors, params

MTAB_URL = "https://mtab.app/api/v1/mtab"


class MTabResult(object):
    """
    Mtab のレスポンスを解析するクラス
    """

    def __init__(self, mtab_response: dict = None):
        self.run_time = None
        self.structure_data = None
        self.cta_data = None
        self.cea_data = None

        if mtab_response is not None:
            self.analyze(mtab_response)

    def analyze(self, mtab_response: dict):
        self.analyze_structure(mtab_response)
        self.analyze_cta(mtab_response)
        self.analyze_cea(mtab_response)

    def analyze_structure(self, result_json):
        if result_json and result_json["tables"]:
            self.run_time = result_json["tables"][0]["run_time"]
            self.structure_data = result_json["tables"][0]["structure"]

    def analyze_cta(self, result_json):
        if result_json and result_json["tables"]:
            self.cta_data = result_json["tables"][0]["semantic"]["cta"]

    def analyze_cea(self, result_json):
        if result_json and result_json["tables"]:
            self.cea_data = result_json["tables"][0]["semantic"]["cea"]


def query_mtab(context, max_lines=None):
    # Mtab に送信するデータを作成
    with context._input as f_in:
        buf = io.StringIO()
        writer = csv.writer(buf)
        lines = 0
        for row in f_in:
            writer.writerow(row)
            lines += 1
            if max_lines is not None and lines == max_lines:
                break

        data = buf.getvalue()

    # Mtab に問い合わせ
    try:
        files = {"file": ("mtab.csv", data, "text/csv")}
        response = requests.post(MTAB_URL, files=files)

        if response.status_code == 200:
            response_json = response.json()

    except Exception as message:
        raise message

    mtab_result = MTabResult(response_json)

    return mtab_result


class MtabWikilinkConvertor(convertors.InputOutputConvertor):
    r"""
    概要
        Mtab を利用して、各行の情報に合致する
        Wikidata へのリンクを計算します。


    コンバータ名
        "geocoder_code"

    パラメータ（InputOutputConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_name": 結果を出力する列名
        * "output_col_idx": 分割した結果を出力する列番号または列名
        * "overwrite": 既に値がある場合に上書きするかどうか [True]

    パラメータ（コンバータ固有）
        * "lines": 処理する最大の行数を指定します [無制限]

    注釈（InputOutputConvertor 共通）
        - ``output_col_name`` が省略された場合、
          ``input_col_idx`` 列の列名が出力列名として利用されます。
        - ``output_col_idx`` が省略された場合、
          出力列名が存在する列名ならばその列の位置に出力し、
          存在しないならば最後尾に追加します。

    サンプル
        先頭列の要素に対応する Wikidata へのリンクを末尾に追加します。
        最大100行まで処理します。

        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "mtab_wikilink",
                "params": {
                    "input_col_idx": "col0",
                    "output_col_name": "Wikilink",
                    "lines": 100
                }
            }

        - コード例

        .. code-block:: python

            >>> from tablelinker import Table
            >>> # mTab API sample より取得
            >>> # https://mtab.app/mtab
            >>> table = Table(data=(
            ...     "col0,col1,col2,col3\n"
            ...     "2MASS J10540655-0031018,-5.7,19.3716366,13.635635128508735\n"
            ...     "2MASS J0464841+0715177,-2.7747499999999996,26.671235999999997,"
            ...     "11.818755055646479\n"
            ...     "2MAS J08351104+2006371,72.216,3.7242887999999996,128.15196099865955\n"
            ...     "2MASS J08330994+186328,-6.993,6.0962562,127.64996294136303\n"
            ... ))
            >>> table = table.convert(
            ...     convertor="mtab_wikilink",
            ...     params={
            ...         "input_col_idx": "col0",
            ...         "output_col_name": "wikilink",
            ...         "lines": 100,
            ...     },
            ... )
            >>> table.write()
            col0,col1,col2,col3,wikilink
            2MASS J10540655-0031018,-5.7,19.3716...,13.6356...,http://www.wikidata.org/entity/Q...
            2MASS J0464841+0715177,-2.7747...,26.6712...,11.8187...,http://www.wikidata.org/entity/Q...
            ...

    """  # noqa: E501

    class Meta:
        key = "mtab_wikilink"
        name = "Mtabデータからwikidata列を追加する"
        description = """
        Mtabデータからwikidataの列を追加します
        """
        help_text = ""
        params = params.ParamSet(
            params.IntParam(
                "lines",
                label="処理する最大行数",
                required=False,
                help_text="処理する最大行数を指定します。"
            ),

        )

    def preproc(self, context):
        super().preproc(context)
        context.reset()
        self.input_col_idx = context.get_param("input_col_idx")
        self.lines = context.get_param("lines")
        self.wikidata = None

        mtab_result = query_mtab(context, max_lines=self.lines)
        if mtab_result:
            wikidata_map = []
            for data in mtab_result.cea_data:
                row = data["target"][0]
                col = data["target"][1]
                if col == self.input_col_idx:
                    wikidata = data["annotation"]["wikidata"]
                    if len(wikidata_map) < row + 1:
                        wikidata_map += [""] * (row - len(wikidata_map) + 1)

                    wikidata_map[row] = wikidata

            self.wikidata = wikidata_map

    def process_header(self, headers, context):
        super().process_header(headers, context)
        # ヘッダ行に対応する wikilink データを削除する
        if len(self.wikidata) > 0:
            self.wikidata.pop(0)

    def process_convertor(self, record, context):
        if len(self.wikidata) > 0:
            wikilink = self.wikidata.pop(0)
        else:
            wikilink = ""

        return wikilink


class MtabColumnAnnotationConvertor(convertors.Convertor):
    r"""
    概要
        Mtab を利用して、各列のアノテーションを生成します。
        生成したアノテーションは最初の行に格納されます。

    コンバータ名
        "geocoder_cta"

    パラメータ
        * "lines": アノテーションに利用する最大の行数を指定します [100]

    注釈
        * アノテーションの候補が複数見つかった場合、 "/" で結合して
          列挙します。
        * アノテーションの候補が見つからなかった場合、 "-" を記載します。

    サンプル
        各列のアノテーションを生成し、最初の行（見出し行の次）に格納します。

        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "mtab_cta",
                "params": {
                    "lines": 100
                }
            }

        - コード例

        .. code-block:: python

            >>> from tablelinker import Table
            >>> # mTab API sample より取得
            >>> # https://mtab.app/mtab
            >>> table = Table(data=(
            ...     "col0,col1,col2,col3\n"
            ...     "2MASS J10540655-0031018,-5.7,19.3716366,13.635635128508735\n"
            ...     "2MASS J0464841+0715177,-2.7747499999999996,26.671235999999997,"
            ...     "11.818755055646479\n"
            ...     "2MAS J08351104+2006371,72.216,3.7242887999999996,128.15196099865955\n"
            ...     "2MASS J08330994+186328,-6.993,6.0962562,127.64996294136303\n"
            ... ))
            >>> table = table.convert(
            ...     convertor="mtab_cta",
            ...     params={
            ...         "lines": 100,
            ...     },
            ... )
            >>> table.write()
            col0,col1,col2,col3
            star/near-IR source,-,-,-
            2MASS J10540655-0031018,-5.7,19.3716...,13.6356...
            ...

    """  # noqa: E501

    class Meta:
        key = "mtab_cta"
        name = "Mtabデータから列アノテーションを生成する。"
        description = """
        mTabに問い合わせて列アノテーションを生成します。
        """
        help_text = ""
        params = params.ParamSet(
            params.IntParam(
                "lines",
                label="アノテーションに利用する最大行数",
                required=False,
                help_text="アノテーションに利用する最大行数を指定します。"
            ),

        )

    def preproc(self, context):
        super().preproc(context)
        context.reset()
        self.lines = context.get_param("lines")

        mtab_result = query_mtab(context, max_lines=self.lines)
        if mtab_result:
            self.cta = mtab_result.cta_data
        else:
            self.cta = None

    def process_header(self, headers, context):
        super().process_header(headers, context)
        record = ["-"] * len(headers)
        if self.cta:
            for anno in self.cta:
                labels = []
                for candidate in anno['annotation']:
                    labels.append(candidate['label'])

                record[anno['target']] = "/".join(labels)

        else:
            record = ["(none)"] * len(headers)

        context.output(record)

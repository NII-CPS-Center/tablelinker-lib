import re

from jeraconv import jeraconv

from tablelinker.core import convertors, params


class ToSeirekiConvertor(convertors.InputOutputConvertor):
    r"""
    概要
        和暦から西暦を計算します。

    コンバータ名
        "to_seireki"

    パラメータ（InputOutputConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_name": 結果を出力する列名
        * "output_col_idx": 分割した結果を出力する列番号または列名
        * "overwrite": 既に値がある場合に上書きするかどうか [True]

    注釈（InputOutputConvertor 共通）
        - ``output_col_name`` が省略された場合、
          ``input_col_idx`` 列の列名が出力列名として利用されます。
        - ``output_col_idx`` が省略された場合、
          出力列名が存在する列名ならばその列の位置に出力し、
          存在しないならば最後尾に追加します。

    サンプル
        「噴火年月日」列を西暦に変換します。

        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "to_seireki",
                "params": {
                    "input_col_idx": "噴火年月日",
                    "output_col_idx": 0,
                    "output_col_name": "噴火年月日"
                    "overwrite": true
                }
            }

        - コード例

        .. code-block:: python

            >>> # 気象庁「過去に発生した火山災害」より作成
            >>> # https://www.data.jma.go.jp/vois/data/tokyo/STOCK/kaisetsu/volcano_disaster.htm
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     "噴火年月日,火山名,犠牲者（人）,備考\n"
            ...     "享保6年6月22日,浅間山,15,噴石による\n"
            ...     "寛保元年8月29日,渡島大島,1467,岩屑なだれ・津波による\n"
            ...     "明和元年7月,恵山,多数,噴気による\n"
            ...     "安永8年11月8日,桜島,150余,噴石・溶岩流などによる「安永大噴火」\n"
            ...     "天明元年4月11日,桜島,8、不明7,高免沖の島で噴火、津波による\n"
            ...     "天明3年8月5日,浅間山,1151,火砕流、土石なだれ、吾妻川・利根川の洪水による\n"
            ...     "天明5年4月18日,青ヶ島,130～140,当時327人の居住者のうち130～140名が死亡と推定され、残りは八丈島に避難\n"
            ...     "寛政4年5月21日,雲仙岳,約15000,地震及び岩屑なだれによる「島原大変肥後迷惑」\n"
            ...     "文政5年3月23日,有珠山,103,火砕流による\n"
            ...     "天保12年5月23日,口永良部島,多数,噴火による、村落焼亡\n"
            ...     "安政3年9月25日,北海道駒ヶ岳,19～27,噴石、火砕流による\n"
            ...     "明治21年7月15日,磐梯山,461（477とも）,岩屑なだれにより村落埋没\n"
            ...     "明治33年7月17日,安達太良山,72,火口の硫黄採掘所全壊\n"
            ...     "明治35年8月上旬(7日～9日のいつか),伊豆鳥島,125,全島民死亡。\n"
            ...     "大正3年1月12日,桜島,58～59,噴火・地震による「大正大噴火」\n"
            ...     "大正15年5月24日,十勝岳,144（不明を含む）,融雪型火山泥流による「大正泥流」\n"
            ...     "昭和15年7月12日,三宅島,11,火山弾・溶岩流などによる\n"
            ...     "昭和27年9月24日,ベヨネース列岩,31,海底噴火（明神礁）、観測船第5海洋丸遭難により全員殉職\n"
            ...     "昭和33年6月24日,阿蘇山,12,噴石による\n"
            ...     "平成3年6月3日,雲仙岳,43（不明を含む）,火砕流による「平成3年(1991年)雲仙岳噴火」\n"
            ...     "平成26年9月27日,御嶽山,63（不明を含む）,噴石等による\n"
            ... ))
            >>> table = table.convert(
            ...     convertor="to_seireki",
            ...     params={
            ...         "input_col_idx": "噴火年月日",
            ...         "output_col_name": "噴火年月日",
            ...         "output_col_idx": 0,
            ...         "overwrite": True,
            ...     },
            ... )
            >>> table.write()
            噴火年月日,火山名,犠牲者（人）,備考
            1721年6月22日,浅間山,15,噴石による
            1741年8月29日,渡島大島,1467,岩屑なだれ・津波による
            1764年7月,恵山,多数,噴気による
            1779年11月8日,桜島,150余,噴石・溶岩流などによる「安永大噴火」
            ...

    """  # noqa: E501

    j2w = None

    class Meta:
        key = "to_seireki"
        name = "和暦西暦変換"
        description = """
        和暦を西暦に変換します
        """
        help_text = None
        params = params.ParamSet()

    def preproc(self, context):
        super().preproc(context)
        if self.__class__.j2w is None:
            self.__class__.j2w = jeraconv.J2W()

        # self.re_pattern = re.compile((
        #     r"明治(元|\d+)年|大正(元|\d+)年|昭和(元|\d+)年"
        #     r"|平成(元|\d+)年|令和(元|\d+)年"))

        self.re_pattern = re.compile(r"(..(元|\d+)年?)")

    def process_convertor(self, record, context):
        result = record[self.input_col_idx]

        targets = self.re_pattern.findall(result)
        for target in targets:
            try:
                yy = "{:d}年".format(self.j2w.convert(target[0]))
                result = result.replace(target[0], yy)
            except ValueError:
                # 和暦ではない
                continue

        return result


class ToWarekiConvertor(convertors.InputOutputConvertor):
    r"""
    概要
        西暦から和暦を計算します。

    コンバータ名
        "to_wareki"

    パラメータ（InputOutputConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_name": 結果を出力する列名
        * "output_col_idx": 分割した結果を出力する列番号または列名
        * "overwrite": 既に値がある場合に上書きするかどうか [True]

    注釈（InputOutputConvertor 共通）
        - ``output_col_name`` が省略された場合、
          ``input_col_idx`` 列の列名が出力列名として利用されます。
        - ``output_col_idx`` が省略された場合、
          出力列名が存在する列名ならばその列の位置に出力し、
          存在しないならば最後尾に追加します。

    サンプル
        「年次」列の西暦年を和暦に変換して「和暦」列に出力します。

        .. code-block :: json

            {
                "convertor": "to_wareki",
                "params": {
                    "input_col_idx": "年次",
                    "output_col_name": "和暦"
                    "output_col_idx": 1
                }
            }

        - コード例

        .. code-block:: python

            >>> # 統計局「人口推計 / 長期時系列データ 長期時系列データ
            >>> # （平成12年～令和２年）」より作成
            >>> from tablelinker import Table
            >>> # https://www.e-stat.go.jp/stat-search/files?page=1&layout=datalist&toukei=00200524&tstat=000000090001&cycle=0&tclass1=000000090004&tclass2=000001051180&tclass3val=0
            >>> table = Table(data=(
            ...     "年次,総人口（千人）\n"
            ...     "2000,126926\n"
            ...     "2005,127768\n"
            ...     "2010,128057\n"
            ...     "2015,127095\n"
            ...     "2020,126146\n"
            ... ))
            >>> table = table.convert(
            ...     convertor="to_wareki",
            ...     params={
            ...         "input_col_idx": "年次",
            ...         "output_col_name": "和暦",
            ...         "output_col_idx": 1,
            ...     },
            ... )
            >>> table.write()
            年次,和暦,総人口（千人）
            2000,平成12,126926
            2005,平成17,127768
            2010,平成22,128057
            2015,平成27,127095
            2020,令和2,126146

    """  # noqa: E501

    w2j = None

    class Meta:
        key = "to_wareki"
        name = "西暦和暦変換"
        description = """
        西暦を和暦に変換します
        """
        help_text = None
        params = params.ParamSet()

    def preproc(self, context):
        super().preproc(context)
        if self.__class__.w2j is None:
            self.__class__.w2j = jeraconv.W2J()

        # self.re_pattern = re.compile((
        #     r"明治(元|\d+)年|大正(元|\d+)年|昭和(元|\d+)年"
        #     r"|平成(元|\d+)年|令和(元|\d+)年"))

        self.re_pattern = re.compile(r"((西暦|)([12]\d{3})年?)")

    def process_convertor(self, record, context):
        result = record[self.input_col_idx]

        targets = self.re_pattern.findall(result)
        for target in targets:
            try:
                converted = self.w2j.convert(
                    int(target[2]), 1, 1, return_type='dict')
                yy = "{}{:d}".format(
                    converted['era'], converted['year'])
                if target[0][-1] == "年":
                    yy += "年"

                result = result.replace(target[0], yy)
            except ValueError:
                # 西暦ではない
                continue

        return result

from abc import ABC
from logging import getLogger
import re
from typing import List

import jageocoder

from tablelinker.core import convertors, params

logger = getLogger(__name__)

jageocoder_initialized = False
re_digits = re.compile(r'^\d+$')
re_spaces = re.compile(r'[ \t\n\r\u3000]+')


def initialize_jageocoder() -> bool:
    """
    jageocoder を初期化します。
    """
    global jageocoder_initialized
    if jageocoder_initialized:
        return True

    try:
        jageocoder.init()
        jageocoder_initialized = True
    except TypeError:
        jageocoder_initialized = False
        logger.error((
            "jageocoder の初期化に失敗しました。"
            "辞書データがインストールされていません。"))
    except RuntimeError as e:
        logger.error(e)
        jageocoder_initialized = False

    return jageocoder_initialized


def check_jageocoder(func):
    """
    jageocoder が利用できない場合は常に False を返す decorator
    利用できる場合は func を実行して結果を返します。
    """
    def wrapper(*args, **kwargs):
        if not initialize_jageocoder():
            return False

        return func(*args, **kwargs)

    return wrapper


@check_jageocoder
def search_node(address_or_id: str):
    """
    住所文字列またはノードIDから、対応する住所ノードを検索します。

    Parameters
    ----------
    address_or_id: str
        住所文字列、またはノードIDを変換した文字列。

    Returns
    -------
    jageocoder.node.AddressNode
        対応する住所要素ノードオブジェクト。
        見つからない場合には None を返します。

    Notes
    -----
    住所文字列から検索するより、一度検索した住所ノードの ID から
    検索する方がはるかに高速です。

    Examples
    --------
    >>> from tablelinker.convertors.extras.geocoder import search_node
    >>> node = search_node("東京都新宿区西新宿2-8-1")
    >>> node.x, node.y
    (139.691778, 35.689627)
    >>> node.get_fullname()
    ['東京都', '新宿区', '西新宿', '二丁目', '8番']
    >>> node_by_id = search_node(str(node.id))
    >>> node_by_id.get_fullname()
    ['東京都', '新宿区', '西新宿', '二丁目', '8番']

    """
    node = None
    if address_or_id == '':
        return None

    if re_digits.match(address_or_id):
        node = jageocoder.get_module_tree().get_node_by_id(address_or_id)
        return node

    address_or_id = re_spaces.sub('', address_or_id)

    try:
        candidates = jageocoder.searchNode(address_or_id)
        if len(candidates) > 0:
            node = candidates[0][0]

    except RuntimeError as e:
        logger.error(e)
        node = None

    return node


class GeocodeConvertor(ABC):
    """
    概要
        ジオコーディングを利用するコンバータのベース抽象クラスです。
        直接インスタンス化はできません。
    """

    def preproc_geocode(self, context):
        self.within = context.get_param("within")
        self.within_col_idxs = context.get_param("within_col_idxs")
        jageocoder.set_search_config(target_area=self.within)

    def search_node(self, value: str, record: List[str]):
        within = []
        for x in self.within_col_idxs:
            if record[x] and record[x][-1] in '都道府県市区町村':
                try:
                    jageocoder.set_search_config(target_area=record[x])
                    within.append(record[x])
                except RuntimeError:
                    pass

        if len(within) > 0:
            jageocoder.set_search_config(target_area=within)
        else:
            jageocoder.set_search_config(target_area=self.within)

        return search_node(value)


class ToCodeConvertor(convertors.InputOutputConvertor,
                      GeocodeConvertor):
    r"""
    概要
        住所から自治体コードを計算します。

    コンバータ名
        "geocoder_code"

    パラメータ（InputOutputConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_name": 結果を出力する列名
        * "output_col_idx": 分割した結果を出力する列番号または列名
        * "overwrite": 既に値がある場合に上書きするかどうか [True]

    パラメータ（コンバータ固有）
        * "within": 検索対象とする都道府県名、市区町村名のリスト []
        * "within_col_idxs": 検索対象とする都道府県名、市区町村名を含む
          列番号または列名のリスト []
        * "default": コードが計算できなかった場合の値 ["0"]
        * "with_check_digit": 検査数字を含むかどうか [False]

    注釈（InputOutputConvertor 共通）
        - ``output_col_name`` が省略された場合、
          ``input_col_idx`` 列の列名が出力列名として利用されます。
        - ``output_col_idx`` が省略された場合、
          出力列名が存在する列名ならばその列の位置に出力し、
          存在しないならば最後尾に追加します。

    注釈（コンバータ固有）
        - ``with_check_digit`` が False の場合は JIS の 5 桁コードを、
          True の場合は総務省の 6 桁コードを返します。
        - 住所が一意ではない場合、最初の候補を選択します。
          精度を向上させたい場合は ``within`` で候補となる
          都道府県名や市区町村名を指定してください。

    サンプル
        「住所」列から 5 桁自治体コードを算出し、
        1列目（先頭の次）に新しく「市区町村コード」列を作って格納します。
        「住所」列が空欄などで計算できない場合は "-" を格納します。

        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "geocoder_code",
                "params": {
                    "input_col_idx": "住所",
                    "output_col_name": "市区町村コード",
                    "output_col_idx": 1,
                    "within": ["北海道"],
                    "default": "-"
                }
            }

        - コード例

        .. code-block :: python

            >>> from tablelinker import Table
            >>> # 「令和3年度全国大学一覧/01国立大学一覧 (Excel:8.7MB)」より作成
            >>> # https://www.mext.go.jp/a_menu/koutou/ichiran/mext_01856.html
            >>> table = Table(data=(
            ...     '"機関名","郵便番号","所在地"\n'
            ...     '"北海道大学","060-0808","札幌市北区北8条西5"\n'
            ...     '"北海道教育大学","002-8501","札幌市北区あいの里5条3-1-3"\n'
            ...     '"室蘭工業大学","050-8585","室蘭市水元町27-1"\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="geocoder_code",
            ...     params={
            ...         "input_col_idx": "所在地",
            ...         "output_col_name": "市区町村コード",
            ...         "output_col_idx": 1,
            ...         "within": ["北海道"],
            ...         "default": "-",
            ...     },
            ... )
            >>> table.write()
            機関名,市区町村コード,郵便番号,所在地
            北海道大学,01102,060-0808,札幌市北区北8条西5
            北海道教育大学,01102,002-8501,札幌市北区あいの里5条3-1-3
            室蘭工業大学,01205,050-8585,室蘭市水元町27-1

    """  # noqa: E501

    class Meta:
        key = "geocoder_code"
        name = "住所から自治体コード"
        description = """
        住所から自治体コードを返します
        """
        help_text = None
        params = params.ParamSet(
            params.StringListParam(
                "within",
                label="都道府県・市区町村名のリスト",
                required=False,
                default_value=[],
                help_text="検索対象とする都道府県名・市区町村名のリスト。"),
            params.InputAttributeListParam(
                "within_col_idxs",
                label="都道府県・市区町村名を含む列のリスト",
                default_value=[],
                help_text="検索対象とする都道府県名・市区町村名を含む列のリスト。"),
            params.StringParam(
                "default",
                label="デフォルト値",
                required=False,
                default_value="0",
                help_text="コードが取得できない場合の値。"),
            params.BooleanParam(
                "with_check_digit",
                label="検査数字を含む",
                required=False,
                default_value=False,
                help_text="6桁団体コードの場合はチェック。"),)

    @check_jageocoder
    def preproc(self, context):
        super().preproc(context)
        super().preproc_geocode(context)
        self.with_check_digit = context.get_param("with_check_digit")
        self.default = context.get_param("default")

    def process_convertor(self, record, context):
        result = self.default
        value = str(record[self.input_col_idx])
        node = self.search_node(value, record)

        if node is not None:
            if self.with_check_digit:
                if node.level < 3:
                    result = node.get_pref_local_authority_code()
                else:
                    result = node.get_city_local_authority_code()
            else:
                if node.level < 3:
                    result = node.get_pref_jiscode() + "000"
                else:
                    result = node.get_city_jiscode()

        return result


class ToLatLongConvertor(convertors.InputOutputsConvertor,
                         GeocodeConvertor):
    r"""
    概要
        住所から緯度・経度・住所レベルを計算します。

    コンバータ名
        "geocoder_latlong"

    パラメータ（InputOutputsConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_names": 結果を出力する列名のリスト
        * "output_col_idx": 分割した結果を出力する列番号または列名
        * "overwrite": 既に値がある場合に上書きするかどうか [True]

    パラメータ（コンバータ固有）
        * "within": 検索対象とする都道府県名、市区町村名のリスト []
        * "within_col_idxs": 検索対象とする都道府県名、市区町村名を含む
          列番号または列名のリスト []
        * "default": 都道府県名が計算できなかった場合の値 ["", "", ""]

    注釈（InputOutputsConvertor 共通）
        - ``output_col_idx`` が省略された場合、最後尾に追加します。
        - ``output_col_names`` で指定された列名が存在している場合、
          ``output_col_idx`` が指定する位置に移動されます。

    注釈（コンバータ固有）
        - ``output_col_names`` には、「緯度」「経度」「住所レベル」を
          格納するための3つの列名を指定する必要があります。
          省略するとエラー（ValueError）になります。
        - 住所が一意ではない場合、最初の候補を選択します。
          精度を向上させたい場合は ``within`` で候補となる
          都道府県名や市区町村名を指定してください。

    サンプル
        「所在地」列から経緯度と住所レベルを計算し、
        先頭に新しく「緯度」「経度」「住所レベル」列を作って最後尾に格納します。
        「所在地」列が空欄などで計算できない場合は "-" を格納します。

        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "geocoder_latlong",
                "params": {
                    "input_col_idx": "所在地",
                    "output_col_names": ["緯度", "経度", "住所レベル"],
                    "output_col_idx": null,
                    "default": "-"
                }
            }

        - コード例

        .. code-block :: python

            >>> # 「令和3年度全国大学一覧/01国立大学一覧 (Excel:8.7MB)」より作成
            >>> # https://www.mext.go.jp/a_menu/koutou/ichiran/mext_01856.html
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '"機関名","郵便番号","所在地"\n'
            ...     '"北海道大学","060-0808","札幌市北区北8条西5"\n'
            ...     '"北海道教育大学","002-8501","札幌市北区あいの里5条3-1-3"\n'
            ...     '"室蘭工業大学","050-8585","室蘭市水元町27-1"\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="geocoder_latlong",
            ...     params={
            ...         "input_col_idx": "所在地",
            ...         "output_col_names": ["緯度", "経度", "住所レベル"],
            ...         "output_col_idx": None,
            ...         "default": "-",
            ...     },
            ... )
            >>> table.write()
            機関名,郵便番号,所在地,緯度,経度,住所レベル
            北海道大学,060-0808,札幌市北区北8条西5,43.070446,141.347151,6
            北海道教育大学,002-8501,札幌市北区あいの里5条3-1-3,43.170497,141.39375,7
            室蘭工業大学,050-8585,室蘭市水元町27-1,42.378715,141.034036,7

   """

    class Meta:
        key = "geocoder_latlong"
        name = "住所から緯度経度"
        description = """
        住所から緯度・経度を生成します
        """
        help_text = None
        params = params.ParamSet(
            params.StringListParam(
                "within",
                label="都道府県・市区町村名のリスト",
                required=False,
                default_value=[],
                help_text="検索対象とする都道府県名・市区町村名のリスト。"),
            params.InputAttributeListParam(
                "within_col_idxs",
                label="都道府県・市区町村名を含む列のリスト",
                default_value=[],
                help_text="検索対象とする都道府県名・市区町村名を含む列のリスト。"),
            params.StringListParam(
                "default",
                label="緯度・経度・住所レベルのデフォルト値",
                required=False,
                default_value=["", "", ""],
                help_text=""),
        )

    @check_jageocoder
    def preproc(self, context):
        super().preproc(context)
        super().preproc_geocode(context)
        self.within = context.get_param("within")
        self.default = context.get_param("default")

        # 出力列名が3つ指定されていることを確認
        self.output_col_names = context.get_param("output_col_names")
        if isinstance(self.output_col_names, str) or \
                len(self.output_col_names) != 3:
            raise ValueError((
                "The output_col_names parameter of geocoder_latlong "
                "requires 3 column names for latitude, longitude and level."))

        # デフォルト値が文字列の場合は 3 列ともその値にする
        # デフォルト値が 3 列でない場合、3 列分になるように加工する
        if isinstance(self.default, str):
            self.default = [self.default] * 3
        elif len(self.default) < 3:
            self.default = (self.default * 3)[0:3]
        elif len(self.default) > 3:
            self.default = self.default[0:3]

    def process_convertor(self, record, context):
        result = self.default
        value = str(record[self.input_col_idx])
        node = self.search_node(value, record)

        if node is not None:
            result = [node.y, node.x, node.level]

        return result


class ToMunicipalityConvertor(convertors.InputOutputsConvertor,
                              GeocodeConvertor):
    r"""
    概要
        住所から市区町村名を計算します。

    コンバータ名
        "geocoder_municipality"

    パラメータ（InputOutputsConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_names": 結果を出力する列名のリスト
        * "output_col_idx": 分割した結果を出力する列番号または列名
        * "overwrite": 既に値がある場合に上書きするかどうか [True]

    パラメータ（コンバータ固有）
        * "within": 検索対象とする都道府県名、市区町村名のリスト []
        * "within_col_idxs": 検索対象とする都道府県名、市区町村名を含む
          列番号または列名のリスト []
        * "default": 都道府県名が計算できなかった場合の値 ["", ""]

    注釈（InputOutputsConvertor 共通）
        - ``output_col_idx`` が省略された場合、最後尾に追加します。
        - ``output_col_names`` で指定された列名が存在している場合、
          ``output_col_idx`` が指定する位置に移動されます。

    注釈（コンバータ固有）
        - ``output_col_names`` に2列分の名前を指定した場合、
          政令指定都市ならば1列目に市名、2列目に区名を格納します。
          それ以外の市区町村の場合（特別区を含む）、1列目に
          市区町村名、2列目に空欄を格納します。
        - ``output_col_names`` に1列分の名前しか指定しなかった場合、
          政令指定都市ならばその列に市名と区名を空白で区切って格納します。
          それ以外の市区町村の場合（特別区を含む）、市区町村名を格納します。
        - 住所が一意ではない場合、最初の候補を選択します。
          精度を向上させたい場合は ``within`` で候補となる
          都道府県名や市区町村名を指定してください。

    サンプル
        「所在地」列から市区町村名を計算し、
        「所在地」列の前に新しく「市区町村」「（区）」列を作って格納します。
        「所在地」列が空欄などで計算できない場合は "-" を格納します。

        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "geocoder_municipality",
                "params": {
                    "input_col_idx": "所在地",
                    "output_col_name": ["市区町村", "（区）"]
                    "output_col_idx": "所在地",
                    "default": "-"
                }
            }

        - コード例

        .. code-block :: python

            >>> # 「令和3年度全国大学一覧/01国立大学一覧 (Excel:8.7MB)」より作成
            >>> # https://www.mext.go.jp/a_menu/koutou/ichiran/mext_01856.html
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '"機関名","郵便番号","所在地"\n'
            ...     '"北海道大学","060-0808","札幌市北区北8条西5"\n'
            ...     '"北海道教育大学","002-8501","札幌市北区あいの里5条3-1-3"\n'
            ...     '"室蘭工業大学","050-8585","室蘭市水元町27-1"\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="geocoder_municipality",
            ...     params={
            ...         "input_col_idx": "所在地",
            ...         "output_col_names": ["市区町村", "（区）"],
            ...         "output_col_idx": "所在地",
            ...         "default": "-",
            ...     },
            ... )
            >>> table.write()
            機関名,郵便番号,市区町村,（区）,所在地
            北海道大学,060-0808,札幌市,北区,札幌市北区北8条西5
            北海道教育大学,002-8501,札幌市,北区,札幌市北区あいの里5条3-1-3
            室蘭工業大学,050-8585,室蘭市,-,室蘭市水元町27-1

    """

    class Meta:
        key = "geocoder_municipality"
        name = "住所から市区町村"
        description = """
        住所から市区町村を返します
        """
        help_text = None
        params = params.ParamSet(
            params.StringListParam(
                "within",
                label="都道府県・市区町村名のリスト",
                required=False,
                default_value=[],
                help_text="検索対象とする都道府県名・市区町村名のリスト。"),
            params.InputAttributeListParam(
                "within_col_idxs",
                label="都道府県・市区町村名を含む列のリスト",
                default_value=[],
                help_text="検索対象とする都道府県名・市区町村名を含む列のリスト。"),
            params.StringListParam(
                "default",
                label="デフォルト市区町村",
                required=False,
                default_value=["", ""]),
        )

    @check_jageocoder
    def preproc(self, context):
        super().preproc(context)
        super().preproc_geocode(context)
        self.default = context.get_param("default")
        jageocoder.set_search_config(target_area=self.within)

        # 出力列名が2つ指定されていることを確認
        self.output_col_names = context.get_param("output_col_names")
        if self.output_col_names is None:
            self.output_col_names = ["市区町村名", "政令市の区名"]
        elif isinstance(self.output_col_names, str):
            self.output_col_names = [self.output_col_names]
        elif len(self.output_col_names) == 1:
            pass
        elif len(self.output_col_names) != 2:
            raise ValueError((
                "'geocoder_municiparlity' コンバータの 'output_col_names' "
                "パラメータには、「市区町村名」「政令市の区名」に対応する"
                "2つの列名を指定する必要があります。"))

        # デフォルト値が文字列の場合は 2 列ともその値にする
        # デフォルト値が 2 列でない場合、2 列分になるように加工する
        if isinstance(self.default, str):
            self.default = [self.default] * 2
        elif len(self.default) < 2:
            self.default = (self.default * 2)[0:2]
        elif len(self.default) > 2:
            self.default = self.default[0:2]

        # 出力列の数にそろえる
        self.default = self.default[0: len(self.output_col_names)]

    def process_convertor(self, record, context):
        result = self.default
        value = str(record[self.input_col_idx])
        node = self.search_node(value, record)

        if node is None:
            return result

        if node.level >= 3:
            parents = node.get_parent_list()
            parents.reverse()
            for i, parent in enumerate(parents):
                if parent.level == 4:  # 政令市の区
                    result = [parents[i + 1].name, parent.name]
                    break
                elif parent.level == 3:  # それ以外の市区町村
                    result = [parent.name]
                    break

        # 結果を1列で返す場合と2列で返す場合の処理
        if len(self.output_col_names) == 1 and len(result) > 1:
            result = [" ".join(result)]
        elif len(self.output_col_names) > 1 and len(result) == 1:
            result.append(self.default[1])

        return result


class ToNodeIdConvertor(convertors.InputOutputConvertor,
                        GeocodeConvertor):
    r"""
    概要
        住所からノードIDを計算します。

        住所から都道府県名や郵便番号を計算するコンバータを利用すると、
        そのたびに住所解析処理を行う必要があるため時間がかかりますが、
        住所の代わりにノードIDを入力とすることで
        住所解析を一度だけ行えば済むようになり、高速化できます。

    コンバータ名
        "geocoder_nodeid"

    パラメータ（InputOutputConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_name": 結果を出力する列名
        * "output_col_idx": 分割した結果を出力する列番号または列名
        * "overwrite": 既に値がある場合に上書きするかどうか [True]

    パラメータ（コンバータ固有）
        * "within": 検索対象とする都道府県名、市区町村名のリスト []
        * "within_col_idxs": 検索対象とする都道府県名、市区町村名を含む
          列番号または列名のリスト []
        * "default": ノードが見つからなかった場合の値 [""]

    注釈（InputOutputConvertor 共通）
        - ``output_col_name`` が省略された場合、
          ``input_col_idx`` 列の列名が出力列名として利用されます。
        - ``output_col_idx`` が省略された場合、
          出力列名が存在する列名ならばその列の位置に出力し、
          存在しないならば最後尾に追加します。

    注釈（コンバータ固有）
        - 住所が一意ではない場合、最初の候補を選択します。
          精度を向上させたい場合は ``within`` で候補となる
          都道府県名や市区町村名を指定してください。
        - ノードIDは住所辞書固有のIDなので、辞書を差し替えると
          同じ住所でも ID が変わる点に注意してください。

    サンプル
        「所在地」列から住所ノードIDを算出し、
        最後尾に「住所ノードID」列を作って格納します。
        「所在地」列が空欄などで計算できない場合は "" を格納します。

        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "geocoder_nodeid",
                "params": {
                    "input_col_idx": "所在地",
                    "output_col_name": "住所ノードID",
                    "output_col_idx": null,
                    "default": ""
                }
            }

        - コード例

        .. code-block :: python

            >>> # 「令和3年度全国大学一覧/01国立大学一覧 (Excel:8.7MB)」より作成
            >>> # https://www.mext.go.jp/a_menu/koutou/ichiran/mext_01856.html
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '"機関名","郵便番号","所在地"\n'
            ...     '"北海道大学","060-0808","札幌市北区北8条西5"\n'
            ...     '"北海道教育大学","002-8501","札幌市北区あいの里5条3-1-3"\n'
            ...     '"室蘭工業大学","050-8585","室蘭市水元町27-1"\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="geocoder_nodeid",
            ...     params={
            ...         "input_col_idx": "所在地",
            ...         "output_col_name": "住所ノードID",
            ...         "output_col_idx": None,
            ...         "within": ["北海道"],
            ...         "default": "",
            ...     },
            ... )
            >>> table.write()
            機関名,郵便番号,所在地,住所ノードID
            北海道大学,060-0808,札幌市北区北8条西5,...
            北海道教育大学,002-8501,札幌市北区あいの里5条3-1-3,...
            室蘭工業大学,050-8585,室蘭市水元町27-1,...

    """

    class Meta:
        key = "geocoder_nodeid"
        name = "住所からノードID"
        description = """
        住所からノードIDを返します
        """
        help_text = None
        params = params.ParamSet(
            params.StringListParam(
                "within",
                label="都道府県・市区町村名のリスト",
                required=False,
                default_value=[],
                help_text="検索対象とする都道府県名・市区町村名のリスト。"),
            params.InputAttributeListParam(
                "within_col_idxs",
                label="都道府県・市区町村名を含む列のリスト",
                default_value=[],
                help_text="検索対象とする都道府県名・市区町村名を含む列のリスト。"),
            params.StringParam(
                "default",
                label="デフォルト値",
                required=False,
                default_value="",
                help_text="住所が解析できない場合の値。"),
        )

    @check_jageocoder
    def preproc(self, context):
        super().preproc(context)
        super().preproc_geocode(context)
        self.default = context.get_param("default")
        jageocoder.set_search_config(target_area=self.within)

    def process_convertor(self, record, context):
        result = self.default
        value = str(record[self.input_col_idx])
        node = self.search_node(value, record)

        if node:
            result = node.id

        return result


class ToPostcodeConvertor(convertors.InputOutputConvertor,
                          GeocodeConvertor):
    r"""
    概要
        住所から郵便番号を検索します。ただしビルのフロアごとに
        振られている番号や、事業者の個別郵便番号は検索できません。

    コンバータ名
        "geocoder_postcode"

    パラメータ（InputOutputConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_name": 結果を出力する列名
        * "output_col_idx": 分割した結果を出力する列番号または列名
        * "overwrite": 既に値がある場合に上書きするかどうか [True]

    パラメータ（コンバータ固有）
        * "within": 検索対象とする都道府県名、市区町村名のリスト []
        * "within_col_idxs": 検索対象とする都道府県名、市区町村名を含む
          列番号または列名のリスト []
        * "default": 郵便番号が計算できなかった場合の値 [""]
        * "hiphen": 3桁目と4桁目の間にハイフンをいれるかどうか [False]

    注釈（InputOutputsConvertor 共通）
        - ``output_col_idx`` が省略された場合、最後尾に追加します。
        - ``output_col_names`` で指定された列名が存在している場合、
          ``output_col_idx`` が指定する位置に移動されます。

    注釈（コンバータ固有）
        - 住所が一意ではない場合、最初の候補を選択します。
          精度を向上させたい場合は ``within`` で候補となる
          都道府県名や市区町村名を指定してください。

    注釈（InputOutputConvertor 共通）
        - ``output_col_name`` が省略された場合、
          ``input_col_idx`` 列の列名が出力列名として利用されます。
        - ``output_col_idx`` が省略された場合、
          出力列名が存在する列名ならばその列の位置に出力し、
          存在しないならば最後尾に追加します。

    サンプル
        「所在地」列から郵便番号を算出し、
        「所在地」列の前の「郵便番号」列に上書きします。
        「所在地」列が空欄などで計算できない場合は空欄にします。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "geocoder_postcode",
                "params": {
                    "input_col_idx": "所在地",
                    "output_col_name": "郵便番号",
                    "output_col_idx": "所在地",
                    "default": "",
                    "hiphen": true,
                    "overwrite": true
                }
            }

        - コード例

        .. code-block :: python

            >>> # 「令和3年度全国大学一覧/01国立大学一覧 (Excel:8.7MB)」より作成
            >>> # https://www.mext.go.jp/a_menu/koutou/ichiran/mext_01856.html
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '"機関名","郵便番号","所在地"\n'
            ...     '"北海道大学","060-0808","札幌市北区北8条西5"\n'
            ...     '"北海道教育大学","002-8501","札幌市北区あいの里5条3-1-3"\n'
            ...     '"室蘭工業大学","050-8585","室蘭市水元町27-1"\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="geocoder_postcode",
            ...     params={
            ...         "input_col_idx": "所在地",
            ...         "output_col_name": "郵便番号",
            ...         "output_col_idx": "所在地",
            ...         "default": "",
            ...         "hiphen": True,
            ...         "overwrite": True,
            ...     },
            ... )
            >>> table.write()
            機関名,郵便番号,所在地
            北海道大学,060-0808,札幌市北区北8条西5
            北海道教育大学,002-8075,札幌市北区あいの里5条3-1-3
            室蘭工業大学,050-0071,室蘭市水元町27-1

    """

    class Meta:
        key = "geocoder_postcode"
        name = "住所から郵便番号"
        description = """
        住所から郵便番号を返します
        """
        help_text = None
        params = params.ParamSet(
            params.StringListParam(
                "within",
                label="都道府県・市区町村名のリスト",
                required=False,
                default_value=[],
                help_text="検索対象とする都道府県名・市区町村名のリスト。"),
            params.InputAttributeListParam(
                "within_col_idxs",
                label="都道府県・市区町村名を含む列のリスト",
                default_value=[],
                help_text="検索対象とする都道府県名・市区町村名を含む列のリスト。"),
            params.StringParam(
                "default",
                label="デフォルト値",
                required=False,
                default_value="0",
                help_text="郵便番号が取得できない場合の値。"),
            params.BooleanParam(
                "hiphen",
                label="3桁目の後ろにハイフンを入れるか",
                required=False,
                default_value=False,
                help_text="3桁目の後ろにハイフンを入れるかどうか。"),
        )

    @check_jageocoder
    def preproc(self, context):
        super().preproc(context)
        super().preproc_geocode(context)
        self.default = context.get_param("default")
        self.hiphen = context.get_param("hiphen")
        jageocoder.set_search_config(target_area=self.within)

    def process_convertor(self, record, context):
        result = self.default
        value = str(record[self.input_col_idx])
        node = self.search_node(value, record)

        if node is not None:
            result = node.get_postcode()

            if self.hiphen:
                result = result[0:3] + "-" + result[3:]

        return result


class ToPrefectureConvertor(convertors.InputOutputConvertor,
                            GeocodeConvertor):
    r"""
    概要
        住所から都道府県名を計算します。

    コンバータ名
        "geocoder_prefecture"

    パラメータ（InputOutputConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_name": 結果を出力する列名
        * "output_col_idx": 分割した結果を出力する列番号または列名
        * "overwrite": 既に値がある場合に上書きするかどうか [True]

    パラメータ（コンバータ固有）
        * "within": 検索対象とする都道府県名、市区町村名のリスト []
        * "within_col_idxs": 検索対象とする都道府県名、市区町村名を含む
          列番号または列名のリスト []
        * "default": 都道府県名が計算できなかった場合の値 [""]

    注釈（InputOutputConvertor 共通）
        - ``output_col_name`` が省略された場合、
          ``input_col_idx`` 列の列名が出力列名として利用されます。
        - ``output_col_idx`` が省略された場合、
          出力列名が存在する列名ならばその列の位置に出力し、
          存在しないならば最後尾に追加します。

    注釈（コンバータ固有）
        - 住所が一意ではない場合、最初の候補を選択します。
          精度を向上させたい場合は ``within`` で候補となる
          都道府県名や市区町村名を指定してください。

    サンプル
        「所在地」列から都道府県名を計算し、
        「郵便番号」列の前に新しく「都道府県名」列を作って格納します。
        「所在地」列が空欄などで計算できない場合は "" を格納します。

        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "geocoder_prefecture",
                "params": {
                    "input_col_idx": "所在地",
                    "output_col_name": "都道府県名",
                    "output_col_idx": "郵便番号",
                    "default": ""
                }
            }

        - コード例

        .. code-block :: python

            >>> # 「令和3年度全国大学一覧/01国立大学一覧 (Excel:8.7MB)」より作成
            >>> # https://www.mext.go.jp/a_menu/koutou/ichiran/mext_01856.html
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '"機関名","郵便番号","所在地"\n'
            ...     '"北海道大学","060-0808","札幌市北区北8条西5"\n'
            ...     '"北海道教育大学","002-8501","札幌市北区あいの里5条3-1-3"\n'
            ...     '"室蘭工業大学","050-8585","室蘭市水元町27-1"\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="geocoder_prefecture",
            ...     params={
            ...         "input_col_idx": "所在地",
            ...         "output_col_name": "都道府県名",
            ...         "output_col_idx": "郵便番号",
            ...         "default": "",
            ...     },
            ... )
            >>> table.write()
            機関名,都道府県名,郵便番号,所在地
            北海道大学,北海道,060-0808,札幌市北区北8条西5
            北海道教育大学,北海道,002-8501,札幌市北区あいの里5条3-1-3
            室蘭工業大学,北海道,050-8585,室蘭市水元町27-1

    """

    class Meta:
        key = "geocoder_prefecture"
        name = "住所から都道府県名"
        description = """
        住所から都道府県を返します
        """
        help_text = None
        params = params.ParamSet(
            params.StringListParam(
                "within",
                label="都道府県・市区町村名のリスト",
                required=False,
                default_value=[],
                help_text="検索対象とする都道府県名・市区町村名のリスト。"),
            params.InputAttributeListParam(
                "within_col_idxs",
                label="都道府県・市区町村名を含む列のリスト",
                default_value=[],
                help_text="検索対象とする都道府県名・市区町村名を含む列のリスト。"),
            params.StringParam(
                "default",
                label="デフォルト都道府県名",
                required=False,
                default_value=""),
        )

    @check_jageocoder
    def preproc(self, context):
        super().preproc(context)
        super().preproc_geocode(context)
        self.default = context.get_param("default")
        jageocoder.set_search_config(target_area=self.within)

    def process_convertor(self, record, context):
        result = self.default
        value = str(record[self.input_col_idx])
        node = self.search_node(value, record)

        if node is not None:
            result = node.get_pref_name()

        return result

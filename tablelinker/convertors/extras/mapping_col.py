from tablelinker.core import convertors, params
from tablelinker.core.mapping import ItemsPair


class AutoMappingColsConvertor(convertors.Convertor):
    r"""
    概要
        指定した列名リストに合わせて既存の列をマッピングします。
        マッピングは語ベクトルと表記の類似度によって決定します。

    コンバータ名
        "auto_mapping_cols"

    パラメータ
        * "column_list": 出力したい列名のリスト [必須]
        * "keep_colname": 元の列名を保持するか [False]
        * "threshold": 列をマッピングするしきい値 [40]

    注釈
        - 元の列のうち、マッピング先の列との類似度が ``threshold``
          以下のものは削除されます。
        - ``threshold`` は 0 - 100 の整数で指定します。
          値が大きいほど一致度が高いものしか残りません。
        - ``keep_colname`` に True を指定すると、元の列名と
          マッピング先の列名が異なる場合に出力列名を
          `<マッピング先の列名> / <元の列名>` に変更します。

    サンプル
        出力したい列名のリストに合わせてマッピングします。

        - タスクファイル例

        .. code-block:: json

            {
                "convertor": "auto_mapping_cols",
                "params": {
                    "column_list": ["名称", "所在地", "経度", "緯度", "説明"],
                    "keep_colname": true
                }
            }

        - コード例

        .. code-block:: python

            >>> # 「八丈島の主な観光スポット一覧」より作成
            >>> # https://catalog.data.metro.tokyo.lg.jp/dataset/t134015d0000000002
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '観光スポット名称,所在地,緯度,経度,座標系,説明,八丈町ホームページ記載\n'
            ...     'ホタル水路,,33.108218,139.80102,JGD2011,八丈島は伊豆諸島で唯一、水田耕作がなされた島で鴨川に沿って水田が残っています。ホタル水路は、鴨川の砂防とともに平成元年につくられたもので、毎年6月から7月にかけてホタルの光が美しく幻想的です。,http://www.town.hachijo.tokyo.jp/kankou_spot/mitsune.html#01\n'
            ...     '登龍峠展望,,33.113154,139.835245,JGD2011,「ノボリュウトウゲ」または「ノボリョウトウゲ」といい、この道を下方から望むとあたかも龍が昇天するように見えるので、この名が付けられました。峠道の頂上近くの展望台は、八丈島で一、二を争う景勝地として名高く、新東京百景の一つにも選ばれました。眼前に八丈富士と神止山、八丈小島を、眼下には底土港や神湊港、三根市街を一望できます。,http://www.town.hachijo.tokyo.jp/kankou_spot/mitsune.html#02\n'
            ...     '八丈富士,,33.139168,139.762187,JGD2011,八丈島の北西部を占める山で、東の三原山に対して『西山』と呼ばれます。伊豆諸島の中では最も高い標高854.3メートル。1605年の噴火後、活動を停止している火山で火口は直径400メートル深さ50メートルで、 さらに火口底には中央火口丘がある二重式火山です。裾野が大きくのびた優雅な姿は、八丈島を代表する美しさのひとつです。,http://www.town.hachijo.tokyo.jp/kankou_spot/mitsune.html#03\n'
            ...     '永郷展望,,33.153559,139.747501,JGD2011,島の北端に近く大越鼻灯台を間近に見る展望台で、すぐ左手に八丈小島が望めます。ここからの八丈小島は、標高618メートルの大平山を中心に形のよい稜線が左右に広がり特に美しいと言われています。周辺は、日本一のビロウヤシの群生地でフェニックス・ロベレニーなど南国の雰囲気が漂っています。空気の澄んだ日には、御蔵島と三宅島を望むことができます。,http://www.town.hachijo.tokyo.jp/kankou_spot/okago.html#04\n'
            ...     'ふれあい牧場,東京都八丈島 八丈町大賀郷5627-1,33.131167,139.767181,JGD2011,八丈富士の中腹に広がる「ふれあい牧場」は、穏やかな山の傾斜地に黒毛和牛やジャージーが放牧されています。また、牧場内の展望台からは、島の中心部や三原山、八丈島空港が一望でき、夜には満天の星空が眺められます。,http://www.town.hachijo.tokyo.jp/kankou_spot/okago.html#05\n'
            ...     '空港道路,,33.116885,139.781262,JGD2011,神湊商港（底土港）から八重根商港（都道）までの区間の路線。道路沿いに南国の象徴ハイビスカスが咲き、等間隔にビロウヤシが植栽されている光景は見ごたえがあります。,http://www.town.hachijo.tokyo.jp/kankou_spot/okago.html#06\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="auto_mapping_cols",
            ...     params={
            ...         "column_list": ["名称", "所在地", "経度", "緯度", "説明"],
            ...         "keep_colname": True,
            ...     },
            ... )
            >>> table.write()
            名称 / 観光スポット名称,所在地,経度,緯度,説明
            ホタル水路,,139.80102,33.108218,八丈島は伊豆諸島で唯一、...
            登龍峠展望,,139.835245,33.113154,「ノボリュウトウゲ」または...
            八丈富士,,139.762187,33.139168,八丈島の北西部を占める山で、...
            ...

    """  # noqa: E501

    class Meta:
        key = "auto_mapping_cols"
        name = "自動カラムマッピング"
        description = "カラムを指定したリストに自動マッピングします"
        help_text = None

        params = params.ParamSet(
            params.StringListParam(
                "column_list",
                label="カラムリスト",
                description="マッピング先のカラムリスト",
                required=True),
            params.BooleanParam(
                "keep_colname",
                label="元カラム名を保持",
                description="元のカラム名を保持するかどうか",
                required=False,
                default_value=False),
            params.IntParam(
                "threshold",
                label="しきい値",
                description="カラムが一致すると判定するしきい値(0-100)",
                required=False,
                default_value=40),
        )

    def process_header(self, headers, context):
        output_headers = context.get_param("column_list")
        pair = ItemsPair(output_headers, headers)
        self.mapping = []
        new_headers = []
        for result in pair.mapping():
            output, header, score = result
            if output is None:
                # マッピングされなかったカラムは除去
                continue

            if score * 100.0 < context.get_param("threshold") or \
                    header is None:
                self.mapping.append(None)
                new_headers.append(output)
            else:
                idx = headers.index(header)
                self.mapping.append(idx)
                if output == header or \
                        not context.get_param('keep_colname'):
                    new_headers.append(output)
                else:
                    new_headers.append("{} / {}".format(
                        output, header))

        context.output(new_headers)

    def process_record(self, record, context):
        context.output(self.reorder(record))

    def reorder(self, fields):
        new_fields = []
        for idx in self.mapping:
            if idx is None:
                new_fields.append('')
            else:
                new_fields.append(fields[idx])

        return new_fields

import datetime

from tablelinker.core import convertors, params
from tablelinker.core.date_extractor import get_datetime


class DatetimeExtractConvertor(convertors.InputOutputConvertor):
    r"""
    概要
        文字列から日時を抽出し、指定したフォーマットで出力します。

    コンバータ名
        "datetime_extract"

    パラメータ（InputOutputConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_name": 結果を出力する列名
        * "output_col_idx": 分割した結果を出力する列番号または列名
        * "overwrite": 既に値がある場合に上書きするかどうか [True]

    パラメータ（コンバータ固有）
        * "format": 日時フォーマット ["%Y-%m-%d %H:%M:%S"]
        * "default": 日時が抽出できなかった場合の値 [""]

    注釈（InputOutputConvertor 共通）
        - ``output_col_name`` が省略された場合、
          ``input_col_idx`` 列の列名が出力列名として利用されます。
        - ``output_col_idx`` が省略された場合、
          出力列名が存在する列名ならばその列の位置に出力し、
          存在しないならば最後尾に追加します。

    注釈（コンバータ固有）
        - ``format`` は `strftime() と strptime() の書式コード
          <https://docs.python.org/ja/3/library/datetime.html#strftime-and-strptime-format-codes>`_
          のコードで記述してください。
        - ``format`` で指定した項目が抽出できない場合（たとえば ``%Y`` が
          含まれているけれど列の値が "1月1日" で年が分からないなど）、
          ``default`` の値が出力されます。

    サンプル
        「発生時刻」列から発生年月日と時分を抽出します。

        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "datetime_extract",
                "params": {
                    "input_col_idx": "発生時刻",
                    "output_col_name": "発生時刻",
                    "output_col_idx": 0,
                    "format": "%Y-%m-%d %H:%M",
                    "overwrite": true
                }
            }

        - コード例

        .. code-block:: python

            >>> # 「Yahoo 地震速報」より作成
            >>> # https://typhoon.yahoo.co.jp/weather/jp/earthquake/
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     "発生時刻,震源地,マグニチュード,最大震度\n"
            ...     "2023年1月31日 4時15分ごろ,宮城県沖,4.3,2\n"
            ...     "2023年1月30日 18時16分ごろ,富山県西部,3.4,2\n"
            ...     "2023年1月30日 9時32分ごろ,栃木県南部,3.5,1\n"
            ...     "2023年1月29日 21時20分ごろ,神奈川県西部,4.8,3\n"
            ...     "2023年1月29日 12時07分ごろ,茨城県北部,2.9,1\n"
            ...     "2023年1月29日 9時18分ごろ,和歌山県北部,2.7,1\n"
            ...     "2023年1月27日 15時03分ごろ,福島県沖,4.2,2\n"
            ...     "2023年1月27日 13時51分ごろ,岐阜県美濃中西部,2.7,1\n"
            ...     "2023年1月27日 13時49分ごろ,岐阜県美濃中西部,3.0,1\n"
            ...     "2023年1月27日 13時28分ごろ,福島県沖,3.6,1\n"
            ... ))
            >>> table = table.convert(
            ...     convertor="datetime_extract",
            ...     params={
            ...         "input_col_idx": "発生時刻",
            ...         "output_col_name": "発生時刻",
            ...         "output_col_idx": 0,
            ...         "format": "%Y-%m-%dT%H:%M:00",
            ...         "overwrite": True,
            ...     },
            ... )
            >>> table.write()
            発生時刻,震源地,マグニチュード,最大震度
            2023-01-31T04:15:00,宮城県沖,4.3,2
            2023-01-30T18:16:00,富山県西部,3.4,2
            2023-01-30T09:32:00,栃木県南部,3.5,1
            2023-01-29T21:20:00,神奈川県西部,4.8,3
            2023-01-29T12:07:00,茨城県北部,2.9,1
            2023-01-29T09:18:00,和歌山県北部,2.7,1
            2023-01-27T15:03:00,福島県沖,4.2,2
            2023-01-27T13:51:00,岐阜県美濃中西部,2.7,1
            2023-01-27T13:49:00,岐阜県美濃中西部,3.0,1
            2023-01-27T13:28:00,福島県沖,3.6,1

    """

    class Meta:
        key = "datetime_extract"
        name = "日時抽出"
        description = """
        日時表現を抽出します。
        """
        help_text = None
        params = params.ParamSet(
            params.StringParam(
                "format",
                label="日時フォーマット",
                required=False,
                default_value="%Y-%m-%d %H:%M:%S",
                help_text="日時フォーマット"),
            params.StringParam(
                "default",
                label="デフォルト値",
                required=False,
                default_value="",
                help_text="日時が抽出できない場合の値。"),
        )

    def preproc(self, context):
        super().preproc(context)

        self.format = context.get_param("format")
        self.default = context.get_param("default")

    def process_convertor(self, record, context):
        extracted = get_datetime(record[self.input_col_idx])
        if len(extracted["datetime"]) == 0:
            return self.default

        format = self.format
        result = self.default
        for dt in extracted["datetime"]:
            try:
                if dt[0] is None:  # 年が空欄
                    dt[0] = 1
                    for p in ("%y", "%Y", ):
                        if p in format:
                            raise ValueError("年が必要です。")

                if dt[1] is None:  # 月が空欄
                    dt[1] = 1
                    for p in ("%b", "%B", "%m",):
                        if p in format:
                            raise ValueError("月が必要です。")

                if dt[2] is None:  # 日が空欄
                    dt[2] = 1
                    for p in ("%a", "%A", "%w", "%d",):
                        if p in format:
                            raise ValueError("日が必要です。")

                if dt[3] is None:  # 時が空欄
                    dt[3] = 0
                    for p in ("%H", "%I", "%p",):
                        if p in format:
                            raise ValueError("時が必要です。")

                if dt[4] is None:  # 分が空欄
                    dt[4] = 0
                    for p in ("%M",):
                        if p in format:
                            raise ValueError("分が必要です。")

                if dt[5] is None:  # 秒が空欄
                    dt[5] = 0
                    for p in ("%S",):
                        if p in format:
                            raise ValueError("秒が必要です。")

                result = datetime.datetime(
                    year=dt[0],
                    month=dt[1],
                    day=dt[2],
                    hour=dt[3],
                    minute=dt[4],
                    second=dt[5]).strftime(format)

            except ValueError:
                pass

            if result != self.default:
                break

        return result


class DateExtractConvertor(convertors.InputOutputConvertor):
    r"""
    概要
        文字列から日付を抽出し、指定したフォーマットで出力します。

    コンバータ名
        "date_extract"

    パラメータ（InputOutputConvertor 共通）
        * "input_col_idx": 対象列の列番号または列名 [必須]
        * "output_col_name": 結果を出力する列名
        * "output_col_idx": 分割した結果を出力する列番号または列名
        * "overwrite": 既に値がある場合に上書きするかどうか [False]

    パラメータ（コンバータ固有）
        * "format": 日時フォーマット ["%Y-%m-%d"]
        * "default": 日時が抽出できなかった場合の値 [""]

    注釈（InputOutputConvertor 共通）
        - ``output_col_name`` が省略された場合、
          ``input_col_idx`` 列の列名が出力列名として利用されます。
        - ``output_col_idx`` が省略された場合、
          出力列名が存在する列名ならばその列の位置に出力し、
          存在しないならば最後尾に追加します。

    注釈（コンバータ固有）
        - ``format`` は `strftime() と strptime() の書式コード <https://docs.python.org/ja/3/library/datetime.html#strftime-and-strptime-format-codes>`_
          のコードで記述してください。
        - ``format`` 時分秒を指定すると常に 0 になります。
        - ``format`` で指定した項目が抽出できない場合（たとえば ``%Y`` が
          含まれているけれど列の値が "1月1日" で年が分からないなど）、
          ``default`` の値が出力されます。

    サンプル
        「開催期間」列から開催開始日を抽出します。

        - タスクファイル例

        .. code-block :: json

            {
                "convertor": "date_extract",
                "params": {
                    "input_col_idx": "開催期間",
                    "output_col_name": "開催開始日",
                    "output_col_idx": 0,
                    "format": "%Y-%m-%d"
                }
            }

        - コード例

        .. code-block:: python

            >>> # 東京国立博物館「展示・催し物」より作成
            >>> # https://www.tnm.jp/modules/r_calender/index.php
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     "展示名,会場,期間\n"
            ...     "令和5年 新指定 国宝・重要文化財,平成館 企画展示室,2023年1月31日（火） ～ 2023年2月19日（日）\n"
            ...     "特別企画「大安寺の仏像」,本館 11室,2023年1月2日（月・休） ～ 2023年3月19日（日）\n"
            ...     "未来の国宝―東京国立博物館　書画の逸品―,本館 2室,2023年1月31日（火） ～ 2023年2月26日（日）\n"
            ...     "創立150年記念特集　王羲之と蘭亭序,東洋館 8室,2023年1月31日（火） ～ 2023年4月23日（日）\n"
            ...     "創立150年記念特集　近世能狂言面名品選 ー「天下一」号を授かった面打ー,本館 14室,2023年1月2日（月・休） ～ 2023年2月26日（日）\n"
            ... ))
            >>> table = table.convert(
            ...     convertor="date_extract",
            ...     params={
            ...         "input_col_idx": "期間",
            ...         "output_col_name": "開催開始日",
            ...         "output_col_idx": 0,
            ...         "format": "%Y-%m-%d",
            ...     },
            ... )
            >>> table.write()
            開催開始日,展示名,会場,期間
            2023-01-31,令和5年 新指定 国宝・重要文化財,平成館 企画展示室,2023年1月31日（火） ～ 2023年2月19日（日）
            2023-01-02,特別企画「大安寺の仏像」,本館 11室,2023年1月2日（月・休） ～ 2023年3月19日（日）
            2023-01-31,未来の国宝―東京国立博物館　書画の逸品―,本館 2室,2023年1月31日（火） ～ 2023年2月26日（日）
            2023-01-31,創立150年記念特集　王羲之と蘭亭序,東洋館 8室,2023年1月31日（火） ～ 2023年4月23日（日）
            2023-01-02,創立150年記念特集　近世能狂言面名品選 ー「天下一」号を授かった面打ー,本館 14室,2023年1月2日（月・休） ～ 2023年2月26日（日）

    """  # noqa: E501

    class Meta:
        key = "date_extract"
        name = "日付抽出"
        description = """
        日付を抽出します。
        """
        help_text = None
        params = params.ParamSet(
            params.StringParam(
                "format",
                label="日付フォーマット",
                required=False,
                default_value="%Y-%m-%d",
                help_text="日付フォーマット"),
            params.StringParam(
                "default",
                label="デフォルト値",
                required=False,
                default_value="",
                help_text="日付が抽出できない場合の値。"),
        )

    def preproc(self, context):
        super().preproc(context)

        self.format = context.get_param("format")
        self.default = context.get_param("default")

    def process_convertor(self, record, context):
        extracted = get_datetime(record[self.input_col_idx])
        if len(extracted["datetime"]) == 0:
            return self.default

        format = self.format
        result = self.default
        for dt in extracted["datetime"]:
            try:
                if dt[0] is None:  # 年が空欄
                    dt[0] = 1
                    for p in ("%y", "%Y", ):
                        if p in format:
                            raise ValueError("年が必要です。")

                if dt[1] is None:  # 月が空欄
                    dt[1] = 1
                    for p in ("%b", "%B", "%m",):
                        if p in format:
                            raise ValueError("月が必要です。")

                if dt[2] is None:  # 日が空欄
                    dt[2] = 1
                    for p in ("%a", "%A", "%w", "%d",):
                        if p in format:
                            raise ValueError("日が必要です。")

                result = datetime.date(
                    year=dt[0],
                    month=dt[1],
                    day=dt[2]).strftime(format)

            except ValueError:
                pass

            if result != self.default:
                break

        return result

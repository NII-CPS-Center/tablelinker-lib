import codecs
from collections import OrderedDict
import csv
import io
from logging import getLogger
import math
import os
import re
import sys
import tempfile
from typing import List, Optional, Union

import pandas as pd
from pandas.core.frame import DataFrame

from ..convertors import basics as basic_convertors
from .context import Context
from .convertors import convertor_find_by
from .input import CsvInputCollection
from .mapping import ItemsPair
from .output import CsvOutputCollection
from .task import Task


logger = getLogger(__name__)

basic_convertors.register()  # コンバータリストを初期化
session_tmpdir = None  # セッション内で有効な一時ディレクトリ


def escape_encoding(exc):
    """
    文字エンコーディングの処理中に UnicodeDecodeError が
    発生した場合のエラーハンドラ。
    https://docs.python.org/ja/3.5/library/codecs.html#codecs.register_error

    変換できなかった文字を '??' に置き換えます。
    """
    logger.warning(str(exc))
    return ('??', exc.end)


def NamedTemporaryFile(*args, **kwargs):
    """
    セッション内で有効な一時ディレクトリの下に、名前付き一時ファイルを作ります。

    Notes
    -----
    - パラメータは ``tempfile.NamedTemporaryFile`` と同じです。
      ただし ``dir`` パラメータは指定できません。
    - With コンテキストでは利用できません。
    """
    global session_tmpdir

    if "dir" in kwargs:
        del kwargs["dir"]

    if session_tmpdir is None:
        session_tmpdir = tempfile.TemporaryDirectory(prefix="table_")
        logger.debug("一時ディレクトリ '{}' を作成しました。".format(
            session_tmpdir.name))

    tmpf = tempfile.NamedTemporaryFile(
        *args, dir=session_tmpdir.name, **kwargs)
    logger.debug("一時ファイル '{}' を作成しました。".format(
        tmpf.name))

    return tmpf


class Table(object):
    r"""
    表形式データを管理するクラスです。

    Parameters
    ----------
    file: File-like, Path-like
        このテーブルが管理する入力表データファイルのパス、
        または file-like オブジェクト。
    data: str, bytes
        CSV 文字列。 file を指定した場合、 data は無視されます。
    sheet: str, None
        入力ファイルが Excel の場合など、複数の表データを含む場合に
        対象を指定するためのシート名。省略された場合は最初の表。
    is_tempfile: bool
        入力表データファイルが一時ファイルかどうかを表すフラグ。
        True の場合、オブジェクトが消滅するときに file が
        指すパスにあるファイルも削除します。
    skip_cleaning: bool
        表データを読み込む際にクリーニングをスキップするか
        どうかを指定するフラグ。
        True を指定した場合、 file で指定したファイルは
        文字エンコーディングが UTF-8（BOM無し）、区切り文字はカンマ、
        先頭部分に説明などの余計な行が含まれていない
        CSV ファイルである必要があります。

    Attributes
    ----------
    file: File-like, Path-like
        パラメータ参照。 data で初期化した場合には、
        その内容を保存した一時ファイル名を参照します。
    sheet: str, optional
        パラメータ参照。
    is_tempfile: bool
        パラメータ参照。
    skip_cleaning: bool
        パラメータ参照。
    filetype: str
        入力表データファイルの種別。 CSV の場合は ``csv``、
        Excel の場合は ``excel`` になります。
    headers: List[str, datatype]
        表データの列ごとの見出しとデータ型を持つリストです。
        ``open()`` を実行した時にファイルの内容から設定します。
        実行前は None です。

    Examples
    --------
    >>> from tablelinker import Table
    >>> table = Table("sample/datafiles/hachijo_sightseeing.csv")
    >>> table.write(lines=2)
    観光スポット名称,所在地,緯度,経度,座標系,説明,八丈町ホームページ記載
    ホタル水路,,33.108218,139.80102,JGD2011,八丈島は伊豆諸島で唯一、水田耕作がなされた島で鴨川に沿って水田が残っています。ホタル水路は、鴨川の砂防とともに平成元年につくられたもので、毎年6月から7月にかけてホタルの光が美しく幻想的です。,http://www.town.hachijo.tokyo.jp/kankou_spot/mitsune.html#01

    Examples
    --------
    >>> from tablelinker import Table
    >>> table = Table(data="国名,3文字コード\nアメリカ合衆国,USA\n日本,JPN\n")
    >>> table.write(lineterminator="\n")
    国名,3文字コード
    アメリカ合衆国,USA
    日本,JPN

    Notes
    -----
    - Excel ファイルのシートを開きたい場合、
      ``sheet`` オプションでシート名を指定します。 ::

          table = Table(ファイル名, sheet=シート名)

    - ``is_tempfile`` に True を指定した場合、
      オブジェクト削除時に ``file`` が指すファイルも削除されます。
    - CSV データが UTF-8、カンマ区切りの CSV であることが
      分かっている場合、 ``skip_cleaning`` に True を指定することで
      クリーニング処理をスキップして高速に処理できます。

    """

    codecs.register_error('escape_encoding', escape_encoding)

    def __init__(
            self,
            file: Optional[os.PathLike] = None,
            data: Union[str, bytes, None] = None,
            sheet: Optional[str] = None,
            is_tempfile: bool = False,
            skip_cleaning: bool = False):
        """
        オブジェクトを初期化します。

        Notes
        -----
        ファイルは開きません。
        """
        self.file = file
        self.sheet = sheet
        self.is_tempfile = is_tempfile
        self.skip_cleaning = skip_cleaning
        self.filetype = "csv"
        self.headers = None
        self._reader = None

        if file is None and data is None:
            raise RuntimeError("file と data のどちらかを指定してください。")

        # 文字列・バイト列が渡された場合は一時ファイルに保存する
        if self.file is None:
            if isinstance(data, bytes):
                f = NamedTemporaryFile(mode="wb", delete=False)
            elif isinstance(data, str):
                f = NamedTemporaryFile(mode="w", delete=False)

            f.write(data)
            self.file = f.name
            self.is_tempfile = True

    def __del__(self):
        """
        オブジェクトを削除する前に呼び出されます。

        self.is_tempfile が True で、かつ self.file が指す
        ファイルが残っている場合、先にファイルを消去します。
        """
        self.close()
        if self.is_tempfile is True and \
                os.path.exists(self.file):
            os.remove(self.file)
            logger.debug("一時ファイル '{}' を削除しました".format(
                self.file))

    def __enter__(self):
        if self._reader is None:
            self.open()

        return self

    def __iter__(self):
        return self

    def __next__(self):
        row = self._reader.__next__()
        return row

    def __exit__(self, exception_type, exception_value, traceback):
        try:
            self._reader.__exit__(
                exception_type, exception_value, traceback)
        except AttributeError:
            # _reader が先に削除されている場合は例外を無視する
            pass

        self.close()

    def open(
            self,
            as_dict: bool = False,
            adjust_datatype: bool = False,
            **kwargs):
        """
        表データを開きます。既に開いている場合、先頭に戻します。

        Parameters
        ----------
        as_dict: bool [False]
            True が指定された場合、 csv.DictReader
            オブジェクトを返します。
        adjust_datatype: bool [False]
            True が指定された場合、列ごとにデータ型を推定して
            その型に合わせた値を返します。
        kwargs: dict
            csv.reader, csv.DictReader に渡すその他のパラメータ。

        Returns
        -------
        Table
            自分自身を返します。
            Table はジェネレータ・イテレータインタフェースを
            備えているので、サンプルのように for 文で行を順番に
            読みだしたり、 with 構文でバインドすることができます。

        Examples
        --------
        >>> from tablelinker import Table
        >>> table = Table("sample/datafiles/hachijo_sightseeing.csv")
        >>> reader = table.open()
        >>> for row in reader:
        ...     print(",".join(row[0:4]))
        ...
        観光スポット名称,所在地,緯度,経度
        ホタル水路,,33.108218,139.80102
        登龍峠展望,,33.113154,139.835245
        八丈富士,,33.139168,139.762187
        永郷展望,,33.153559,139.747501
        ...

        Examples
        --------
        >>> from tablelinker import Table
        >>> table = Table("sample/datafiles/hachijo_sightseeing.csv")
        >>> with table.open(as_dict=True) as dictreader:
        ...     for row in dictreader:
        ...         print(",".join([row[x] for x in [
        ...             "観光スポット名称", "所在地", "経度", "緯度"]]))
        ...
        ホタル水路,,139.80102,33.108218
        登龍峠展望,,139.835245,33.113154
        八丈富士,,139.762187,33.139168
        永郷展望,,139.747501,33.153559
        ...

        Examples
        --------
        >>> import json
        >>> from tablelinker import Table
        >>> table = Table("sample/datafiles/hachijo_sightseeing.csv")
        >>> with table.open(adjust_datatype=True) as reader:
        ...     for row in reader:
        ...         print(json.dumps(row[0:4], ensure_ascii=False))
        ...
        ["観光スポット名称", "所在地", "緯度", "経度"]
        ["ホタル水路", "", 33.108218, 139.80102]
        ["登龍峠展望", "", 33.113154, 139.835245]
        ["八丈富士", "", 33.139168, 139.762187]
        ["永郷展望", "", 33.153559, 139.747501]
        ...

        Notes
        -----
        - CSV、タブ区切りテキスト、 Excel に対応しています。
        - 表データの確認とクリーニングは、このメソッドが
          呼ばれたときに実行されます。
        """
        self.filetype = None
        if not self.skip_cleaning:
            # エクセルファイルとして読み込む
            try:
                if self.sheet is None:
                    df = pd.read_excel(self.file, sheet_name=0)
                else:
                    try:
                        df = pd.read_excel(self.file, sheet_name=self.sheet)
                    except ValueError:
                        if re.match(r'^\d+', self.sheet):
                            self.sheet = int(self.sheet)
                        df = pd.read_excel(self.file, sheet_name=self.sheet)

                data = df.to_csv(index=False)
                self._reader = CsvInputCollection(
                    file_or_path=io.StringIO(data),
                    skip_cleaning=False).open(
                        as_dict=as_dict,
                        adjust_datatype=adjust_datatype,
                        **kwargs)

                self.filetype = "excel"

            except ValueError as e:
                if str(e).lower().startswith(
                        "excel file format cannot be determined"):
                    pass  # Excel ファイルではないので CSV として開く
                elif self.sheet is not None:
                    logger.error(
                        "対象にはシート '{}' は含まれていません。".format(
                            self.sheet))
                    raise ValueError("Invalid sheet name.")

        if self.filetype is None:
            # CSV 読み込み
            self._reader = CsvInputCollection(
                self.file,
                skip_cleaning=self.skip_cleaning).open(
                    as_dict=as_dict,
                    adjust_datatype=adjust_datatype,
                    **kwargs)

            self.filetype = "csv"

        return self

    def close(self):
        """
        ファイルを閉じます。開いていない場合には何もしません。
        """
        if self._reader is not None:
            del self._reader

        self._reader = None

    def get_reader(self):
        """
        管理している表データへの reader オブジェクトを取得します。

        Returns
        -------
        csv.reader, csv.DictReader
            reader オブジェクト。ただし ``open()`` を実行する前は
            ``None`` を返します。

        """
        if self._reader is not None:
            return self._reader.get_reader()

        return None

    @classmethod
    def useExtraConvertors(cls) -> None:
        """
        拡張コンバータを利用することを宣言します。

        Notes
        -----
        - ``tablelinker.useExtraConvertors()`` と等価です。

        """
        import tablelinker
        tablelinker.useExtraConvertors()

    def save(self, path: os.PathLike, encoding="utf-8", **fmtparams):
        """
        Table オブジェクトが管理する表データを csv.writer を利用して
        指定したパスのファイルに保存します。

        Parameters
        ----------
        path: os.PathLike
            保存する CSV ファイルのパス。
        encoding: str ["utf-8"]
            テキストエンコーディング。
        fmtparams: dict
            csv.writer に渡すフォーマットパラメータ。

        Examples
        --------
        >>> import csv
        >>> from tablelinker import Table
        >>> table = Table("sample/datafiles/hachijo_sightseeing.csv")
        >>> table.save("hachijo_sightseeing_utf8.csv", quoting=csv.QUOTE_ALL)

        """
        with self.open() as reader, \
                open(path, mode="w", newline="",
                     encoding=encoding, errors="escape_encoding") as f:
            writer = csv.writer(f, **fmtparams)
            for row in reader:
                writer.writerow(row)

    def merge(self, target: Union[str, os.PathLike, "Table"]):
        """
        Table オブジェクトが管理する表データを、
        指定したファイルまたは Table の末尾に結合 (merge) します。

        Parameters
        ----------
        target: os.PathLike, Table
            結合先の CSV ファイルのパスまたは Table。

        Examples
        --------
        >>> import shutil
        >>> from tablelinker import Table
        >>> _ = shutil.copy("katsushika_tourism.csv", "tourism.csv")
        >>> table_src = Table("shimabara_tourism.csv")
        >>> table_src.merge("tourism.csv")  # ファイルの末尾に結合
        >>> with Table("tourism.csv").open() as reader:
        ...     nlines = 0
        ...     for _ in reader:
        ...         nlines += 1
        ...
        >>> nlines
        32

        Examples
        --------
        >>> import shutil
        >>> from tablelinker import Table
        >>> _ = shutil.copy("katsushika_tourism.csv", "tourism.csv")
        >>> table_src = Table("shimabara_tourism.csv")
        >>> table_dst = Table("tourism.csv")
        >>> table_src.merge(table_dst)  # 他のテーブルの末尾に結合
        >>> with table_dst.open() as reader:
        ...     nlines = 0
        ...     for _ in reader:
        ...         nlines += 1
        ...
        >>> nlines
        32

        Notes
        -----
        - 結合先ファイルの列の順番に合わせて並べ替えます。
        - 文字エンコーディングも結合先ファイルに合わせます。
        - 見出し行は出力しません。

        """
        if not isinstance(target, Table):
            # 結合先ファイルの存在チェック
            if not os.path.exists(target):
                logger.debug((
                    "結合先のファイル '{}' が存在しないため、"
                    "そのまま保存します。").format(target))
                return self.save(target)

            target_table = Table(target, skip_cleaning=False)
        else:
            target_table = target

        target_delimiter = ","
        target_encoding = "UTF-8"
        with target_table.open() as target_reader:
            if target_table.filetype != "csv":
                logger.error(
                    "結合先のファイル '{}' は CSV ではありません。".format(
                        target_table.file))
                raise RuntimeError("The merged file must be a CSV.")

            cc = target_table._reader._reader  # CSVCleaner
            target_delimiter = cc.delimiter
            target_encoding = cc.encoding
            target_header = target_reader.__next__()

        target_table.close()  # 結合先ファイルを書き込み用に一度閉じる

        # 結合先のファイルに列の順番をそろえる
        try:
            reordered = self.convert(
                convertor="reorder_cols",
                params={"column_list": target_header})
        except ValueError as e:
            logger.error(
                "結合先のファイルと列を揃える際にエラー。({})".format(
                    e))
            raise ValueError(e)

        # 結合先のファイルに追加出力
        with reordered.open() as reader, \
                open(target_table.file, mode="a", newline="",
                     encoding=target_encoding, errors="escape_encoding") as f:
            writer = csv.writer(f, delimiter=target_delimiter)
            reader.__next__()  # ヘッダ行をスキップ
            for row in reader:
                writer.writerow(row)

    def write(
            self,
            lines: int = -1,
            file=None,
            skip_header: bool = False,
            **fmtparams):
        """
        入力 CSV データを csv.writer を利用して
        指定したファイルオブジェクトに出力します。

        Parameters
        ----------
        lines: int [default:-1]
            出力する最大行数。
            省略された場合、または負の場合は全ての行を出力します。
        file: File-like オブジェクト [default: None]
            出力先のファイルオブジェクト。
            省略された場合または None が指定された場合は標準出力。
        skip_header: bool [default: False]
            見出し行をスキップする場合は True を指定します。
        fmtparams: dict
            csv.writer に渡すフォーマットパラメータ。

        Examples
        --------
        >>> import csv
        >>> from tablelinker import Table
        >>> table = Table("sample/datafiles/hachijo_sightseeing.csv")
        >>> with open("hachijo_2.csv", "w", newline="") as f:
        ...     table.write(lines=2, file=f, quoting=csv.QUOTE_ALL)
        ...

        """
        if file is None:
            file = sys.stdout

        with self.open() as reader:
            writer = csv.writer(file, **fmtparams)
            if skip_header:
                reader.__next__()

            for n, row in enumerate(reader):
                if n == lines:
                    break

                writer.writerow(row)

    def to_str(self, **kwargs):
        """
        write() を利用して、クリーンな CSV 文字列を返します。

        Parameters
        ----------
        **kwargs: dict
            write() に渡すパラメータを指定します。

        Returns
        -------
        str
            CSV 文字列を含む文字列。

        Notes
        -----
        このメソッドはメモリ上に表データのコピーを作成します。
        """
        buf = io.StringIO()
        self.write(file=buf, **kwargs)

        return buf.getvalue()

    def apply(self, tasks: Union[Task, List[Task]]) -> 'Table':
        r"""
        テーブルが管理する表データにタスクを適用して変換し、
        変換結果を管理する新しい Table オブジェクトを返します。

        Parameters
        ----------
        tasks: Task, List[Task]
            適用するタスク、またはタスクのリスト。

        Returns
        -------
        Table
            変換結果を管理する Table オブジェクト。

        Examples
        --------
        >>> from tablelinker import Table, Task
        >>> table = Table("ma030000.csv")
        >>> table.write(lines=2)
        ,人口,出生数,死亡数,（再掲）,,自　然,死産数,,,周産期死亡数,,,婚姻件数,離婚件数
        ,,,,乳児死亡数,新生児,増減数,総数,自然死産,人工死産,総数,22週以後,早期新生児,,
        >>> table.apply(Task.from_files("task1.json")).write(lines=2)
        地域,人口,出生数,死亡数,（再掲）,,自　然,死産数,,,周産期死亡数,,,婚姻件数,離婚件数
        ,,,,乳児死亡数,新生児,増減数,総数,自然死産,人工死産,総数,22週以後,早期新生児,,
        >>> tasks = Task.from_files(["task1.json", "task2.json"])
        >>> table.apply(tasks).write(lines=3)
        地域,人口,出生数,死亡数,（再掲）乳児死亡数,（再掲）新生児死亡数,自　然増減数,死産数総数,死産数自然死産,死産数人工死産,周産期死亡数総数,周産期死亡数22週以後の死産数,周産期死亡数早期新生児死亡数,婚姻件数,離婚件数
        全　国,123398962,840835,1372755,1512,704,-531920,17278,8188,9090,2664,2112,552,525507,193253
        01 北海道,5188441,29523,65078,59,25,-35555,728,304,424,92,75,17,20904,9070

        """  # noqa: E501
        if isinstance(tasks, Task):  # タスクが一つの場合
            tasks = [tasks]

        table = self
        for task in tasks:
            if task.note:
                logger.info(task)
            else:
                logger.debug("Running {}".format(task))

            table = table.convert(
                convertor=task.convertor,
                params=task.params)

            if task.note:
                logger.info("{} 完了".format(task.convertor))

        return table

    def convert(
            self,
            convertor: str,
            params: dict,
            output: Optional[os.PathLike] = None) -> 'Table':
        r"""
        テーブルが管理する表データにコンバータを適用して変換し、
        変換結果を管理する新しい Table オブジェクトを返します。

        Parameters
        ----------
        convertor: str
            適用するコンバータ名 (例: 'rename_col')。
        params: dict
            コンバータに渡すパラメータ名・値の辞書。
            例: {"input_col_idx": 1, "new_col_name": "番号"}
        output: Path-like, optional
            出力結果を保存する CSV ファイル名を指定します。
            省略した場合には一時ファイルを作成します。
            途中経過を保存したい場合に指定してください。
            ここで作成したファイルは変換処理完了後も削除されません。

        Returns
        -------
        Table
            変換結果を管理する Table オブジェクト。

        Examples
        --------
        >>> from tablelinker import Table
        >>> table = Table("sample/datafiles/hachijo_sightseeing.csv")
        >>> table.write(lines=1)
        観光スポット名称,所在地,緯度,経度,座標系,説明,八丈町ホームページ記載
        >>> table = table.convert(
        ...     convertor="rename_col",
        ...     params={"input_col_idx":0, "output_col_name":"名称"},
        ... )
        >>> table.write(lines=1)
        名称,所在地,緯度,経度,座標系,説明,八丈町ホームページ記載

        Notes
        -----
        - 変換結果はテンポラリディレクトリ (``/tmp/`` など) の下に
          ``table_`` から始まるファイル名を持つファイルに出力されます。
        - このメソッドが返す Table オブジェクトが削除される際に、
          変換結果ファイルも自動的に削除されます。
        - ただしエラーや中断により途中で停止した場合には、
          変換結果ファイルが残る場合があります。
        """
        self.open()
        if output is not None:
            csv_out = output
        else:
            csv_out = NamedTemporaryFile(
                delete=False,
                prefix='table_').name

        input = self._reader
        output = CsvOutputCollection(csv_out)
        conv = convertor_find_by(convertor)
        if conv is None:
            # 拡張コンバータも読み込み、もう一度確認する
            self.useExtraConvertors()
            conv = convertor_find_by(convertor)

        if conv is None:
            raise ValueError("コンバータ '{}' は未登録です".format(
                convertor))

        with Context(
                convertor=conv,
                convertor_params=params,
                input=input,
                output=output) as context:
            try:
                conv().process(context)
                logger.debug((
                    "ファイル '{}' にコンバータ '{}' を適用し"
                    "一時ファイル '{}' に出力しました。").format(
                    self.file, convertor, csv_out))
                new_table = Table(
                    csv_out,
                    is_tempfile=(output is None),
                    skip_cleaning=True)
                return new_table

            except RuntimeError as e:
                if output is None:
                    os.remove(csv_out)
                    logger.debug((
                        "ファイル '{}' にコンバータ '{}' を適用中、"
                        "エラーのため一時ファイル '{}' を削除しました。").format(
                        self.file, convertor, csv_out))
                else:
                    logger.debug((
                        "ファイル '{}' にコンバータ '{}' を適用中、"
                        "エラーが発生しました。途中結果は '{}'"
                        "にあります。").format(
                            self.file, convertor, csv_out))

                raise e

    def mapping(
            self,
            template: "Table",
            threshold: Optional[int] = None) -> dict:
        """
        他のテーブル（テンプレート）に変換するための
        対応表を生成します。

        Parameters
        -----------
        template: Table
            変換対象のテーブルオブジェクト。
        threshold: int, optional
            一致する列と判定する際のしきい値。0-100 で指定し、
            0 の場合が最も緩く、100の場合は完全一致した場合しか
            対応しているとみなしません。

        Returns
        -------
        dict
            キーに変換先テーブルの列名、値にその列に対応すると
            判定された自テーブルの列名を持つ dict を返します。

        Notes
        -----
        結果の dict はコンバータ mapping_cols の column_map
        パラメータにそのまま利用できます。

        .. code-block: python

            map = table.mapping(template)
            mapped_table = table.convert(
                convertor="mapping_cols",
                params={"column_map": map},
            )

        """
        threshold = 20 if threshold is None else threshold  # デフォルトは 20

        # テンプレート CSV の見出し行を取得
        with template.open() as reader:
            template_headers = reader.__next__()

        return self.mapping_with_headers(
            headers=template_headers,
            threshold=threshold)

    def mapping_with_headers(
            self,
            headers: List[str],
            threshold: Optional[int] = None) -> dict:
        """
        テンプレートの見出し列に一致するように変換するための
        対応表を生成します。

        Parameters
        -----------
        headers: List[str]
            テンプレートの見出し列。
        threshold: int, optional
            一致する列と判定する際のしきい値。0-100 で指定し、
            0 の場合が最も緩く、100の場合は完全一致した場合しか
            対応しているとみなしません。

        Returns
        -------
        dict
            キーに変換先テーブルの列名、値にその列に対応すると
            判定された自テーブルの列名を持つ dict を返します。

        Notes
        -----
        結果の dict はコンバータ mapping_cols の column_map
        パラメータにそのまま利用できます。

        .. code-block: python

            map = table.mapping(template)
            mapped_table = table.convert(
                convertor="mapping_cols",
                params={"column_map": map},
            )

        """
        threshold = 20 if threshold is None else threshold  # デフォルトは 20
        logger.debug("しきい値： {}".format(threshold))

        # 自テーブルの見出し行を取得
        with self.open() as reader:
            my_headers = reader.__next__()

        # 項目マッピング
        pair = ItemsPair(headers, my_headers)
        mapping = OrderedDict()
        for result in pair.mapping():
            output, header, score = result
            logger.debug("対象列：{}, 対応列：{}, 一致スコア:{:3d}".format(
                output, header, int(score * 100.0)))
            if output is None:
                # マッピングされなかったカラムは除去
                continue

            if header is None:
                mapping[output] = None
            elif math.ceil(score * 100.0) < threshold:
                mapping[output] = None
            else:
                mapping[output] = header

        return dict(mapping)

    @classmethod
    def fromPandas(cls, df: DataFrame) -> "Table":
        r"""
        Pandas DataFrame から Table オブジェクトを作成します。

        Parameters
        ----------
        df: pandas.core.frame.DataFrame
            表データを持つ Pandas DataFrame オブジェクト。

        Returns
        -------
        Table
            新しい Table オブジェクト。

        Examples
        --------
        >>> from tablelinker import Table
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     "国名":["アメリカ合衆国","日本","中国"],
        ...     "3文字コード":["USA","JPN","CHN"],
        ... })
        >>> table = Table.fromPandas(df)
        >>> table.write(lineterminator="\n")
        国名,3文字コード
        アメリカ合衆国,USA
        日本,JPN
        中国,CHN

        Notes
        -----
        このメソッドは、一度 DataFrame のすべてのデータを
        CSV ファイル（一時ファイル）に出力します。
        """
        table = None
        f = NamedTemporaryFile(mode="w+b", delete=False)
        df.to_csv(f, index=False)
        table = Table(
            f.name,
            is_tempfile=True,
            skip_cleaning=True)

        return table

    def toPandas(self) -> DataFrame:
        r"""
        Table オブジェクトから Pandas DataFrame を作成します。

        Returns
        -------
        pandas.core.frame.DataFrame

        Examples
        --------
        >>> import pandas as pd
        >>> from tablelinker import Table
        >>> table = Table(data="国名,3文字コード\nアメリカ合衆国,USA\n日本,JPN\n")
        >>> df = table.toPandas()
        >>> df.columns
        Index(['国名', '3文字コード'], dtype='object')

        """
        with self.open(as_dict=True, adjust_datatype=True) as reader:
            df = pd.DataFrame.from_records(reader)

        return df

    @classmethod
    def fromPolars(cls, df) -> Optional["Table"]:
        r"""
        Polars DataFrame から Table オブジェクトを作成します。

        Parameters
        ----------
        df: polars.DataFrame
            表データを持つ Polars DataFrame オブジェクト。

        Returns
        -------
        Table
            新しい Table オブジェクト。

        Examples
        --------
        >>> from tablelinker import Table
        >>> import polars as pl
        >>> df = pl.DataFrame({
        ...     "国名":["アメリカ合衆国","日本","中国"],
        ...     "3文字コード":["USA","JPN","CHN"],
        ... })
        >>> df.columns
        ['国名', '3文字コード']
        >>> table = Table.fromPolars(df)
        >>> table.write(lineterminator="\n")
        国名,3文字コード
        アメリカ合衆国,USA
        日本,JPN
        中国,CHN

        Notes
        -----
        このメソッドは、一度 DataFrame のすべてのデータを
        CSV ファイル（一時ファイル）に出力します。
        """
        try:
            import polars  # noqa: F401
        except ModuleNotFoundError:
            logger.error("Polars がインストールされていません。")
            return None

        table = None
        f = NamedTemporaryFile(mode="w+b", delete=False)
        df.write_csv(f.name)
        table = Table(
            f.name,
            is_tempfile=True,
            skip_cleaning=True)

        return table

    def toPolars(self):
        r"""
        Table オブジェクトから Polars DataFrame を作成します。

        Returns
        -------
        polars.DataFrame

        Examples
        --------
        >>> import polars as pl
        >>> from tablelinker import Table
        >>> table = Table(data="国名,3文字コード\nアメリカ合衆国,USA\n日本,JPN\n")
        >>> df = table.toPolars()
        >>> df.columns
        ['国名', '3文字コード']

        Notes
        -----
        - Table オブジェクトが明示的にクリーニング不要（skip_cleaning = True）
          な CSV ファイルを参照している場合、 Polars DataFrame も
          直接そのファイルを開きます。
        - それ以外の場合は、 一度 Table が参照しているすべてのデータを
          メモリに読み込んでから Polars DataFrame に渡すため、
          ファイルサイズが大きい場合には時間がかかることがあります。

        """
        try:
            import polars as pl
        except ModuleNotFoundError:
            logger.error("Polars がインストールされていません。")
            return None

        if self.skip_cleaning:
            # クリーニング不要な CSV ファイルを開いている場合、
            # そのまま Polars でファイルを開く。
            df = pl.read_csv(self.file)
        else:
            # メモリに読み込んでから渡す。
            buffer = io.StringIO()
            self.write(file=buffer)
            df = pl.read_csv(buffer)

        return df

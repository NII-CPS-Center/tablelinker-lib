import csv
import io
from logging import getLogger
import re

from .csv_cleaner import CSVCleaner

logger = getLogger(__name__)


class InputCollection(object):
    """
    データセット(Array, File)
    """

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def open(self):
        pass

    def close(self):
        pass

    def reset(self):
        pass

    def next(self):
        return None

    def encode(self):
        return []

    @classmethod
    def decode(cls, args):
        pass

    @classmethod
    def key(cls):
        return cls.__name__


class ArrayInputCollection(InputCollection):
    def __init__(self, array):
        self._array = array
        self.reset()

    def reset(self):
        self._current = 0

    def next(self):
        if self._current == len(self._array):
            raise StopIteration()
        value = self._array[self._current]
        self._current += 1
        return value

    def encode(self):
        return [self._array]

    @classmethod
    def decode(cls, args):
        return cls(args[0])


class CsvInputCollection(InputCollection):

    _int_pattern = r'[\-\+]?([1-9]\d{0,2}(,\d{3})*|[1-9]\d+|0)'
    _float_pattern = fr'{_int_pattern}(\.\d+)?'
    _re_int = re.compile(rf'^{_int_pattern}$')
    _re_float = re.compile(rf'^{_float_pattern}$')

    def __init__(self, file_or_path, skip_cleaning=False):
        # file_or_path パラメータが File-like か PathLike か判別
        if all(hasattr(file_or_path, attr)
               for attr in ('seek', 'close', 'read')):
            # File-like オブジェクトの場合
            self.fp = file_or_path
            self.path = None
            logger.debug("Detect file-like object.")
        else:
            self.fp = None
            self.path = file_or_path
            logger.debug("Detect path-like object.")

        self.skip_cleaning = skip_cleaning
        self.as_dict = False
        self.adjust_datatype = False
        self.headers = None
        self._reader = None

    def get_header_info(self):
        """
        管理している表データの先頭 20 行を読み込み、
        列見出しとデータタイプを推定します。

        Returns
        -------
        list:
            [列見出し, データ型] のリストで、データ型は
            int, float, str のいずれかになります。

        Notes
        -----
        - このメソッドを呼び出すと、ファイルの先頭に巻き戻されます。
        """
        with self as reader:
            header_titles = reader.__next__()
            headers = [[x, 0, 0, 0] for x in header_titles]
            for i, row in enumerate(reader):
                if i == 20:
                    break

                if isinstance(row, dict):
                    row = list(row.values())

                for i in range(len(header_titles)):
                    if len(row) <= i:
                        continue

                    if self._re_int.match(row[i]):
                        headers[i][1] += 1
                    elif self._re_float.match(row[i]):
                        headers[i][2] += 1
                    else:
                        headers[i][3] += 1

        detected_headers = []
        for header in headers:
            if header[1] >= header[2] and header[1] >= header[3]:
                data_type = int
            elif header[2] >= header[1] and header[2] >= header[3]:
                data_type = float
            else:
                data_type = str

            detected_headers.append([header[0], data_type])

        self.close()
        return detected_headers

    def datatype_wrapper(self, as_dict: bool = False):
        """
        列ごとに推定された型に変更したリストを返す
        ラッパーリソースを返します。
        """
        self.close()
        with self.open(as_dict=as_dict) as reader:
            for row in reader:
                output = row[:]
                for i, val in enumerate(row):
                    try:
                        if self.headers[i][1] == int:
                            output[i] = int(val.replace(',', ''))
                        elif self.headers[i][1] == float:
                            output[i] = float(val.replace(',', ''))
                    except ValueError:
                        pass  # 数値ではないので文字列のまま

                yield output

    def __enter__(self):
        if self._reader is None:
            self._open()

        return self

    def _open(
            self,
            as_dict: bool = False,
            adjust_datatype: bool = False,
            **kwargs):
        """
        ファイルを開く。
        skip_cleaning が False の場合、コンテンツを読み込み
        CSVCleaner で整形したバッファを開く。
        """
        reader = csv.reader
        if as_dict is True:
            reader = csv.DictReader

        if self.skip_cleaning:
            # ファイルをそのまま開く
            if self.path is not None:
                if self.fp is not None:
                    self.fp.close()

                self.fp = open(self.path, "r", newline="")
                self._reader = reader(self.fp, **kwargs)
            else:
                self.fp.seek(0)
                top = self.fp.read(1)
                self.fp.seek(0)
                if isinstance(top, bytes):
                    # バイトストリーム
                    stream = io.TextIOWrapper(
                        self.fp, encoding="utf-8")
                    self._reader = reader(stream, **kwargs)
                else:
                    # テキストストリーム
                    self._reader = reader(self.fp, **kwargs)
        else:
            # ファイルをクリーニングしながら読み込む
            if self.path is not None:
                self.fp = open(self.path, "rb")
            else:
                self.fp.seek(0)

            # クリーニング
            self._reader = CSVCleaner(self.fp)
            self._reader.open(as_dict=as_dict, **kwargs)

        return self

    def open(
            self,
            as_dict: bool = False,
            adjust_datatype: bool = False,
            **kwargs):
        """
        ファイルを開く。
        skip_cleaning が False の場合、コンテンツを読み込み
        CSVCleaner で整形したバッファを開く。
        """
        if adjust_datatype:
            self.headers = self.get_header_info()

        self.as_dict = as_dict
        self.adjust_datatype = adjust_datatype

        return self._open(
            as_dict=as_dict,
            adjust_datatype=adjust_datatype,
            **kwargs)

    def close(self):
        if self._reader is not None:
            del self._reader
            self._reader = None

        if self.path is not None:
            if self.fp is not None:
                self.fp.close()
        else:
            self.fp.seek(0)

    def get_reader(self):
        if self._reader is not None:
            return self._reader

        return False

    def reset(self):
        self.open(
            as_dict=self.as_dict,
            adjust_datatype=self.adjust_datatype)

    def next(self):
        row = self._reader.__next__()
        if not self.adjust_datatype:
            return row

        for i, val in enumerate(row):
            try:
                if self.headers[i][1] == int:
                    row[i] = int(val.replace(',', ''))
                elif self.headers[i][1] == float:
                    row[i] = float(val.replace(',', ''))
            except ValueError:
                pass  # 数値ではないので文字列のまま

        return row

    def encode(self):
        return [self.filepath]

    @classmethod
    def decode(cls, args):
        return cls(args[0])

    def __exit(self, type_, value, traceback):
        if self._reader is not None:
            self._reader.__exit__()

        if self.path is not None and self.fp is not None:
            self.fp.close()


INPUTS = [ArrayInputCollection, CsvInputCollection]

INPUTS_DICT = {}
for i in INPUTS:
    INPUTS_DICT[i.key()] = i


def register_input(input_class):
    INPUTS.append(input_class)
    INPUTS_DICT[input_class.key()] = input_class


def input_find_by(name):
    return INPUTS_DICT.get(name)


def encode_input(input):
    return [input.key(), input.encode()]


def decode_input(input):
    return input_find_by(input[0]).decode(input[1])

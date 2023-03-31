import csv

from .input import ArrayInputCollection, CsvInputCollection


class OutputCollection(object):
    """
    データセット(Array, File)
    """

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.close()

    def open(self):
        pass

    def append(self, value):
        pass

    def close(self):
        pass

    def get_data(self):
        return None

    def getInput(self):
        return None

    def encode(self):
        return []

    @classmethod
    def decode(cls, args):
        pass

    @classmethod
    def key(cls):
        return cls.__name__


class ArrayOutputCollection(OutputCollection):
    def __init__(self, array=None):
        self._array = [] if array is None else array

    def append(self, value):
        self._array.append(value)

    def get_data(self):
        return self._array

    def getInput(self):
        return ArrayInputCollection(self._array)

    def encode(self):
        return [self._array]

    @classmethod
    def decode(cls, args):
        return cls(args[0])


class CsvOutputCollection(OutputCollection):
    def __init__(self, filepath):
        self._filepath = filepath
        self._file = None
        self._writer = None

    def open(self):
        self._file = self.open_file()
        self._writer = csv.writer(self._file)

    def open_file(self):
        return open(self._filepath, "w", newline="")

    def append(self, value):
        return self._writer.writerow(value)

    def close(self):
        self._file.close()

    def get_data(self):
        return self._filepath

    def getInput(self):
        return CsvInputCollection(self._filepath)

    def encode(self):
        return [self._filepath]

    @classmethod
    def decode(cls, args):
        return cls(args[0])


OUTPUTS = [ArrayOutputCollection, CsvOutputCollection]

OUTPUTS_DICT = {}
for o in OUTPUTS:
    OUTPUTS_DICT[o.key()] = o


def register_output(output):
    OUTPUTS.append(output)
    OUTPUTS_DICT[output.key()] = output


def output_find_by(name):
    return OUTPUTS_DICT.get(name)


def encode_output(output):
    return [output.key(), output.encode()]


def decode_output(output):
    return output_find_by(output[0]).decode(output[1])

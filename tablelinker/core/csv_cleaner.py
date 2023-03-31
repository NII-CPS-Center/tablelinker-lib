import csv
import io
from logging import getLogger

import charset_normalizer


logger = getLogger(__name__)


class CSVCleaner(object):
    """
    Converts a CSV file whose character encoding is SJIS or
    whose delimiter is TAB to a UTF-8, comma-delimited CSV.

    If the table data is preceded by lines such as a title,
    it will also be skipped.

    Usage:

        with CSVCleaner(data) as dictreader:
            # 'dictreader' is a csv.DictReader object.
            fieldnames = dictreader.fieldnames
            for row in dictreader:
                ...
    """

    def __init__(self, fp):
        self.text_io = None
        self.csv_reader = None
        self.delimiter = ','
        self.encoding = "UTF-8"

        # Check if the fp is a bytes-file or a text-file.
        line = fp.readline()
        if isinstance(line, bytes):
            if line[0:3] == b'\xef\xbb\xbf':  # UTF-8 with BOM
                # UTF-8 BOM
                line = line[3:]
                self.encoding = "utf-8-sig"
            else:
                # Detect encoding
                guess = charset_normalizer.detect(line)
                n = 0
                while guess["encoding"] is None:
                    line = fp.readline()
                    if line == "" or n > 1000:
                        logger.warning(
                            "Can't detect character encoding, give up.")
                        guess["encoding"] = "UTF-8"

                    guess = charset_normalizer.detect(line)
                    n += 1

                self.encoding = guess["encoding"]
                if self.encoding == "Shift_JIS":
                    self.encoding = "cp932"

            self.text_io = io.TextIOWrapper(
                buffer=fp, encoding=self.encoding, newline='')

        else:
            self.text_io = fp

        fp.seek(0)

    def open(self, as_dict: bool = False):
        self.delimiter = self.get_delimiter()
        self.skip_lines = self.get_skip_lines()

        self.text_io.seek(0)
        for _ in range(self.skip_lines):
            next(self.text_io)

        if as_dict is True:
            self.csv_reader = csv.DictReader(
                self.text_io, delimiter=self.delimiter)
        else:
            self.csv_reader = csv.reader(
                self.text_io, delimiter=self.delimiter)

        return self.csv_reader

    def get_reader(self):
        if self.csv_reader is not None:
            return self.csv_reader

        return False

    def __enter__(self, as_dict: bool = False):
        return self.open(as_dict=as_dict)

    def __next__(self):
        return self.csv_reader.__next__()

    def __exit__(self, type, value, traceback):
        pass
        # if self.text_io:
        #     self.text_io.close()

    def get_delimiter(self):
        """
        Get delimiter character.

        Returns
        -------
        str
            ',' or '\t'.
        """
        self.text_io.seek(0)
        for i, line in enumerate(self.text_io):
            if len(line) < 10:
                continue

            ncommas = line.count(',')
            ntabs = line.count('\t')
            if i < 5 or ncommas + ntabs < 2:
                continue

            if ncommas > ntabs:
                return ','
            elif ntabs > ncommas:
                return '\t'

        return ','

    def get_skip_lines(self):
        """
        Detect how many lines should be skipped from the beginning.

        Returns
        -------
        int
            Number of lines to be skipped.
        """
        # Count the number of columns in the first 20 rows,
        # and determine the max value as the number of columns of the table.
        ncols = []
        nvalues = []
        self.text_io.seek(0)
        reader = csv.reader(self.text_io, delimiter=self.delimiter)
        for i, row in enumerate(reader):
            while len(row) > 0 and \
                    (row[-1] == '' or row[-1].startswith('Unnamed: ')):
                del row[-1]

            ncols.append(len(row))
            nvalues.append(len(list(filter(len, row))))
            if i > 20:
                break

        table_columns = max(ncols)

        """
        # An alternative method

        from collections import defaultdict

        # Make frequency table
        freqs = defaultdict(int)
        for ncol in ncols:
            freqs[ncol] += 1

        freqs_sorted = sorted(freqs.items(), reverse=True, key=lambda x: x[1])

        # Remain the top three candidates for the number of columns,
        # with a frequency of occurrence of at least 1/3 of the number of rows.
        freqs = {}
        for ncol, freq in freqs_sorted[0:3]:
            if freq <= len(ncols) / 3:
                break

            freqs[ncol] = freq

        # Determine the largest value among the remaining candidates
        # as the number of columns in the table.
        table_columns = max(freqs.keys())
        """

        # Count the rows that do not match the calculated number of columns.
        skip_lines = 0
        for i, ncol in enumerate(ncols):
            nvalue = nvalues[i]
            if ncol == table_columns and nvalue > 1:
                # If the number of columns matches that of the table
                # and more than one columns contain values,
                # consider that line to be the starting line of data.
                break
            elif ncol == 0:
                if i < len(ncols) and nvalues[i + 1] > 1:
                    # If the line following an empty line has
                    # more than one columns, the data is considered
                    # to be the starting line of data.
                    skip_lines += 1
                    break

            skip_lines += 1

        return skip_lines


if __name__ == '__main__':
    """
    This sample code converts various CSV files in 'text_csv/'
    to UTF-8, comma separated, header skipped CSV files
    and save under 'text_csv_converted/'.
    """
    import glob
    import os

    for srcname in glob.glob('test_csv/*.csv'):
        basename = os.path.basename(srcname)
        dstname = os.path.join('test_csv_converted', basename)

        with open(srcname, 'rb') as fb, open(dstname, 'w', newline='') as dst:
            content = fb.read()
            with CSVCleaner(data=content) as cc:
                writer = csv.writer(dst)
                for row in cc:
                    writer.writerow(row)

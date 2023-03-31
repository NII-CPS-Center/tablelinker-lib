import json
import random
from dateutil.parser import parse
from convertors.core.types import DataType


class DataTypeResolver(object):
    """
    型の分析するクラスです。
    """

    def __init__(self, dataset_attr, threshold=None):
        self.attr_types = DataType.choices()
        self.dataset_attr = dataset_attr
        self.threshold = threshold if threshold is not None else 0.99
        self.counter = self.__setup_counter()
        self.collector = self.__setup_collector()

    def append(self, record, index):
        if index < len(record):
            value = record[index]
            data_type = self.__resolve_type(value)
            self.__count(value, data_type)
            self.__collect(value, data_type)

    def resolve(self):
        data_type = self.__analyze()
        self.dataset_attr.sample_values = self.__sample_by_collector(data_type)

        # TODO: 変更済みは、変更しない
        if data_type:
            try:
                self.dataset_attr.data_type = data_type[0]
            except TypeError:
                # データタイプが取得エラーになる場合は、unknownにする。
                self.dataset_attr.data_type = "unknown"
        self.dataset_attr.save()

    def __setup_counter(self):
        counter = {}
        for data_type in self.attr_types:
            counter[data_type[0]] = 0
        return counter

    def __setup_collector(self):
        collector = {}
        for data_type in self.attr_types:
            collector[data_type[0]] = set()
        return collector

    def __count(self, value, data_type):
        self.counter[data_type] += 1

    def __collect(self, value, data_type):
        self.collector[data_type].add(value)

    def __resolve_by_collector(self, data_type):
        # 文字列が２種類の場合
        if data_type == "string" and len(self.collector["string"]) == 2:
            return "boolean"
        return data_type

    def __sample_by_collector(self, data_type):
        """
        サンプル値を集める
        """
        sample_values = []
        for values in self.collector.values():
            for value in values:
                if value is not None and value != "":
                    sample_values.append(value)

        # 10個以上の値がある場合は、ランダムで10個を抽出します。
        if len(sample_values) > 10:
            sample_values = random.sample(sample_values, k=10)

        return json.dumps(list(sample_values), ensure_ascii=False)

    def __resolve_type(self, value):
        if is_int(value):  # 整数(全ての文字が数字なら真、そうでなければ偽
            return "integer"
        elif is_float(value):  # (半角・全角のアラビア数字が真
            return "float"
        elif is_date(value):  # 日付
            return "datetime"
        else:  # それ以外は、文字列
            return "string"

    def __analyze(self):
        total = sum(self.counter.values())

        if total == 0:
            return DataType.unknown

        data_type_key = None
        for key, value in self.counter.items():
            if (value / total) >= self.threshold:
                data_type_key = key
                continue

        if data_type_key is None:
            # 実数と整数の合計が、しきい値を超えるなら、実数として扱う。
            if self.counter["float"] + self.counter["integer"] \
                    > self.threshold:
                data_type_key = "float"
            if data_type_key is None:
                data_type_key = "unknown"
        else:
            data_type_key = self.__resolve_by_collector(data_type_key)

        for attr in self.attr_types:
            if attr[0] == data_type_key:
                return attr

        return DataType.unknown


def is_int(value):
    try:
        int(value)
    except ValueError:
        return False
    else:
        return True


def is_float(value):
    try:
        float(value)
    except ValueError:
        return False
    else:
        return True


def is_date(value):
    try:
        parse(value)
        return True
    except Exception:
        return False

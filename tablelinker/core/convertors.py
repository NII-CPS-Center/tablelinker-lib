from abc import ABC
from logging import getLogger
from typing import Any, List

from . import params

logger = getLogger(__name__)


class ConvertorMeta(object):
    """
    コンバータのメタデータを管理するクラス。

    Attrubutes
    ----------
    key: str
        コンバータ名。コンバータを指定する際に指定します。
    name: str
        コンバータの表示名。
    description: str
        簡単な説明。
    message: str
        表示用の簡単な説明。クラスで定義されていない場合は
        description を代わりに用います。
    help_text: str
        ヘルプ用メッセージ。
    params: params.ParamSet
        コンバータが受け付けるパラメータの集合です。
    """

    def __init__(self, meta):
        self.key = meta.key
        self.name = meta.name
        self.description = meta.description
        self.message = getattr(
            meta, "message", getattr(meta, "description", ""))
        self.help_text = meta.help_text
        self.params = meta.params

    @property
    def input_params(self):
        return [
            param for param in self.params
            if param.Meta.type == "input-attribute"
        ]

    @property
    def output_params(self):
        return [
            param for param in self.params
            if param.Meta.type == "output-attribute"
        ]


class Convertor(ABC):
    """
    コンバータのベースクラス。
    """

    def __repr__(self):
        return self.__class__.meta().key

    @classmethod
    def meta(cls):
        """
        コンバータクラスのメタデータクラスを返します。
        """
        return ConvertorMeta(cls.Meta)

    @classmethod
    def key(cls):
        """
        コンバータクラスの名前を返します。
        """
        return cls.meta().key

    @property
    def params(self):
        """
        コンバータクラスが受け付けるパラメータの集合を返します。
        """
        return self.__class__.meta().params

    def process(self, context):
        """
        変換処理を実行します。

        Parameters
        ----------
        context: Context
            コンバータを呼び出したコンテキスト情報です。
            入力データや出力先、実行時のパラメータを含みます。

        Notes
        -----
        ベースクラスの実装では、以下のメソッドを呼び出します。
        - preproc: 前処理。
        - process_header: 見出し行に対する処理。
        - process_record: データ行に対する処理。
        - postproc: 後処理。

        これ以外の処理を行うクラスを実装する場合は、 process を
        オーバーライドしてください。
        """
        # 前処理
        if self.preproc(context) is False:
            raise RuntimeError((
                "コンバータ {} は利用できません。"
                "エラーメッセージを確認してください。").format(self.key()))

        # データの先頭に巻き戻し、見出し行を取得します。
        context.reset()
        context.next()

        # 見出し行の処理
        self.process_header(self.headers, context)

        # データ行の処理
        for rows in context.read():
            if not self.check_record(rows, context):
                # データ行に異常がある場合はスキップ
                logger.warning("データ行をスキップ: '{}...'".format(
                    (",".join(rows))[0:10]))
                continue

            self.process_record(rows, context)

    def preproc(self, context) -> bool:
        """
        前処理を行います。

        Parameters
        ----------
        context: Context
            コンバータを呼び出したコンテキスト情報です。
            入力データや出力先、実行時のパラメータを含みます。

        Returns
        -------
        bool
            コンバータが利用できない等の理由で前処理に失敗した場合、
            False を返します。この場合処理は継続できません。

        Notes
        -----
        ベースクラスの実装では、以下の処理を行います。
        - コンテキストに渡された実行時パラメータの値のチェック。
        - "input_col_idx" から始まるパラメータに「列名」が渡された場合に
          列番号に置き換える処理。
        - "output_col_idx" から始まるパラメータに「列名」が渡された場合に
          列番号に置き換える処理。

        これ以外の前処理を行うクラスを実装する場合は、 preproc を
        オーバーライドしてください。
        """
        headers = context.next()
        context.set_data("headers", headers)
        context.set_data("num_of_columns", len(headers))

        # 入出力列番号に列名が指定された場合、列番号に変換する
        """
        for key in context.get_params():
            if key.startswith('input_col_idx'):
                val = context.get_param(key)
                if isinstance(val, str):
                    try:
                        idx = headers.index(val)
                        context._convertor_params[key] = idx
                    except ValueError:
                        raise RuntimeError((
                            "パラメータ '{}' で指定された列 '{}' は"
                            "有効な列名ではありません。有効な列名は次の通り; {}"
                        ).format(key, val, ",".join(headers)))
                elif isinstance(val, list):
                    for i, v in enumerate(val):
                        if isinstance(v, str):
                            try:
                                idx = headers.index(v)
                                context._convertor_params[key][i] = idx
                            except ValueError:
                                raise RuntimeError((
                                    "パラメータ '{}' の {} 番目で指定された列 '{}' は"
                                    "有効な列名ではありません。有効な列名は次の通り; {}"
                                ).format(key, i + 1, v, ",".join(headers)))

            if key.startswith('output_col_idx'):
                val = context.get_param(key)
                if isinstance(val, str):
                    try:
                        idx = headers.index(val)
                    except ValueError:
                        idx = len(headers)

                    context._convertor_params[key] = idx
                elif isinstance(val, list):
                    for i, v in enumerate(val):
                        if isinstance(v, str):
                            try:
                                idx = headers.index(v)
                            except ValueError:
                                idx = len(headers)
                                headers.append(v)

                            context._convertor_params[key][i] = idx
        """
        self.headers = headers
        self.num_of_columns = len(headers)

    def process_header(self, headers: List[str], context):
        """
        ヘッダ行に対する処理を実行します。

        Parameters
        ----------
        headers: List[str]
            見出しの列。
        context: Context
            コンバータを呼び出したコンテキスト情報です。
            入力データや出力先、実行時のパラメータを含みます。

        Notes
        -----
        ベースクラスの実装では、そのまま見出し列を出力します。

        これ以外の処理を行うクラスを実装する場合は、 process_header を
        オーバーライドしてください。
        """
        context.output(headers)

    def check_record(self, rows: List[Any], context) -> bool:
        """
        入力するレコードへのチェックを行います。

        Parameters
        ----------
        rows: List[Any]
            データ行の値の列。
        context: Context
            コンバータを呼び出したコンテキスト情報です。
            入力データや出力先、実行時のパラメータを含みます。

        Returns
        -------
        bool
            正常な場合は True, 異常が見つかった場合は False を返します。

        Notes
        -----
        ベースクラスの実装では、入力レコードに含まれる列数が
        見出し行と一致しているかどうかをチェックします。

        これ以外の処理を行うクラスを実装する場合は、 check_record を
        オーバーライドしてください。
        """
        num_of_columns = context.get_data("num_of_columns")
        if num_of_columns != len(rows):
            logger.warning(
                "num_of_columns: {:d} but record has {:d} fields.".format(
                    num_of_columns,
                    len(rows)))
            return False
        else:
            return True

    def process_record(self, rows: List[Any], context):
        """
        データ行に対する処理を実行します。

        Parameters
        ----------
        rows: List[Any]
            データ列。
        context: Context
            コンバータを呼び出したコンテキスト情報です。
            入力データや出力先、実行時のパラメータを含みます。

        Notes
        -----
        ベースクラスの実装では、そのままデータ列を出力します。

        これ以外の処理を行うクラスを実装する場合は、 process_record を
        オーバーライドしてください。
        """
        context.output(rows)

    @classmethod
    def get_message(cls, params):
        """
        変換時に追加するメッセージを生成します。
        params: パラメータのリストです。
        """
        return cls.meta().message.format(**params)


class InputOutputConvertor(Convertor):
    """
    1列の値を入力として、変換した結果を1列に出力する
    コンバータのベースクラスです。

    Attributes
    ----------
    input_col_idx: int
        入力値を持つ列番号（0が先頭列）。
    output_col_name: str
        出力列の列名。新規の列名も指定できます。
    output_col_idx: int
        出力する列の列番号（0が先頭列）。
    overwrite: bool [False]
        False の場合、出力列が空欄の場合のみ出力します。
    """
    @classmethod
    def meta(cls):
        _meta = ConvertorMeta(cls.Meta)
        _meta.params = params.ParamSet(
            [
                params.InputAttributeParam(
                    "input_col_idx",
                    label="入力列",
                    description="処理をする対象の列",
                    required=True),
                params.StringParam(
                    "output_col_name",
                    label="出力列名",
                    description="変換結果を出力する列名です。",
                    help_text="空もしくは既存の名前が指定された場合、置換となります。",
                    required=False,
                ),
                params.OutputAttributeParam(
                    "output_col_idx",
                    label="出力列の位置",
                    description="新しい列の挿入位置です。",
                    label_suffix="の後",
                    empty=True,
                    empty_label="先頭",
                    required=False,
                ),
                params.BooleanParam(
                    "overwrite",
                    label="上書き",
                    description="既に値が存在する場合に上書きするか指定します。",
                    default_value=True,
                    required=False)
            ]
            + _meta.params.params()
        )
        return _meta

    def preproc(self, context) -> bool:
        """
        前処理を行います。

        Parameters
        ----------
        context: Context
            コンバータを呼び出したコンテキスト情報です。
            入力データや出力先、実行時のパラメータを含みます。

        Notes
        -----
        InputOutputConvertor クラスの実装では、以下の処理を行います。
        - ベースクラスのすべての処理。
        - 出力列名 output_col_name が指定されていない場合、
          入力列名 input_col_name をコピー。
        - 出力列名 output_col_name が入力列に存在する場合、
          上書き列として記録。
        - 出力列番号 output_col_idx が指定されていない場合、
          末尾に新規列を追加。

        これ以外の前処理を行うクラスを実装する場合は、 preproc を
        オーバーライドしてください。
        """
        super().preproc(context)
        self.input_col_idx = context.get_param("input_col_idx")
        self.output_col_name = context.get_param("output_col_name")
        self.output_col_idx = context.get_param("output_col_idx")
        self.overwrite = context.get_param("overwrite")

        if self.output_col_name is None:
            # 出力列名が指定されていない場合は既存列名を利用する
            self.output_col_name = self.headers[self.input_col_idx]
            self.del_col = self.input_col_idx
            if self.output_col_idx is None:
                # 出力列番号も指定されていない場合は既存列の位置
                self.output_col_idx = self.input_col_idx

        else:
            # 出力列名が存在するかどうか調べる
            try:
                idx = self.headers.index(self.output_col_name)
                self.del_col = idx
            except ValueError:
                # 存在しない場合は新規列
                self.del_col = None
                self.overwrite = True

        if self.output_col_idx is None:
            # 出力列番号が指定されていない場合は末尾に追加
            self.output_col_idx = self.num_of_columns

        return True

    def process_header(self, headers, context):
        """
        ヘッダ行に対する処理を実行します。

        Parameters
        ----------
        headers: List[str]
            見出しの列。
        context: Context
            コンバータを呼び出したコンテキスト情報です。
            入力データや出力先、実行時のパラメータを含みます。

        Notes
        -----
        このクラスの実装では、以下の処理を行います。
        - 上書きされる列を削除。
        - 新しい列名を output_col_idx の位置に挿入。

        これ以外の処理を行うクラスを実装する場合は、 process_header を
        オーバーライドしてください。
        """
        headers = self.reorder(
            original=headers,
            del_idx=self.del_col,
            insert_idx=self.output_col_idx,
            insert_value=self.output_col_name)

        context.output(headers)

    def process_record(self, rows: List[Any], context):
        """
        データ行に対する処理を実行します。

        Parameters
        ----------
        rows: List[Any]
            データ列。
        context: Context
            コンバータを呼び出したコンテキスト情報です。
            入力データや出力先、実行時のパラメータを含みます。

        Notes
        -----
        このクラスの実装では、以下の処理を行います。
        - 上書きされる列を削除。
        - 処理結果を output_col_idx の位置に挿入。

        これ以外の処理を行うクラスを実装する場合は、 process_record を
        オーバーライドしてください。
        """
        need_value = False
        if self.overwrite:
            need_value = True
        else:
            # 置き換える列に空欄があるかどうか
            if self.del_col >= len(rows) or \
                    rows[self.del_col] == "":
                need_value = True

        if need_value:
            value = self.process_convertor(rows, context)
            if value is False:
                # コンバータの process_convertor で False を返す行はスキップされる
                return

        else:
            value = rows[self.del_col]

        rows = self.reorder(
            original=rows,
            del_idx=self.del_col,
            insert_idx=self.output_col_idx,
            insert_value=value)

        context.output(rows)

    def process_convertor(self, rows: List[Any], context):
        """
        データに対する処理を実行します。

        一般的な1入力-1出力コンバータでは、このメソッドをオーバーライドすれば
        必要な処理が実装できます。

        Parameters
        ----------
        rows: List[Any]
            データ列。
        context: Context
            コンバータを呼び出したコンテキスト情報です。
            入力データや出力先、実行時のパラメータを含みます。

        Notes
        -----
        このクラスの実装では、入力列の値をそのまま返します。
        入力列の値は rows[self.input_col_idx] で取得できます。

        処理を行った結果を返してください。
        ただし False を返すと、その行全体がスキップされます。

        これ以外の処理を行うクラスを実装する場合は、 process_convertor を
        オーバーライドしてください。
        """
        return rows[self.input_col_idx]

    def reorder(self, original, del_idx, insert_idx, insert_value):
        new_list = original[:]
        if del_idx is not None:
            new_list.pop(del_idx)
            if del_idx < insert_idx:
                insert_idx -= 1

        if insert_idx < 0:
            new_list.append(insert_value)
        else:
            new_list.insert(insert_idx, insert_value)

        return new_list


class InputOutputsConvertor(Convertor):
    """
    入力列が1, 出力列が複数のコンバータの基底クラス
    """

    @classmethod
    def meta(cls):
        _meta = ConvertorMeta(cls.Meta)
        _meta.params = params.ParamSet(
            [
                params.InputAttributeParam(
                    "input_col_idx",
                    label="入力列",
                    description="処理をする対象の列",
                    required=True),
                params.StringListParam(
                    "output_col_names",
                    label="出力列名のリスト",
                    description="変換結果を出力する列名のリストです。",
                    help_text="既存の列名が指定された場合、置換となります。",
                    required=False,
                    default_value=[],
                ),
                params.OutputAttributeParam(
                    "output_col_idx",
                    label="出力列の位置",
                    description="新しい列の挿入位置です。",
                    label_suffix="の後",
                    empty=True,
                    empty_label="先頭",
                    required=False,
                ),
                params.BooleanParam(
                    "overwrite",
                    label="上書き",
                    description="既に値が存在する場合に上書きするか指定します。",
                    default_value=False,
                    required=False
                ),
            ]
            + _meta.params.params()
        )
        return _meta

    def preproc(self, context) -> bool:
        super().preproc(context)
        self.old_col_indexes = []
        self.del_col_indexes = []
        self.input_col_idx = context.get_param("input_col_idx")
        self.output_col_idx = context.get_param("output_col_idx")
        self.output_col_names = context.get_param("output_col_names")
        if isinstance(self.output_col_names, str):
            self.output_col_names = [self.output_col_names]

        # 既存列をチェック
        for output_col_name in self.output_col_names:
            if output_col_name in self.headers:
                idx = self.headers.index(output_col_name)
                self.old_col_indexes.append(idx)
            else:
                self.old_col_indexes.append(None)

        # 挿入する位置
        if self.output_col_idx is None or \
                self.output_col_idx >= len(self.headers):  # 末尾
            self.output_col_idx = len(self.headers)

        # 列を一つずつ削除した場合に正しい列番号になるよう調整
        self.del_col_indexes = self.old_col_indexes[:]
        for i, del_index in enumerate(self.del_col_indexes):
            if del_index is None:
                continue

            if del_index < self.output_col_idx:
                self.output_col_idx -= 1

            for j, d in enumerate(self.del_col_indexes[i + 1:]):
                if d is not None and del_index < d:
                    self.del_col_indexes[i + j + 1] -= 1

        return True

    def process_header(self, headers, context):
        headers = self.reorder(
            original=headers,
            delete_idxs=self.del_col_indexes,
            insert_idx=self.output_col_idx,
            insert_values=self.output_col_names
        )
        context.output(headers)

    def process_record(self, rows, context):
        old_values = []
        for idx in self.old_col_indexes:
            if idx is None:
                old_values.append("")
            else:
                old_values.append(rows[idx])

        if context.get_param("overwrite"):
            new_values = self.process_convertor(
                rows, context)
        else:
            values = None
            new_values = []
            for i, old_value in enumerate(old_values):
                if old_value == "":
                    if values is None:
                        values = self.process_convertor(
                            rows, context)

                    new_values.append(values[i])
                else:
                    new_values.append(old_value)

        rows = self.reorder(
            original=rows,
            delete_idxs=self.del_col_indexes,
            insert_idx=self.output_col_idx,
            insert_values=new_values)
        context.output(rows)

    def process_convertor(self, rows, context):
        return rows[self.input_col_idx]

    def reorder(self, original, delete_idxs, insert_idx, insert_values):
        """
        列の削除と追加を行う。

        Parameters
        ----------
        original: list[str]
            入力行。
        delete_idxs: list[(int, None)]
            削除する列番号、 None の場合は削除しない。
        insert_idx: int
            追加する列番号
        insert_values: list[str]
            追加する文字列のリスト
        """
        new_list = original[:]
        for delete_idx in delete_idxs:
            if delete_idx is None:
                continue

            del new_list[delete_idx]

        new_list = new_list[0:insert_idx] + insert_values \
            + new_list[insert_idx:]

        return new_list


class NoopConvertor(Convertor):
    """
    何もしない
    """

    class Meta:
        key = "noop"
        name = "何もしません"
        description = None
        help_text = None
        params = params.ParamSet()


class AttrCopyConvertor(InputOutputConvertor):
    """
    列コピー
    """

    class Meta:
        key = "acopy"
        name = "列のコピー"
        description = "列をコピーします"
        help_text = None
        params = params.ParamSet()


CONVERTORS = [AttrCopyConvertor]
CONVERTOR_DICT = {}
for f in CONVERTORS:
    CONVERTOR_DICT[f.key()] = f


def register_convertor(convertor, selectable=True):
    """
    コンバータを登録します。
    convertor: コンバータクラス
    selectable: ユーザが選択可能なコンバータかどうか
    """
    if selectable:
        CONVERTORS.append(convertor)
    CONVERTOR_DICT[convertor.key()] = convertor


def convertor_find_by(name):
    """
    登録済みのコンバータを取得します。
    """
    convertor = CONVERTOR_DICT.get(name)
    if convertor is None:
        from tablelinker.convertors.extras import register
        register()

    return CONVERTOR_DICT.get(name)


def convertor_all():
    return [f for f in CONVERTORS]


def convertor_keys():
    return [f.Meta.key for f in CONVERTORS]


def encode_convertor(convertor):
    return [convertor.key()]


def decode_convertor(convertor):
    return convertor_find_by(convertor[0])()

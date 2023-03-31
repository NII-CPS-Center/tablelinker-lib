import hashlib
from logging import getLogger

from tablelinker.core import convertors, params

logger = getLogger(__name__)


class UniqueKeyGenerator(object):
    """
    一意の文字列からユニークキーを生成するクラス。
    """

    def __init__(self):
        self.key_list = {}

    @classmethod
    def md5hex(cls, val: str) -> str:
        """
        Return md5 hex digest string.

        Parameters
        ----------
        val: str
            Input string.

        Returns
        -------
        str
            md5 hex digest string.

        Examples
        --------
        >>> UniqueKeyGenerator.md5hex('Lorem Ipsum')
        '6dbd01b4309de2c22b027eb35a3ce18b'
        """
        return hashlib.md5(val.encode('utf-8')).hexdigest()

    @classmethod
    def radix2number(cls, val: str, charset: str = '0123456789abcdef') -> int:
        """
        Converts a string consisting of a specific set of characters
        to a numeric value.

        Parameters
        ----------
        val: str
            Input string. It is case-sensitive.
        charset: str, optional
            The set of characters.
            If omitted, the hexadecimal characters are used.

        Returns
        -------
        int
            The converted int value.

        Examples
        --------
        >>> UniqueKeyGenerator.radix2number('45ac')
        17836
        >>> UniqueKeyGenerator.radix2number('a39c22e0')
        2744918752
        """
        result = 0
        radix = len(charset)
        for c in val:
            result = result * radix + charset.index(c)

        return result

    @classmethod
    def number2radix(cls, val: int, charset: str = '0123456789abcdef') -> str:
        """
        Converts a numeric value to a string consisting of
        a specific set of characters.

        Parameters
        ----------
        val: int
            Input value.
        charset: str, optional
            The set of characters.
            If ommitted, the hexadecimal characters are used.

        Returns
        -------
        str
            The converted string.

        Examples
        --------
        >>> UniqueKeyGenerator.number2radix(17836)
        '45ac'
        >>> UniqueKeyGenerator.number2radix(2744918752)
        'a39c22e0'
        """
        result = ''
        radix = len(charset)
        while val > 0:
            result = charset[val % radix] + result
            val //= radix

        return result

    @classmethod
    def generate_short_hash_string(
            cls,
            key: str,
            hash_len: int = 8) -> str:
        """
        短いハッシュ文字列を生成します。
        Parameters
        ----------
        key: str
            ハッシュの元になる文字列
        hash_len: int, optional
            ハッシュ文字列の長さ（デフォルトは8）
        Returns
        -------
        str
            生成したハッシュ文字列
        """
        md5_str = cls.md5hex(key)
        hash_value = cls.radix2number(md5_str)
        hash_str = cls.number2radix(
            hash_value,
            "23456789ABCDEFGHIJKLMNPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        )
        return hash_str[0:hash_len]

    def gen_key(
            self,
            seed: str,
            length: int = 6,
            check_uniqueness: bool = False) -> str:
        """
        ユニークキー文字列を生成します。
        既に登録済みのキーとの重複チェックも行ないます。
        異なる seed から同じキーが生成された場合、
        RuntimeError 例外を生成します。

        Parameters
        ----------
        seed: str
            データセット内でユニークな文字列
        length: int, optional [6]
            生成する文字列の長さ
        check_uniqueness: bool, optional [False]
            True の場合、キーが重複すると None を返します。

        Returns
        -------
        str
            生成したキー文字列
        """
        key = self.__class__.generate_short_hash_string(
            seed, length)
        if key in self.key_list:
            if self.key_list[key] != seed:
                logger.debug(
                    "key: '{}', seed: '{}', seed in list: '{}'".format(
                        key, seed, self.key_list[key]))
                raise ValueError(
                    "キーが重複しました。length を大きくしてください。")

            if check_uniqueness:
                return None

        self.key_list[key] = seed
        return key


class GeneratePkConvertor(convertors.InputOutputConvertor):
    r"""
    概要
        指定した列の文字列をシードとして、
        ユニークなキー文字列を生成します。

    コンバータ名
        "generate_pk"

    パラメータ（InputOutputConvertor 共通）
        * "input_col_idx": シードとする列の列番号または列名 [必須]
        * "output_col_idx": 結果を出力する列番号または列名のリスト
        * "output_col_name": 結果を出力する列名
        * "overwrite": 既に値がある場合に上書きするかどうか [False]

    パラメータ（コンバータ固有）
        * "length": 生成するキー文字列の長さ [6]
        * "skip_if_not_unique": 同じ値の行が存在する場合に
          スキップするかどうか [False]
        * "error_if_not_unique": 同じ値の行が存在する場合に
          エラーにするかどうか [True]

    注釈（InputOutputConvertor 共通）
        - ``output_col_name`` が省略された場合、
          ``input_col_idx`` 列の列名が出力列名として利用されます。
        - ``output_col_idx`` が省略された場合、
          出力列名が存在する列名ならばその列の位置に出力し、
          存在しないならば最後尾に追加します。

    注釈（コンバータ固有）
        - 入力列の値が異なるのに生成されたキーが同じになる場合、
          RuntimeError 例外が発生するので ``length`` を増やしてください。

    サンプル
        「クレジットカード」列の値から 6 桁のキーを生成し、
        先頭に「PK」列として追加します。

        - タスクファイル例

        .. code-block:: json

        .. code-block :: json

            {
                "convertor": "generate_pk",
                "params": {
                    "input_col_idx": "クレジットカード",
                    "output_col_name": "PK",
                    "output_col_idx": 0,
                    "length": 6,
                    "error_if_not_unique": false,
                    "skip_if_not_unique": true
                }
            }

        - コード例

        .. code-block:: python

            >>> # データはランダム生成
            >>> from tablelinker import Table
            >>> table = Table(data=(
            ...     '"氏名","生年月日","性別","クレジットカード"\n'
            ...     '"小室 友子","1990年06月20日","女","3562635454918233"\n'
            ...     '"小室 雅代","1963年08月19日","女","3562635454918233"\n'
            ...     '"江島 佳洋","1992年10月07日","男","376001629316609"\n'
            ...     '"三沢 大志","1995年02月13日","男","4173077927458449"\n'
            ... ))
            >>> table = table.convert(
            ...     convertor="generate_pk",
            ...     params={
            ...         "input_col_idx": "クレジットカード",
            ...         "output_col_name": "PK",
            ...         "output_col_idx": 0,
            ...         "length": 6,
            ...         "error_if_not_unique": False,
            ...         "skip_if_not_unique": True,
            ...     },
            ... )
            >>> table.write()
            PK,氏名,生年月日,性別,クレジットカード
            9wUXiv,小室 友子,1990年06月20日,女,3562635454918233
            JtFkJ7,江島 佳洋,1992年10月07日,男,376001629316609
            KP9RIz,三沢 大志,1995年02月13日,男,4173077927458449

    """

    class Meta:
        key = "generate_pk"
        name = "ユニークキー生成"
        description = """
        ユニークキーを生成します。
        """
        help_text = None
        params = params.ParamSet(
            params.IntParam(
                "length",
                label="生成するキー文字列の長さ",
                required=False,
                default_value=6,
            ),
            params.BooleanParam(
                "error_if_not_unique",
                label="一意ではない場合エラーにするか",
                required=False,
                default_value=True,
            ),
            params.BooleanParam(
                "skip_if_not_unique",
                label="一意ではない場合スキップするか",
                required=False,
                default_value=False,
            ),
        )

    def preproc(self, context):
        super().preproc(context)
        self.length = context.get_param("length")
        self.error_if_not_unique = context.get_param("error_if_not_unique")
        self.skip_if_not_unique = context.get_param("skip_if_not_unique")
        self.ukgen = UniqueKeyGenerator()

    def process_convertor(self, record, context):
        key = self.ukgen.gen_key(
            seed=record[self.input_col_idx],
            length=self.length,
            check_uniqueness=(
                self.skip_if_not_unique or self.error_if_not_unique
            ),
        )
        if key is None:
            # 同じ値を持つ行が見つかった
            if self.error_if_not_unique:
                raise ValueError("Not unique key generated by '{}'".format(
                    record[self.input_col_idx]))

            if self.skip_if_not_unique:
                return False

        return key

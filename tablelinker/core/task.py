import json
from logging import getLogger
import os
from typing import List, Optional, Union

from .convertors import convertor_find_by


logger = getLogger(__name__)


class Task(object):
    """
    タスクを管理するクラス。

    Parameters
    ----------
    convertor: str
        コンバータ名。
    params: dict
        パラメータ名と値を持つ dict。
    note: str, optional
        タスクの内容に対するメモ。

    Attributes
    ----------
    convertor: str
        パラメータ参照。
    params: dict
        パラメータ参照。
    note: str, optional
        指定されている場合、変換処理実行時にタスク名をロガーに
        INFO レベルで出力します。

    """

    def __init__(
            self,
            convertor: str,
            params: dict,
            note: Optional[str] = None):
        self.convertor = convertor
        self.params = params
        self.note = note

    def __repr__(self):
        if self.note:
            return "{}({})".format(
                self.convertor,
                self.note)

        return "{}".format(self.convertor)

    @classmethod
    def create(cls, task: dict) -> "Task":
        """
        dict から Task を作成します。
        パラメータのキーのチェックも行います。

        Parameters
        ----------
        task: dict
            キーに "convertor", "params" を必ず含み、オプションとして
            "note" を含む dict。

        Returns
        -------
        Task
            新しい Task オブジェクト。

        Examples
        --------
        >>> from tablelinker import Task
        >>> task = Task.create({
        ...     "convertor": "rename_col",
        ...     "params": {"input_col_idx":1, "output_col_name":"地域"},
        ... })
        >>> task
        rename_col

        Examples
        --------
        >>> # 不要なキーが含まれていると ValueError を送出します
        >>> from tablelinker import Task
        >>> task = Task.create({
        ...     "convertor_name": "rename_col",
        ...     "params": {"input_col_idx":1, "output_col_name":"地域"},
        ... })
        Traceback (most recent call last):
        ValueError: 未定義のキー 'convertor_name' が使われています。

        Examples
        --------
        >>> # 必要なキーが含まれていない場合も ValueError を送出します
        >>> from tablelinker import Task
        >>> task = Task.create({
        ...     "convertor": "rename_col",
        ... })
        Traceback (most recent call last):
        ValueError: キー 'params' が必要です。

        Examples
        --------
        >>> # 未定義のコンバータを指定した場合も ValueError を送出します
        >>> from tablelinker import Task
        >>> task = Task.create({
        ...     "convertor": "undefined_convertor",
        ...     "params": {"input_col_idx": 1},
        ... })
        Traceback (most recent call last):
        ValueError: コンバータ 'undefined_convertor' は登録されていません。

        Examples
        --------
        >>> # ただし params の内容は変換実行時までチェックしません
        >>> from tablelinker import Task
        >>> task = Task.create({
        ...     "convertor": "rename_col",
        ...     "params": None,
        ... })
        >>> task
        rename_col

        Notes
        -----
        - 必要なキーが欠けていたり、不要なキーが含まれていると
          `ValueError` 例外を送出します。
        - キーのチェックしかしないため、正しくない値が指定されていても
          エラーにはなりません。
        - たとえば params にそのコンバータでは利用できないパラメータが
          指定されていてもエラーになりません。

        """
        if not isinstance(task, dict):
            raise ValueError("タスクが object ではありません。")

        unrecognized_keys = []
        for key in task.keys():
            if key not in ("convertor", "params", "note",):
                unrecognized_keys.append(key)

        if len(unrecognized_keys) > 0:
            raise ValueError("未定義のキー '{}' が使われています。".format(
                ",".join(unrecognized_keys)))

        undefined_keys = []
        for key in ("convertor", "params",):
            if key not in task:
                undefined_keys.append(key)

        if len(undefined_keys) > 0:
            raise ValueError("キー '{}' が必要です。".format(
                ",".join(undefined_keys)))

        if convertor_find_by(task["convertor"]) is None:
            raise ValueError(
                "コンバータ '{}' は登録されていません。".format(
                    task["convertor"]))

        return Task(**task)

    @classmethod
    def from_files(
        cls,
        taskfiles: Union[str, os.PathLike, List[os.PathLike]],
        *args,
    ) -> List["Task"]:
        """
        タスクファイルを読み込み、解析・検証してタスクリストを作成します。

        Parameters
        ----------
        taskfiles: str, PathLike, List[PathLike]
            タスクファイルのパス、またはパスのリスト。
        args: List[str, PathLike]
            追加のタスクファイルのパス。

        Returns
        -------
        List[Task]
            タスクのリスト。

        Examples
        --------
        >>> # タスクファイルを1つ指定すると、タスクを1つ含むリストを返します。
        >>> from tablelinker import Task
        >>> Task.from_files("task1.json")
        [rename_col]

        Examples
        --------
        >>> # タスクファイルのリストを指定すると、複数のタスクを含むリストを返します。
        >>> Task.from_files(["task1.json", "task2.json"])
        [rename_col, concat_title]

        Examples
        --------
        >>> # タスクファイルを複数のパラメータとして指定しても、複数のタスクを含むリストを返します。
        >>> Task.from_files("task1.json", "task2.json")
        [rename_col, concat_title]

        Notes
        -----
        - タスクが1つの場合でもリストを返します。

        """  # noqa: E501
        if isinstance(taskfiles, (str, os.PathLike,)):
            taskfiles = [taskfiles]

        for arg in args:
            taskfiles.append(arg)

        all_tasks = []
        for taskfile in taskfiles:
            with open(taskfile, 'r') as jsonf:
                logger.debug("Reading tasks from '{}'.".format(
                    taskfile))
                try:
                    tasks = json.load(jsonf)
                except json.decoder.JSONDecodeError as e:
                    logger.error((
                        "タスクファイル '{}' の JSON 表記が正しくありません。"
                        "json.decoder.JSONDecodeError: {}").format(
                            taskfile, e))
                    raise ValueError("Invalid JSON in '{}'.({})".format(
                        taskfile, e))

            if isinstance(tasks, dict):
                # コンバータが一つだけ指定されている場合
                tasks = [tasks]

            try:
                for task in tasks:
                    # タスクファイルのフォーマットチェック
                    all_tasks.append(Task.create(task))

            except ValueError as e:
                logger.error((
                    "タスクファイル '{}' のフォーマットが"
                    "正しくありません。詳細：{}").format(taskfile, str(e)))
                raise ValueError("Invalid Task format in '{}'.({})".format(
                    taskfile, e))

        return all_tasks

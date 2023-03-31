from logging import getLogger

from .core.table import Table
from .core.task import Task

__version__ = "1.0.0"  # pyproject.toml と git tag も変更すること

logger = getLogger(__name__)


def useExtraConvertors() -> None:
    """
    拡張コンバータを利用することを宣言する。
    """
    from .convertors import extras as extra_convertors
    extra_convertors.register()
    logger.debug("拡張コンバータを登録しました。")


__all__ = [
    Table,
    Task,
    useExtraConvertors
]

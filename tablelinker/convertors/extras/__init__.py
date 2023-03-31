import glob
import inspect
import importlib
import os

from tablelinker.core.convertors import Convertor, register_convertor


__all__ = []


def register():
    """
    このディレクトリにある全てのモジュールをインポートします。
    """
    modules = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))
    for f in modules:
        if os.path.isfile(f) and not f.endswith('__init__.py'):
            __all__.append(os.path.basename(f)[:-3])  # '.py' を除く

    for m in __all__:
        importlib.import_module("." + m, __name__)

    # モジュール内の Convertor のサブクラスを探して登録します。
    module_dict = globals()
    for m in __all__:
        # module_name = __name__ + '.' + m
        module = module_dict.get(m)
        for name in dir(module):
            c = getattr(module, name)
            if not inspect.isclass(c):
                continue

            if issubclass(c, Convertor):
                register_convertor(c)

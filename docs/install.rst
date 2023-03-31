.. _install:

インストール手順
================

.. note::

    他の Python パッケージと同様に、 Tablelinker パッケージは
    多くの依存パッケージをインストールします。システムの
    Python 環境を汚さないように
    `pyenv <https://github.com/pyenv/pyenv>`_,
    `venv <https://docs.python.org/ja/3/library/venv.html>`_
    などで仮想環境を作成し、その中にインストールすることをお勧めします。

Tablelinker パッケージのインストール
------------------------------------

Tablelinker は pip コマンドでインストールできます。 ::

    pip install tablelinker

ただし、 Python のバージョンが 3.7 以上、 3.10 以下である必要があります。

3.11 に対応していないのは、 `pytorch が 3.11 をまだサポートしていない
<https://github.com/pytorch/pytorch/issues/86566>`_ ためですので、
そのうちこの問題は解消される予定です。

Mac の場合
^^^^^^^^^^

MacOS Ventura で Xcode をインストールすると Python 3.11 が
インストールされますので、そのままでは Tablelinker は利用できません。

お手数ですが `Homebrew <https://brew.sh/index_ja>`_ と
`pyenv <https://github.com/pyenv/pyenv>`_ を利用して、
Python 3.10 をインストールしてからご利用ください。

.. code-block:: zsh

    (Homebrew をインストールしている場合)
    % brew install pyenv
    (表示されるメッセージに従って PATH などを設定)
    % pyenv install 3.10
    % pyenv local 3.10
    % python -m pip install tablelinker

Windows の場合
^^^^^^^^^^^^^^

Microsoft Store から Python 3.10 をインストールし、
PowerShell を開いて上記の pip コマンドを利用すれば
Tablelinker をインストールできます。

.. code-block:: powershell

    > pip install tablelinker

複数の Python バージョンをインストールしている場合、
Python launcher ``py.exe`` を実行して `利用するバージョンを指定する
<https://docs.python.org/ja/3/using/windows.html#from-the-command-line>`_ 
必要があります。

.. code-block:: powershell

    > py --list
    Installed Pythons found by C:\WINDOWS\py.exe Launcher for Windows
     -3.9-64 *
     -3.10-64
    > py -3.10 -m pip install tablelinker

インストール中に、以下のような警告が表示されます。 ::

    ...
    Installing collected packages: tablelinker
      WARNING: The script tablelinker.exe is installed in 'C:\Users\foo\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\Scripts' which is not on PATH.
      Consider adding this directory to PATH or, if you prefer to suppress this warning, use --no-warn-script-location.
    Successfully installed tablelinker-1.0.0

``tablelinker.exe`` は :ref:`as_command` で説明するコマンドです。
このコマンドを利用したい場合は、警告の `... is installed in` の後ろに
表示されているディレクトリを環境変数 ``PATH`` に追加してください。

上の例では ``C:\Users\foo\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\Scripts`` となっていますが、実行中の Python
環境によって異なりますので、必ず表示されているメッセージに合わせてください。

環境変数 ``PATH`` にディレクトリを追加するには、
コントロールパネルのシステム設定を利用するなどいろいろな方法があります。
ウェブ検索するなどして、やりやすい方法を利用してください。

コマンドラインでの操作に慣れている場合は、
PowerShell から以下の方法で追加できます。

.. code-block:: powershell

    > # 現在の Path の値を表示して、最後が ; で終わっているかどうか確認する
    > $Env:Path
    > # ; で終わっている場合は
    > $Env:Path += "C:\Users\foo\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\Scripts"
    > # ; で終わっていない場合は
    > $Env:Path += ";C:\Users\foo\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\LocalCache\local-packages\Python310\Scripts"


Linux の場合
^^^^^^^^^^^^

Linux ディストリビューションごとのパッケージ管理ツールで
Python と pip をインストールして、ターミナル上で上記の pip コマンドを
利用すれば Tablelinker をインストールできます。

ただし Python 2.x 系と 3.x 系の両方が利用できるディストリビューションでは、
Python 3.x 系のコマンドは ``python3``、 pip コマンドは ``pip3`` に
なっている場合がありますので注意してください。

.. code-block:: bash

    (Ubuntu の場合)
    $ sudo apt install python3 python3-pip
    $ pip3 install tablelinker


住所辞書データのインストール
----------------------------

住所ジオコーディング機能が必要なコンバータを利用するには、
別途住所辞書データをダウンロード・インストールする必要があります。
住所ジオコーディング機能を利用しない場合は住所辞書データは不要です。 ::

    python -m jageocoder download-dictionary
    python -m jageocoder install-dictionary jusho-20220519.zip

詳細は `jageocoderのインストール手順 <https://jageocoder.readthedocs.io/ja/latest/install.html#install-dictionary>`_ を参照してください。


アンインストール手順
--------------------

住所辞書データをインストールした場合、 Tablelinker パッケージを
アンインストールする前に辞書をアンインストールしてください。 ::

    python -m jageocoder uninstall-dictionary

Tablelinker パッケージは pip uninstall でアンインストールできます。 ::

    pip uninstall tablelinker

Mac の場合
^^^^^^^^^^

`Homebrew <https://brew.sh/index_ja>`_ と
`pyenv <https://github.com/pyenv/pyenv>`_ を利用して
Python 3.10 をインストールした場合は、 ``pip`` でアンインストールできます。

.. code-block:: zsh

    % pip uninstall tablelinker

Windows の場合
^^^^^^^^^^^^^^

複数の Python バージョンをインストールしている場合、
Python launcher ``py.exe`` を実行して、
Tablelinker をインストールした Python バージョンを指定する
必要があります。

.. code-block:: powershell

    > py -3.10 -m pip uninstall tablelinker

Linux の場合
^^^^^^^^^^^^

3.x 系の Python を実行するのに ``python3`` コマンドを利用する
必要がある場合、 ``pip3`` コマンドでアンインストールできます。

.. code-block:: bash

    $ pip3 uninstall tablelinker

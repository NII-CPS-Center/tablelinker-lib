import json
import logging
from logging import getLogger
from pathlib import Path
import re
import sys
import tempfile
from typing import List

from docopt import docopt

from tablelinker import Table, Task

logger = getLogger(__name__)

HELP = """
'tablelinker' は表データ（CSV, TSV, Excel）を読み込み、
さまざまなコンバータを適用して変換・加工し、
目的のフォーマットの表データを生成するツールです。

Usage:
  {p} -h
  {p} mapping [-d] [-i <file>] [-s <sheet>] [-o <file>]\
 [-a ([--sjis]|[--bom]) [-m] ] ([-t <sheet>] <template>|--headers=<headers>)\
 [--th=<th>]
  {p} [-d] [-i <file>] [-s <sheet>] [-o <file>] ([--sjis]|[--bom]) [-m]\
 [--no-cleaning] -c <convertor> -p <params>
  {p} [-d] [-i <file>] [-s <sheet>] [-o <file>] ([--sjis]|[--bom]) [-m]\
 [--no-cleaning] [<task>...]

Options:
  -h --help              このヘルプを表示
  -d --debug             デバッグメッセージを表示
  -i, --input=<file>     入力ファイルを指定（省略時は標準入力）
  -s, --sheet=<sheet>    入力ファイルのうち対象とするシート名（省略時は先頭）
  -o, --output=<file>    出力ファイルを指定（省略時は標準出力）
  -a, --auto             マッピング情報ではなくマッピング結果を出力する
  --sjis                 SJIS (cp932) でエンコードする（省略時は UTF-8）
  --bom                  BOM付き UTF-8 でエンコードする（省略時は BOM無し）
  -m, --merge            出力ファイルにマージ（省略時は上書き）
  -t, --template-sheet=<sheet>  テンプレートのシート名（省略時は先頭）
  --headers=<headers>    列名リスト（カンマ区切り）
  --th=<th>              マッピング判定のしきい値（0から100） [default: 20]
  --no-cleaning          指定すると入力ファイルをクリーニングしない
  -c, --convertor=<convertor>   コンバータ名
  -p, --params=<params>  パラメータ（JSON）

Parameters:
  <task>        タスクファイル（コンバータとパラメータを記述した JSON）
  <template>    テンプレート列を含む表データファイル

Examples:

- CSV ファイル ma030000.csv を変換して標準出力に表示します

  python -m tablelinker -i ma030000.csv task.json

  適用するコンバータやパラメータは task.json ファイルに JSON 形式で記述します。

- Excel ファイル hachijo_sightseeing.xlsx をテンプレート\
  xxxxxx_tourism.csv に合わせるマッピング情報を生成します

  python -m tablelinker mapping \
-i hachijo_sightseeing.xlsx templates/xxxxxx_tourism.csv

  マッピング情報はタスクとして利用できる JSON 形式で出力されます。
""".format(p='tablelinker')


def process_tasks(args: dict, all_tasks: List["Task"]):
    """
    すべての task を実行します。
    """
    skip_cleaning = bool(args['--no-cleaning'])

    with tempfile.TemporaryDirectory() as tmpdir:
        if args['--input'] is not None:
            csv_in = Path(args['--input'])
        else:
            logger.debug("Reading csv data from STDIN...")
            # sys.stdin は seek できないので、一時ファイルに保存する
            csv_in = Path(tmpdir) / 'input.csv'
            with open(csv_in, 'wb') as fout:
                fout.write(sys.stdin.buffer.read())

        logger.debug("Start convertor(s)...")
        table = Table(
            csv_in,
            sheet=args['--sheet'],
            skip_cleaning=skip_cleaning)

        # タスク実行
        for task in all_tasks:
            try:
                logger.debug("Running {}".format(task))
                table = table.apply(task)

            except RuntimeError as e:
                logger.error((
                    "タスク '{}' の実行中にエラーが発生しました。"
                    "詳細：{}").format(task, str(e)))
                sys.exit(-1)

        # 結果を出力
        if args['--output'] is None:
            table.write(skip_header=args['--merge'])
        elif args['--merge']:
            table.merge(Path(args['--output']))
        else:
            encoding = "utf-8"
            if args["--sjis"]:
                encoding = "cp932"
            elif args["--bom"]:
                encoding = "utf-8-sig"

            table.save(Path(args['--output']), encoding=encoding)


def mapping(args: dict):
    with tempfile.TemporaryDirectory() as tmpdir:
        if args['--input'] is not None:
            csv_in = Path(args['--input'])
        else:
            # 標準入力のデータを一時ファイルに保存する
            # Note: stdin は seek() が利用できないため
            logger.debug("Reading csv data from STDIN...")
            csv_in = Path(tmpdir) / 'input.csv'
            with open(csv_in, 'wb') as fout:
                fout.write(sys.stdin.buffer.read())

        table = Table(csv_in, sheet=args['--sheet'])

        # しきい値
        # 手作業で修正することを前提とするため、
        # デフォルトは緩い値（20）
        th = int(args['--th'])

        logger.debug("マッピング中")
        if args['<template>']:
            # テンプレートとなる表データファイルを指定
            template = Table(
                file=Path(args['<template>']),
                sheet=args['--template-sheet'])
            mapping = table.mapping(template, th)
        elif args['--headers']:
            mapping = table.mapping_with_headers(args['--headers'], th)

        logger.debug("マッピング完了：{}".format(dict(mapping)))

        if args["--auto"] is False:
            # 結果出力
            result = json.dumps({
                "convertor": "mapping_cols",
                "params": {"column_map": mapping},
            }, indent=2, ensure_ascii=False)

            if args['--output']:
                with open(args['--output'], 'w') as f:
                    print(result, file=f)
            else:
                print(result)

        else:
            # "--auto" オプションが指定されている場合は変換結果を出力
            table = table.convert(
                convertor='mapping_cols',
                params={'column_map': mapping})
            if args['--output'] is None:
                table.write(skip_header=args['--merge'])
            elif args['--merge']:
                table.merge(Path(args['--output']))
            else:
                encoding = "utf-8"
                if args["--sjis"]:
                    encoding = "cp932"
                elif args["--bom"]:
                    encoding = "utf-8-sig"

                table.save(Path(args['--output']), encoding=encoding)


def parse_relaxed_json(val: str):
    """
    Windows 環境でパラメータの " が除去されてしまうため、
    JSON に戻してパーズします。

    Parameters
    ----------
    val: str
        '"' が欠けた JSON のような文字列。
        例： '{input_col_idx:住所, output_col_names:[緯度0,経度0,レベル0]}'
    """
    try:
        parsed = json.loads(val)
        # 正常な JSON フォーマットの場合
        return parsed
    except json.decoder.JSONDecodeError:
        pass

    fixed = re.sub(r'(\w+)', r'"\g<1>"', val)
    try:
        parsed = json.loads(fixed)
        # 語の周りを '"' で囲えば解析できる場合
        return parsed
    except json.decoder.JSONDecodeError:
        pass

    logger.error("パラメータ '{}' を解釈できません。".format(val))
    sys.exit(-1)


def main():
    args = docopt(HELP)

    if args['--debug']:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s:%(levelname)s:%(module)s:%(lineno)d:%(message)s')

    logger.debug(args)

    if args['--input'] is not None:
        if args['--input'].lower() in ('-', 'stdin'):
            args['--input'] = None

    if args['--output'] is not None:
        if args['--output'].lower() in ('-', 'stdout'):
            args['--output'] = None

    if args['mapping']:
        mapping(args)
    elif args["--convertor"] and args["--params"]:
        if args["--params"][0] != '{' and args["--params"][-1] != '}':
            args["--params"] = "{" + args["--params"] + "}"

        task = Task.create({
            "convertor": args["--convertor"],
            "params": parse_relaxed_json(args["--params"]),
        })
        process_tasks(args, [task])
    else:
        process_tasks(
            args,
            Task.from_files(args['<task>']))

#!/usr/bin/env python3
"""csv2strings

CSV から iOS 用 Localizable.strings と Android 用 strings.xml を生成する。

    csv2strings.py {source path}.csv {output directory path}

CSV の 1 列目は文字列 ID。2 列目以降は各言語の列で、ヘッダー名が
出力ディレクトリ名になる。ID が "#" で始まる行はセクション区切りとして
コメントに変換される。
"""

import argparse
import csv
import os
import re
import sys


def build_ios(header, keyed_rows, key_id):
    """iOS 用 Localizable.strings の中身を組み立てる。"""
    lines = [
        "/* \n  Localizable.strings\n  {}\n  \n  Generate by csv2strings\n*/\n".format(header)
    ]

    for row in keyed_rows:
        entry_id = row.get(key_id, "")
        if not entry_id:
            continue

        if entry_id.startswith("#"):
            lines.append("\n// MARK: - {}".format(section_name(entry_id)))
            continue

        value = unescape_entities(cell_value(row, header, entry_id))
        lines.append('"{}" = "{}";'.format(entry_id, escape_ios(value)))

    return "\n".join(lines)


def escape_ios(value):
    """Localizable.strings の "key" = "value"; 形式に収まるようエスケープする。

    裸の " が入ると構文が壊れるため \\" にする。

    バックスラッシュは .strings が解釈するエスケープだけ書かれたまま通す。
    CSV の \\n は改行エスケープとして意図的に書かれているものなので、\\\\n に
    すると改行されず画面に \\n がそのまま出てしまう。一方それ以外の \\ を
    そのまま通すと壊れる。C:\\Users\\test は \\U が Unicode エスケープとして
    解釈されて "C:\\0sers\\test" になり、末尾の \\ は閉じ引用符をエスケープして
    ファイル全体がパース不能になる。そのため意味を持たない \\ だけ \\\\ にする。
    """
    def escape(match):
        valid, bare_backslash = match.group(1), match.group(2)
        if valid is not None:
            return valid  # 有効なエスケープはそのまま通す
        if bare_backslash is not None:
            return "\\\\"
        return '\\"'  # 裸の "

    return IOS_ESCAPE.sub(escape, value)


# 1: .strings が解釈する有効なエスケープ (そのまま通す)
# 2: それ以外の裸の \ (\\ にする)  3: 裸の " (\" にする)
# 有効なエスケープを先に食わせることで、\n の \ を裸の \ と誤認しないようにする
IOS_ESCAPE = re.compile(r'(\\(?:[abfnrtv"\'\\]|U[0-9a-fA-F]{4}))|(\\)|(")')


def build_android(header, keyed_rows, key_id):
    """Android 用 strings.xml の中身を組み立てる。"""
    lines = ["<!-- Generate by csv2strings -->\n", "<resources>"]

    for row in keyed_rows:
        entry_id = row.get(key_id, "")
        if not entry_id:
            continue

        if entry_id.startswith("#"):
            lines.append("\n    <!-- {} -->".format(section_name(entry_id)))
            continue

        value = unescape_entities(cell_value(row, header, entry_id), xml=True)

        # iOS 形式の書式指定子 (%@) を Android 形式 (%s) に置換する
        value = FORMAT_SPECIFIER_OBJC.sub(lambda m: m.group(0)[:-1] + "s", value)

        value = escape_android(value)

        if FORMAT_SPECIFIER.search(value):
            lines.append(
                '    <string name="{}" formatted="true">{}</string>'.format(entry_id, value)
            )
        else:
            lines.append('    <string name="{}">{}</string>'.format(entry_id, value))

    lines.append("</resources>")
    return "\n".join(lines)


# %@ / %1$@ など iOS 形式の書式指定子。末尾の @ を s に差し替えて Android 形式にする
FORMAT_SPECIFIER_OBJC = re.compile(r"%(?:\d+\$)?@")

# Android の String.format が解釈する書式指定子。"100%" のような裸の % は含まない。
# フラグにスペースを含めると "50% off" の "% o" を拾ってしまうため許容しない
FORMAT_SPECIFIER = re.compile(r"%(?:\d+\$)?[-+#0]*\d*(?:\.\d+)?[sdfeguxo]", re.IGNORECASE)


def escape_android(value):
    """strings.xml のリソース値として安全な形にエスケープする。

    ' と " は Android のリソース解析でエスケープが要る。裸の < > & は XML の
    エンティティにする。ただし &amp; など元から書かれていたエンティティは
    unescape_entities(xml=True) が残したものなので、二重エスケープしない。
    """
    # 既存のエンティティを退避してから & を変換し、あとで書き戻す
    kept = []

    def stash(match):
        kept.append(match.group(0))
        return "\x00"

    value = ENTITY.sub(stash, value)
    value = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    value = value.replace("'", "\\&apos;").replace('"', "\\&quot;")

    parts = value.split("\x00")
    restored = parts[0]
    for entity, part in zip(kept, parts[1:]):
        restored += entity + part
    return restored


# 既存の HTML/XML エンティティ (&amp; &#39; など)
ENTITY = re.compile(r"&(?:#\d+|#x[0-9a-fA-F]+|[a-zA-Z][a-zA-Z0-9]*);")


def section_name(entry_id):
    return entry_id.replace("# ", "").replace("#", "")


def unescape_entities(value, xml=False):
    """スプレッドシート由来の HTML エンティティを実体に戻す。

    GOOGLETRANSLATE の結果などに &nbsp; や &amp; がそのまま混ざることがあり、
    デコードしないと画面にエンティティの文字列がそのまま表示されてしまう。
    &nbsp; は U+00A0 ではなく半角スペースに落とす。表示上の差は無い一方、
    U+00A0 だと折り返しや trim の挙動が変わるため、従来の bin/csv2strings の
    出力に合わせている。&apos; は Android 側でエスケープし直すため変換しない。

    xml=True (strings.xml 向け) では &amp; を変換しない。XML では &amp; が
    アンパサンドの正しい表記であり、& に戻すとパースできない XML になる。
    """
    value = value.replace("&nbsp;", " ")
    if not xml:
        value = value.replace("&amp;", "&")
    return value


def cell_value(row, header, entry_id):
    """該当言語の値を取り出す。空欄なら未定義マーカーを返す。

    引用符の解除は csv モジュールが済ませているので、ここでは何もしない。
    値に含まれる " は本文の一部として扱い、出力形式ごとにエスケープする。
    """
    raw = row.get(header, "")
    if not raw.strip():
        return "{{{{Undefined: {}}}}}".format(entry_id)
    return raw.strip()


def read_csv(input_path):
    """CSV を読んでヘッダーと行の辞書リストを返す。"""
    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = [row for row in reader if any(cell.strip() for cell in row)]

    if not rows:
        return [], []

    headers = rows[0]
    keyed_rows = []
    for row in rows[1:]:
        keyed = {}
        for index, value in enumerate(row):
            if index < len(headers) and value.strip():
                keyed[headers[index]] = value
        keyed_rows.append(keyed)

    return headers, keyed_rows


def write_output(output_dir, header, text, os_name, file_name):
    path = os.path.join(output_dir, os_name, header)
    os.makedirs(path, exist_ok=True)

    file_path = os.path.join(path, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

    return file_path


def run(input_path, output_dir):
    if not os.path.isfile(input_path):
        print("Error! Source file not found.", file=sys.stderr)
        return 1
    if not os.path.isdir(output_dir):
        print("Error! Destination directory not found.", file=sys.stderr)
        return 1

    try:
        headers, keyed_rows = read_csv(input_path)
    except (UnicodeDecodeError, csv.Error, OSError) as e:
        print("Error! Source file can not read. ({})".format(e), file=sys.stderr)
        return 1

    if not headers:
        print("Error! Source file is empty.", file=sys.stderr)
        return 1

    key_id = headers[0]

    for header in headers[1:]:
        if not header:
            continue
        print("header {}".format(header))

        try:
            write_output(
                output_dir,
                header,
                build_ios(header, keyed_rows, key_id),
                "ios",
                "Localizable.strings",
            )
            write_output(
                output_dir,
                header,
                build_android(header, keyed_rows, key_id),
                "android",
                "strings.xml",
            )
        except OSError as e:
            print("Error! Can not write output. ({})".format(e), file=sys.stderr)
            return 1

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="generates Localizable.strings and strings.xml from a csv file."
    )
    parser.add_argument("source", help="source csv file path")
    parser.add_argument("output", help="output directory path")
    args = parser.parse_args()

    print("src: {}".format(args.source))
    print("dst: {}".format(args.output))

    return run(args.source, args.output)


if __name__ == "__main__":
    sys.exit(main())

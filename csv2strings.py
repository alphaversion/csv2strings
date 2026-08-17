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

        value = cell_value(row, header, entry_id)
        lines.append('"{}" = "{}";'.format(entry_id, unescape_entities(value)))

    return "\n".join(lines)


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

        # 書式指定子を含む場合は iOS 形式 (%@) を Android 形式 (%s) に置換する
        if "%" in value:
            value = value.replace("%@", "%s")
            for index in range(1, 5):
                value = value.replace("%{}$@".format(index), "%{}$s".format(index))
            value = value.replace("'", "\\&apos;")
            lines.append(
                '    <string name="{}" formatted="true">{}</string>'.format(entry_id, value)
            )
        else:
            value = value.replace("'", "\\&apos;")
            lines.append('    <string name="{}">{}</string>'.format(entry_id, value))

    lines.append("</resources>")
    return "\n".join(lines)


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
    """該当言語の値を取り出す。空欄なら未定義マーカーを返す。"""
    raw = row.get(header, "")
    if not raw.strip():
        return "{{{{Undefined: {}}}}}".format(entry_id)
    return raw.replace('"', "").strip()


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
    except UnicodeDecodeError:
        print("Error! Source file can not read.", file=sys.stderr)
        return 1

    if not headers:
        print("Error! Source file is empty.", file=sys.stderr)
        return 1

    key_id = headers[0]

    for header in headers[1:]:
        if not header:
            continue
        print("header {}".format(header))

        write_output(
            output_dir, header, build_ios(header, keyed_rows, key_id), "ios", "Localizable.strings"
        )
        write_output(
            output_dir, header, build_android(header, keyed_rows, key_id), "android", "strings.xml"
        )

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

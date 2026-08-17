# csv2strings

generates Localizable.strings and strings.xml.

## csv2strings.py (推奨)

Python 3 標準ライブラリのみで動作します。macOS / Linux / Windows で利用可能です。

```
python3 csv2strings.py {source path}.csv {output directory path}
```

出力先には `{output}/ios/{言語}/Localizable.strings` と
`{output}/android/{言語}/strings.xml` が生成されます。

## csv2strings (Swift / macOS 専用)

```
csv2strings {source path}.csv {output directory path}
```

### example csv file

| id | ja | en | ko | zh-Hans | zh-Han
| -- | -- | -- | -- | -- | --
| # common |   |   |   |   |  
| ok | OK | OK |   |   |  
| cancel | キャンセル | Cancel |   |   |  
| close | 閉じる | Close |   |   |  
| save | 保存 | Save |   |   |  
| done | 完了 | Done |   |   |  
| # settings |   |   |   |   |  
| settings_title | 設定 | Settings | 설정 | 设置 | 設定


## using

* [CSwiftV](https://github.com/Daniel1of1/CSwiftV)

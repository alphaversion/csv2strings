//
//  main.swift
//  csv2strings
//
//  Created by KENJI WADA on 2019/07/19.
//  Copyright © 2019 jp.co.alphaversion. All rights reserved.
//

import Foundation

let DEBUG = false

let arguments = Array((ProcessInfo.processInfo.arguments[1..<ProcessInfo.processInfo.arguments.count]))
if arguments.count < 2 {
    print("csv2strings {source path}.csv {output directory path}")
    if !DEBUG {
        exit(0)
    }
}

let inputPath: String
let outputDir: String
if DEBUG {
    inputPath = "/Users/ch3cooh/csv2strings/app.csv"
    outputDir = "/Users/ch3cooh/csv2strings/lang"
} else {
    inputPath = arguments[0]
    outputDir = arguments[1]
}

print("src: \(inputPath)")
print("dst: \(outputDir)")

Process.run(inputFilePath: inputPath, outputDirPath: outputDir)

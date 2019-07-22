//
//  Process.swift
//  csv2strings
//
//  Created by KENJI WADA on 2019/07/19.
//  Copyright © 2019 jp.co.alphaversion. All rights reserved.
//

import Foundation

class Process {
    
    static func run(inputFilePath: String, outputDirPath: String) {
        if !FileManager.default.fileExists(atPath: inputFilePath) {
            print("Error! Source file not found.")
            return
        }
        if !exsitsDirectory(atPath: outputDirPath) {
            print("Error! Destination file not found.")
            return
        }
        
        guard
            let data = FileManager.default.contents(atPath: inputFilePath),
            let csvStr = String(data: data, encoding: .utf8)
            else {
                print("Error! Source file can not read.")
                return
        }
        
        let csv = CSwiftV(with: csvStr)
        let keyId = csv.headers[0]
        
        for header in csv.headers[1..<csv.headers.count] {
            guard !header.isEmpty else {
                continue
            }
            print("header \(header)")
  
            var destIOS = [String]()
            destIOS.append("/* \n  Localizable.strings\n  \(header)\n  \n  Generate by csv2strings\n*/\n")
            var destAndroid = [String]()
            destAndroid.append("<!-- Generate by csv2strings -->\n")
            destAndroid.append("<resources>")

            csv.keyedRows?.forEach({ (row) in
                guard let id = row[keyId], !id.isEmpty else {
                    return
                }
                
                if id.hasPrefix("#") {
                    var separator = id.replacingOccurrences(of: "# ", with: "")
                    separator = separator.replacingOccurrences(of: "#", with: "")
                    
                    destIOS.append("\n// MARK: - \(separator)")
                    destAndroid.append("\n    <!-- \(separator) -->")
                    return
                }
                
                let value: String
                if let str = row[header] {
                    value = str.replacingOccurrences(of: "\"", with: "")
                } else {
                    value = "{{Undefined String: \(id)}}"
                }
                
                destIOS.append("\"\(id)\" = \"\(value)\";")
                
                if value.contains("%") {
                    let v = value.replacingOccurrences(of: "%@", with: "%s")
                    destAndroid.append("    <string name=\"\(id)\" formatted=\"true\">\(v)</string>")
                } else {
                    destAndroid.append("    <string name=\"\(id)\">\(value)</string>")
                }
            })
            destAndroid.append("</resources>")
            
            output(dirPath: outputDirPath, header: header, text: destIOS.joined(separator: "\n"), os: "ios")
            output(dirPath: outputDirPath, header: header, text: destAndroid.joined(separator: "\n"), os: "android")
        }
    }
    
    private static func output(dirPath: String, header: String, text: String, os: String) {
        let path = "\(dirPath)/\(os)/\(header)"
        
        if !exsitsDirectory(atPath: path) {
            let url = URL(fileURLWithPath: path, isDirectory: true)
            try! FileManager.default.createDirectory(at: url, withIntermediateDirectories: true, attributes: nil)
        }
        
        let fileName: String
        if os == "android" {
            fileName = "strings.xml"
        } else {
            fileName = "Localizable.strings"
        }
 
        let filePath = path.append(pathComponent: fileName)
        if FileManager.default.fileExists(atPath: filePath) {
            try! FileManager.default.removeItem(atPath: filePath)
        }

        FileManager.default.createFile(atPath: filePath, contents: text.data(using: .utf8), attributes: nil)
    }
    
    private static func exsitsDirectory(atPath path: String) -> Bool {
        let isDirectory = UnsafeMutablePointer<ObjCBool>.allocate(capacity: 1)
        isDirectory[0] = true
        
        if FileManager.default.fileExists(atPath: path, isDirectory: isDirectory) {
            return true
        } else {
            return false
        }
    }
}


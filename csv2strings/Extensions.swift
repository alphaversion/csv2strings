//
//  Extensions.swift
//  csv2strings
//
//  Created by KENJI WADA on 2019/07/19.
//  Copyright © 2019 jp.co.alphaversion. All rights reserved.
//

import Foundation

extension String {

    func append(pathComponent str: String) -> String {
        return (self as NSString).appendingPathComponent(str)
    }

}

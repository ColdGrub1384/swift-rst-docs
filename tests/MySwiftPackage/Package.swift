// swift-tools-version: 6.2
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "MySwiftPackage",
    products: [
        .library(
            name: "MySwiftLibrary",
            targets: ["MySwiftLibrary"]
        ),
        .library(
            name: "MyOtherSwiftLibrary",
            targets: ["MyOtherSwiftLibrary"]
        ),
    ],
    targets: [
        .target(
            name: "MySwiftLibrary"
        ),
        .target(
            name: "MyOtherSwiftLibrary",
            dependencies: ["MySwiftLibrary"]
        ),
    ]
)

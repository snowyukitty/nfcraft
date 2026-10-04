// swift-tools-version:5.9
//
// Platform-neutral core of the iPhone writer: the NTAG215 encoder, command
// layer, per-tap decision logic and destination history. It imports nothing
// from Core NFC or UIKit, so it builds and tests on Linux and Windows as well
// as in Xcode. The Core NFC adapter belongs to the app target, which needs a
// Mac; see ../README.md.
import PackageDescription

let package = Package(
    name: "NfcraftKit",
    platforms: [.iOS(.v15), .macOS(.v12)],
    products: [
        .library(name: "NfcraftKit", targets: ["NfcraftKit"]),
    ],
    targets: [
        .target(name: "NfcraftKit"),
        .executableTarget(name: "nfcraft-parity", dependencies: ["NfcraftKit"]),
        .testTarget(name: "NfcraftKitTests", dependencies: ["NfcraftKit"]),
    ]
)

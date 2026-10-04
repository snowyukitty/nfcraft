import Foundation

/// The shared inputs in ios/tools/parity-cases.json, read the same way by
/// ios/tools/ref.py. Only this executable uses Foundation; the library does not.
struct ParityCases {
    let urls: [String]
    let bad: [String]
    let edge: [String]
    let stricter: [String]

    init() {
        guard CommandLine.arguments.count == 2 else {
            FileHandle.standardError.write(Data("usage: nfcraft-parity <parity-cases.json>\n".utf8))
            exit(2)
        }
        let url = URL(fileURLWithPath: CommandLine.arguments[1])
        guard let data = try? Data(contentsOf: url),
              let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let urls = object["urls"] as? [String],
              let bad = object["bad"] as? [String],
              let edge = object["edge"] as? [String],
              let stricter = object["stricter"] as? [String] else {
            FileHandle.standardError.write(Data("cannot read parity cases\n".utf8))
            exit(2)
        }
        self.urls = urls
        self.bad = bad
        self.edge = edge
        self.stricter = stricter
    }
}

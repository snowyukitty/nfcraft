// Prints the Swift encoder's output in exactly the format of
// ios/tools/ref.py, so ios/tools/check.sh can diff the two.
import NfcraftKit

let cases = ParityCases()

func render(_ value: Bool) -> String { value ? "true" : "false" }

for url in cases.urls {
    print("URL " + url)
    print("  validate " + (Ndef.validate(url) ?? "null"))
    let area = try Ndef.encodeArea(url)
    print("  area " + Ndef.hex(area))
    let plan = try Ndef.writePlan(url)
    print("  plan " + plan.map { Ndef.hex([UInt8($0.page)]) + ":" + Ndef.hex($0.data) }.joined(separator: " "))
    var full = [UInt8](repeating: 0, count: Ndef.capacity)
    full.replaceSubrange(0..<area.count, with: area)
    print("  decode " + (Ndef.decodeArea(full) ?? "None"))
    print("  empty " + render(Ndef.isEmpty(full)))
}

// Indexed, not echoed: some cases are deliberately non-ASCII and a console
// encoding must not show up as an encoder difference.
for (i, url) in cases.bad.enumerated() {
    print("BAD[\(i)] rejected " + render(Ndef.validate(url) != nil))
}
for (i, url) in cases.edge.enumerated() {
    print("EDGE[\(i)] rejected " + render(Ndef.validate(url) != nil))
}
for (i, url) in cases.stricter.enumerated() {
    print("STRICTER[\(i)] rejected " + render(Ndef.validate(url) != nil))
}

var blank = [UInt8](repeating: 0, count: Ndef.capacity)
print("blank empty " + render(Ndef.isEmpty(blank)))
blank[0] = 0x03; blank[1] = 0x00; blank[2] = 0xFE
print("emptytlv empty " + render(Ndef.isEmpty(blank)))
print("emptytlv hides " + render(Ndef.hidesDataUnderEmptyTlv(blank, plannedLength: 24)))
blank[9] = 0x41
print("emptytlv+data empty " + render(Ndef.isEmpty(blank)))
print("emptytlv+data hides " + render(Ndef.hidesDataUnderEmptyTlv(blank, plannedLength: 24)))
print("emptytlv+data hides(short) " + render(Ndef.hidesDataUnderEmptyTlv(blank, plannedLength: 8)))

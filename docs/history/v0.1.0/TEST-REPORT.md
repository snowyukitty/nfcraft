# Test report — 2026-09-05

## Executed in the build environment

| Check | Actual result |
|---|---|
| Python suite | **76 tests passed**; standard-library unittest |
| Public Worker handler suite | **13 tests passed**; Node built-in test runner with mocked D1 |
| Python source compilation | Passed |
| Front-end JavaScript syntax | Passed `node --check` |
| Worker JavaScript syntax | Passed `node --check` |
| Live local daemon + CLI status / audit | Passed against the running demo workspace |
| Live local daemon + MCP stdio | Initialization and `nfc_status` call passed; notifications did not emit responses |
| Manifest-to-SQL CLI | Export converted; resulting schema/data imported into ordinary in-memory SQLite |
| GUI workflow | Six simulated cards verified, including one interrupted write recovered with the same identity |
| GUI exports | Public manifest with six simulated routes downloaded; QR SVG downloaded |
| GUI scripting | No captured JavaScript page errors |
| Responsive workbench rendering | No horizontal document overflow at 390 px viewport |

The Python suite covers URL/NDEF vectors, safe page ranges, reservation-before-write, duplicate rejection, held-card latching, foreign/locked/wrong-chip refusal, configuration guards, approval expiry, mid-write pause, readback mismatch, quarantine/recovery, restart handling, audit corruption, backups, CSV escaping, role-separated HTTP APIs and a narrow MCP protocol surface. The Worker suite checks route responses, suspended/unknown cards, profile escaping, vCard folding/injection prevention, method restrictions and malformed profile handling.

## Important browser-test limitation

The container's managed Chromium blocks navigation to local URLs and file URLs. To inspect and exercise the actual UI, the test harness rendered the shipped HTML/CSS/JavaScript in a blank page and bridged its `fetch` calls through Python to the real loopback server. Browser storage was supplied by the harness because the blank page has an opaque origin. The production app files were not modified for this harness.

Therefore these are genuine interactive UI/rendering tests against the demo engine, **not proof that an ordinary browser navigation, deployed CSP integration, Windows browser or pywebview launch works end-to-end**. Direct HTTP authorization/Host/Origin/CSP-header behavior was tested separately in the Python suite. Full normal-browser testing remains part of local acceptance.

The screenshots show the app's simulation workspace. Their times are simulated operation times, not NFC reader throughput.

## Not performed

- Any physical NFC read or write, reader connection, RF interruption or measured card throughput.
- ACR1552U transparent protocol/ACK verification on a real reader or specific firmware.
- Windows, macOS or physical Linux PC/SC integration tests.
- A compiled, signed Windows installer or optional pywebview/pystray execution.
- End-to-end integration inside an actual Codex or Claude MCP client.
- Android Web NFC, a native Android app, or an iPhone scan/vCard import.
- QR scanning from printed/engraved wood or final materials testing.
- Wrangler local emulation, live Cloudflare deployment, D1 remote SQL import, DNS or TLS setup.
- Authentication/anti-cloning, tamper-proof audit or database encryption. These are not claimed features.

`hardware_qualified` remains false and the hardware adapter remains experimental/read-only by default. Passing tests do not remove these limitations.

## Reproduce

```sh
python -m unittest discover -s tests -v
python -m compileall -q nfc_card_ops
node --check nfc_card_ops/web/app.js
node --check cloudflare/worker.mjs
node --test cloudflare/worker.test.mjs
```

Captured final logs and sanitized browser-result metadata are in `test-evidence/`. Hardware acceptance is a separate unexecuted template in `examples/PILOT-ACCEPTANCE.md`.

## Build environment versions

Linux container; Python 3.13.5, Node v22.16.0, playwright 1.57.0, qrcode 8.2. Optional hardware/desktop dependencies were not installed.

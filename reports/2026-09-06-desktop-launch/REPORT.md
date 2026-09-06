# nfcraft 0.2.2 — repair the actual desktop launch

## Incident and cause

The owner reported that the PowerShell-based desktop shortcut did nothing. Read-only inspection found the previous `nfcraft.exe` still listening, with its `nfcraft` window hidden. The `-WindowStyle Hidden` startup flag applied to the WinForms window as well as the console. Separately, IconFlow's shortcut helper assigns `WindowStyle = 7` (minimized), which is inappropriate for this native app.

The previous checkpoint tested shortcut properties and a different process launch, but did not test the installed shortcut's visible/non-minimized window. That evidence gap is explicitly corrected here. The old hidden process was confirmed unarmed using the agent status API, then closed through its own window's WM_CLOSE. No card write, UI approval, database deletion or migration was performed.

## Change

- `nfcraft-desktop.exe` is a Windows GUI-subsystem executable with an unconditional desktop entrypoint. It needs no PowerShell launcher, console or `--desktop` flag. Existing `nfcraft.exe`, CLI/MCP and browser use remain available.
- `packaging/windows.spec` uses one Analysis/PYZ, two explicit script entrypoints and one COLLECT dependency folder. The GUI and console share dependencies without guessing mode from executable names or standard-stream availability. Specification reference: https://pyinstaller.org/en/latest/spec-files.html.
- `nfcraft/desktop_app.py` handles missing standard streams and shows startup errors in a native message box after core cleanup. It never persists the operator URL or raw dependency logs. Unexpected exception text is excluded from the user-facing fallback to avoid leaking capabilities.
- The core exposes an optional error callback; CLI behavior and security boundaries remain intact. Four new tests cover absent streams, an occupied workspace, an occupied port with cleanup, and exception-content privacy.
- The desktop shortcut directly targets `dist/nfcraft/nfcraft-desktop.exe`, with empty arguments and normal window style **1**. `scripts/install-desktop-shortcut.ps1` is a repeatable installation helper, not the app's runtime launcher. It uses IconFlow's icon/shortcut creation, then validates the native window style and exact arguments. The shared toolkit was not modified.
- `scripts/smoke_shortcut_windows.py` exercises a real `.lnk` through ShellExecute, checks the PE GUI subsystem, visible/non-minimized window and normal dimensions, then closes only its own temporary demo process. Existing native lifecycle tests now require a visible window and use the GUI executable by default.

## Verification

Baseline: 114 Python / 16 Worker PASS (`.local/evidence/launch-baseline.txt`). Final build verification: **118 Python / 16 Worker** PASS, with compile, daemon/CLI/MCP and JS checks (`.local/verification/`). Native and shortcut tests require Windows and are not physical NFC acceptance.

| Result | Evidence |
|---|---|
| PASS | Four startup/error regressions (`tests/test_desktop_app.py`) |
| PASS | Shared GUI/console build, `launch-build-final.txt` |
| PASS | Packaged desktop/tray visible launch, close and persistence, `launch-native.txt`; fixture `native package 測試 2ds670wv` |
| PASS | Actual `.lnk` ShellExecute, non-minimized 960x700-or-larger window, clean close, `launch-shortcut.txt` |
| PASS | Packaged library workflow, `launch-library.txt`; fixture `library-lximjE` |
| PASS | Packaged offline bilingual guide, `launch-guide.txt` |
| PASS | Installed owner desktop shortcut opens a visible, non-minimized **1320x920** window; `launch-installed-shortcut.json` |

The installed app was left open for the owner. Verification inspected only native window metadata; no operator capability was extracted and no UI operation or write was automated in the normal workspace.

Intermediate failures are retained locally. An initial shared-script prototype inferred GUI mode from standard streams; inherited handles made that unreliable, so it was replaced with explicit entrypoints. A Unicode test argument passed through shortcut COM/native-shell transport did not round-trip. The delivered shortcut has no arguments; test-only arguments use an ASCII path with spaces and are verified exactly. Native package/workspace Unicode coverage remains separate. Windows PowerShell 5.1 also split nested quotes when forwarding arguments to a native command, so the installation helper assigns arguments through COM after IconFlow creates the link. No toolkit-level compatibility claim is made.

## Operations and handoff

Double-click **nfcraft** on the desktop, or `dist/nfcraft/nfcraft-desktop.exe`. Close the native window to stop. The optional console/browser entry remains `nfcraft.exe`; `Start Desktop.cmd` remains a developer/source launcher. The bilingual guide is available through its existing desktop shortcut or the app's Guide link.

Current version: 0.2.2, unsigned portable Windows app. Keep the complete `dist/nfcraft` folder. Prior ZIPs remain available. No journal/public schema or card identity changed. Hardware qualification, phone/printed-QR QA, signing, clean-machine acceptance and cloud destination approval remain separate outstanding work.

Package: `dist/nfcraft-0.2.2-windows-unsigned.zip`, 29,114,627 bytes, SHA-256 `84aabeeab04d94f389bf728de9ca96ca2a1ad05cc76afa6b987d6137e89b3c6b`.
GUI executable SHA-256: `289b1a7a1d0067bdbba1e144cc5c3c349791becdec02d8edbc01c6e36e1bd8d3`.
Console executable SHA-256: `45efc5834a5775e68e1fd4a88702283ed5e6eb68d24569d1fcb9aeb63bc8af34`.

GitHub checkpoint: the existing private `snowyukitty/nfcraft` repository, both `main` and the work branch. No release, visibility or deployment change. Source and CI evidence are attached to the final commit. Staged credential scan and whitespace check pass. Atlas confirmed release of the `nfcraft` lease held by `codex-nfcraft` after local verification. No subagents.

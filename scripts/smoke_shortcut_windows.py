"""Exercise a real .lnk through Windows ShellExecute with isolated demo data."""
import ctypes
import base64
from ctypes import wintypes
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    # WScript.Shell may ANSI-convert Arguments; the delivered shortcut has none.
    # Keep test-only data arguments ASCII; native lifecycle tests cover Unicode paths.
    root = Path(tempfile.mkdtemp(prefix='shortcut space ', dir=ROOT / '.local/evidence'))
    executable = ROOT / 'dist/nfcraft/nfcraft-desktop.exe'
    data = executable.read_bytes()
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    assert struct.unpack_from('<H', data, pe + 24 + 68)[0] == 2, 'A Windows GUI subsystem executable is required'
    def quote(value):
        return "'" + str(value).replace("'", "''") + "'"
    command = (f"& {quote(ROOT / 'scripts/install-desktop-shortcut.ps1')} -Name 'nfcraft test' "
        f"-Destination {quote(root)} -Arguments {quote('--data-dir ' + chr(34) + str(root / 'workspace') + chr(34) + ' --port 0')}")
    installed = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-EncodedCommand',
        base64.b64encode(command.encode('utf-16-le')).decode('ascii')],
        capture_output=True)
    assert installed.returncode == 0, (installed.stdout + installed.stderr).decode('utf-8', 'replace')

    class ShellExecuteInfo(ctypes.Structure):
        _fields_ = [('cbSize', wintypes.DWORD), ('fMask', wintypes.ULONG), ('hwnd', wintypes.HWND),
            ('lpVerb', wintypes.LPCWSTR), ('lpFile', wintypes.LPCWSTR), ('lpParameters', wintypes.LPCWSTR),
            ('lpDirectory', wintypes.LPCWSTR), ('nShow', ctypes.c_int), ('hInstApp', wintypes.HINSTANCE),
            ('lpIDList', ctypes.c_void_p), ('lpClass', wintypes.LPCWSTR), ('hkeyClass', wintypes.HKEY),
            ('dwHotKey', wintypes.DWORD), ('hIcon', wintypes.HANDLE), ('hProcess', wintypes.HANDLE)]

    shell = ctypes.WinDLL('shell32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    user = ctypes.WinDLL('user32', use_last_error=True)
    shell.ShellExecuteExW.argtypes = [ctypes.POINTER(ShellExecuteInfo)]
    kernel.GetProcessId.argtypes = [wintypes.HANDLE]
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user.IsWindowVisible.argtypes = [wintypes.HWND]
    user.IsIconic.argtypes = [wintypes.HWND]
    user.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    info = ShellExecuteInfo(cbSize=ctypes.sizeof(ShellExecuteInfo), fMask=0x40,
        lpVerb='open', lpFile=str(root / 'nfcraft test.lnk'), nShow=1)
    assert shell.ShellExecuteExW(ctypes.byref(info)), ctypes.get_last_error()
    pid = kernel.GetProcessId(info.hProcess)
    assert pid
    handle = None
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            found = []
            observed = []
            @callback_type
            def visit(hwnd, _):
                owner = wintypes.DWORD(); user.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
                if owner.value == pid:
                    title = ctypes.create_unicode_buffer(100); user.GetWindowTextW(hwnd, title, 100)
                    observed.append((title.value, bool(user.IsWindowVisible(hwnd))))
                    if title.value == 'nfcraft' and user.IsWindowVisible(hwnd): found.append(hwnd)
                return True
            user.EnumWindows(visit, 0)
            if found:
                handle = found[0]; break
            assert kernel.WaitForSingleObject(info.hProcess, 0) == 258, 'App exited before showing a window'
            time.sleep(0.2)
        assert handle, f'Shell-opened shortcut did not show the app; windows: {observed}'
        time.sleep(3)
        assert not user.IsIconic(handle), 'Shortcut must not minimize the app'
        bounds = wintypes.RECT(); user.GetWindowRect(handle, ctypes.byref(bounds))
        assert bounds.right - bounds.left >= 960 and bounds.bottom - bounds.top >= 700
        assert (root / 'workspace/demo/agent-runtime.json').exists()
        assert user.PostMessageW(handle, 0x0010, 0, 0)
        assert kernel.WaitForSingleObject(info.hProcess, 15000) == 0, 'App did not close cleanly'
        assert not (root / 'workspace/demo/agent-runtime.json').exists()
        result = {'result':'PASS', 'checks':['PE GUI subsystem', 'real .lnk ShellExecute',
            'visible, non-minimized native window', 'normal window dimensions',
            'default desktop without --desktop argument', 'clean close'],
            'scope':'temporary demo data only'}
        (root / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2))
    finally:
        if kernel.WaitForSingleObject(info.hProcess, 0) == 258:
            subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'], capture_output=True)
        kernel.CloseHandle(info.hProcess)


if __name__ == '__main__':
    main()

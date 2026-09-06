# Authored build recipe: two entrypoints share one dependency directory.
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files

root = Path(SPECPATH).parent
datas = collect_data_files('nfcraft')
binaries = []
hiddenimports = ['pystray._win32']
for package in ('webview', 'smartcard'):
    package_data, package_binaries, package_imports = collect_all(package)
    datas += package_data
    binaries += package_binaries
    hiddenimports += package_imports
a = Analysis([str(root / 'run.py'), str(root / 'run_desktop.py')], pathex=[str(root)], binaries=binaries,
             datas=datas, hiddenimports=hiddenimports, noarchive=False)
pyz = PYZ(a.pure)
options = dict(exclude_binaries=True, icon=str(root / 'nfcraft/web/icons/build/icon.ico'),
               debug=False, strip=False, upx=True)
# Keep shared runtime hooks, but execute exactly one application entrypoint.
console_scripts = [entry for entry in a.scripts if entry[0] != 'run_desktop']
desktop_scripts = [entry for entry in a.scripts if entry[0] != 'run']
console = EXE(pyz, console_scripts, [], name='nfcraft', console=True, **options)
desktop = EXE(pyz, desktop_scripts, [], name='nfcraft-desktop', console=False, **options)
COLLECT(console, desktop, a.binaries, a.datas, name='nfcraft', strip=False, upx=True)

# PyInstaller spec: one-file executable.  Build with tools/build.sh (or: pyinstaller vpxconfig.spec).
# Relative paths below are relative to this file.
a = Analysis(
    ["run.py"],
    pathex=["."],
    datas=[
        ("web", "web"),               # the wizard's pages, scripts and styles
        ("VPinballX.ini", "."),       # the base ini: also defines every field's label, default and options
    ],
    excludes=["tkinter"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="vpxconfig",
    console=True,       # a local web server: it prints its address and stops with Ctrl+C
    upx=False,
)

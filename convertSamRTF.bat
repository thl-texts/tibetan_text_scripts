@echo off

for %%f in (in\*.rtf) do (
    echo Doing %%~nf
    copy "%%f" "out\%%~nf.rtf"
    c:\unicdocp\udp.exe -x rtf "out\%%~nf.rtf"
    del "out\%%~nf.BAK"
)

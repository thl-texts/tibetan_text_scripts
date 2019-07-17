@echo off

for %%f in (RTFs\*.rtf) do (
    echo Doing %%~nf
    copy %%f Unicode\%%~nf.rtf
    c:\unicdocp\udp.exe -x rtf Unicode\%%~nf.rtf
    del Unicode\%%~nf.BAK
)
@echo off
REM 编译脚本 - 编译 zuoye-paiban 四件套
REM 用法：build.bat <工作目录> <输出文件名前缀>

set WORK_DIR=%~1
set NAME=%~2

if "%WORK_DIR%"=="" (
    echo 错误：未指定工作目录
    exit /b 1
)

if "%NAME%"=="" (
    echo 错误：未指定输出文件名
    exit /b 1
)

cd /d "%WORK_DIR%\output"

echo 正在编译 %NAME% ...

REM 第一遍编译（丢弃输出）
for %%v in (student teacher student_onepage) do (
    echo   编译 %%v ...
    xelatex -interaction=nonstopmode -output-directory="%WORK_DIR%\output" "%NAME%_%%v.tex" >nul 2>&1
)

REM 第二遍编译（解析页码引用）
for %%v in (student teacher student_onepage) do (
    echo   编译 %%v (第2遍)...
    xelatex -interaction=nonstopmode -output-directory="%WORK_DIR%\output" "%NAME%_%%v.tex"
)

REM 清理辅助文件
del /q "%WORK_DIR%\output\*.aux" "%WORK_DIR%\output\*.log" "%WORK_DIR%\output\*.out" 2>nul

echo 编译完成！
echo PDF 文件位于：%WORK_DIR%\output\

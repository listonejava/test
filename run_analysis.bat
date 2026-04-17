@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║         SpringBoot + Vue 全链路静态分析工具 v2.0               ║
echo ║     业务功能 → 前端请求 → 后端 API → 服务层 → 存储层 → 数据结构    ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM ==================== 配置区域 ====================
REM 请根据实际项目结构修改以下路径
SET BACKEND_PATH=E:\workspace-analysis\AI4DC\05 源码\backend
SET FRONTEND_PATH=E:\workspace-analysis\AI4DC\05 源码\frontend
SET OUTPUT_DIR=E:\workspace-analysis\AI4DC\05 源码\analysis_output
SET PROJECT_NAME=数币工程
REM ================================================

echo 📁 项目配置:
echo   后端路径：%BACKEND_PATH%
echo   前端路径：%FRONTEND_PATH%
echo   输出目录：%OUTPUT_DIR%
echo   项目名称：%PROJECT_NAME%
echo.

REM 检查后端目录
if not exist "%BACKEND_PATH%" (
    echo ❌ 错误：后端项目路径不存在：%BACKEND_PATH%
    echo    请编辑本文件，修改 BACKEND_PATH 为正确的后端项目路径
    pause
    exit /b 1
)

REM 检查前端目录
if not exist "%FRONTEND_PATH%" (
    echo ❌ 错误：前端项目路径不存在：%FRONTEND_PATH%
    echo    请编辑本文件，修改 FRONTEND_PATH 为正确的前端项目路径
    pause
    exit /b 1
)

echo ✅ 路径检查通过
echo.

REM 检查 Python
where python >nul 2>nul
if errorlevel 1 (
    echo ❌ 错误：未找到 Python，请确保已安装 Python 3.12+ 并添加到 PATH
    echo    下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 🐍 Python 环境检查通过
python --version
echo.

REM 检查工具文件
SET TOOL_PATH=%~dp0fullchain_analyzer.py
if not exist "%TOOL_PATH%" (
    echo ❌ 错误：未找到分析工具：%TOOL_PATH%
    echo    请将 fullchain_analyzer.py 放置到与本批处理相同的目录
    pause
    exit /b 1
)

echo 🔧 工具文件存在：%TOOL_PATH%
echo.

REM 创建输出目录
if not exist "%OUTPUT_DIR%" (
    echo 📂 创建输出目录：%OUTPUT_DIR%
    mkdir "%OUTPUT_DIR%"
)

REM 执行分析
echo ════════════════════════════════════════════════════════════
echo 🚀 开始执行全链路静态分析...
echo ════════════════════════════════════════════════════════════
echo.

python "%TOOL_PATH%" ^
  --backend "%BACKEND_PATH%" ^
  --frontend "%FRONTEND_PATH%" ^
  --output "%OUTPUT_DIR%" ^
  --project-name "%PROJECT_NAME%"

if errorlevel 1 (
    echo.
    echo ❌ 分析过程中出现错误
    pause
    exit /b 1
)

echo.
echo ════════════════════════════════════════════════════════════
echo ✅ 分析完成！
echo ════════════════════════════════════════════════════════════
echo.
echo 📊 报告文件位置：%OUTPUT_DIR%
echo.
echo 📄 生成的 JSON 报告:
dir /b "%OUTPUT_DIR%\*.json" 2>nul | findstr /i ".json"
echo.
echo 💡 提示：可以使用文本编辑器或 JSON 查看器打开报告文件
echo.

pause

exit /b 0

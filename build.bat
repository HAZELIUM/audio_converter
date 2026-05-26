@echo off
echo ============================================
echo  Sound Converter v2 - EXE Builder
echo ============================================
echo.

set SCRIPT_DIR=%~dp0
set DIST_DIR=%SCRIPT_DIR%dist

echo [1/2] Building sound_converter.exe ...
pyinstaller ^
  --onedir ^
  --windowed ^
  --name sound_converter ^
  --distpath "%DIST_DIR%" ^
  --workpath "%SCRIPT_DIR%build_temp\sound_converter" ^
  --specpath "%SCRIPT_DIR%build_temp" ^
  "%SCRIPT_DIR%sound converter.py"

if errorlevel 1 (
  echo ERROR: sound_converter build failed.
  pause
  exit /b 1
)
echo [1/2] Done.
echo.

echo [2/2] Building sound_converter_transparent.exe ...
pyinstaller ^
  --onedir ^
  --windowed ^
  --name sound_converter_transparent ^
  --distpath "%DIST_DIR%" ^
  --workpath "%SCRIPT_DIR%build_temp\sound_converter_transparent" ^
  --specpath "%SCRIPT_DIR%build_temp" ^
  "%SCRIPT_DIR%sound converter test.py"

if errorlevel 1 (
  echo ERROR: sound_converter_transparent build failed.
  pause
  exit /b 1
)
echo [2/2] Done.
echo.

echo ============================================
echo  Build complete! Output is in:
echo  %DIST_DIR%
echo    - sound_converter\sound_converter.exe
echo    - sound_converter_transparent\sound_converter_transparent.exe
echo ============================================
echo.
echo You can safely delete the "build_temp" folder.
pause

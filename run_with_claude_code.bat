@echo off
echo 🚀 Xserver VPS 自動更新スクリプト (Claude Code統合版) を開始します
echo.

REM 必要なファイルの存在確認
if not exist "xserver_improved.py" (
    echo ❌ xserver_improved.py が見つかりません
    echo 💡 このスクリプトをxserver_improved.pyと同じフォルダで実行してください
    pause
    exit /b 1
)

if not exist "claude_code_integration.py" (
    echo ❌ claude_code_integration.py が見つかりません
    echo 💡 Claude Code統合機能が利用できません
    pause
    exit /b 1
)

echo ✅ 必要なファイルを確認しました

REM Claude Code CLIの可用性をチェック
claude --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Claude Code CLI が見つかりません
    echo 💡 以下の手順でClaude Code CLIをインストールしてください：
    echo    1. https://docs.anthropic.com/en/docs/claude-code/quickstart
    echo    2. インストール後、'claude --version' で動作確認
    echo.
    echo ⚠️  Claude Code統合機能なしで実行します
    pause
) else (
    echo ✅ Claude Code CLI が利用可能です
)

echo.
echo 📋 機能一覧:
echo    1. OCR (EasyOCR) による自動認証
echo    2. Claude API による自動認証
echo    3. Claude Code CLI による自動認証 (NEW!)
echo    4. 手動入力フォールバック
echo.
echo 🎯 更新タイミング最適化:
echo    - 24時間前から更新可能
echo    - 残り時間 + 2日間で期限延長
echo    - 設定可能な更新閾値 (デフォルト: 12時間前)
echo.

REM 設定確認
echo 📝 実行前に以下の設定を確認してください:
echo    - USERNAME (ユーザー名)
echo    - PASSWORD (パスワード)
echo    - SERVER_ID (サーバーID)
echo    - ANTHROPIC_API_KEY (環境変数、オプション)
echo.

set /p proceed="続行しますか? (Y/n): "
if /i "%proceed%" neq "Y" if /i "%proceed%" neq "" (
    echo 処理を中止しました
    pause
    exit /b 0
)

REM Python スクリプトを実行
echo.
echo 🚀 Python スクリプトを実行します...
python xserver_improved.py

REM 実行結果の確認
if %errorlevel% equ 0 (
    echo.
    echo ✅ スクリプトが正常に完了しました
) else (
    echo.
    echo ❌ スクリプトの実行中にエラーが発生しました
    echo 💡 エラーメッセージを確認してください
)

echo.
echo 📸 生成されたファイル:
if exist "captcha_screen.png" echo    - captcha_screen.png (画像認証のスクリーンショット)
if exist "captcha_cropped.png" echo    - captcha_cropped.png (切り取り済み画像認証)
if exist "captcha_processed.png" echo    - captcha_processed.png (OCR前処理済み画像)
if exist "captcha_debug_*.png" echo    - captcha_debug_*.png (デバッグ用画像)

echo.
pause
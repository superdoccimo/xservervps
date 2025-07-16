# Xserver無料VPS自動更新スクリプト (Gemini連携対応版)

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

Xserver無料VPSの「2日ごと手動更新」を、**GoogleのAI「Gemini」との連携**によって完全自動化し、永続利用を可能にするPythonスクリプトです。

## 🤖【最大の特徴】Gemini連携による画像認証の完全突破

Xserverが導入した、ひらがなの手書き文字による**画像認証（CAPTCHA）**。従来のOCR技術では読み取りが困難で、多くの自動化スクリプトがここで停止してしまいます。

このスクリプトは、その問題を**あなたとGeminiとの連携**という画期的な方法で解決します。

### ✨ 連携の仕組み

1.  **スクリプトが実行**され、更新プロセスを進めます。
2.  画像認証の画面に到達すると、まず内蔵のOCRで自動解析を試みます。
3.  **もしOCRが失敗すると、スクリプトはあなたに助けを求めます。**
    - `「Geminiと連携してください」`というメッセージと共に一時停止します。
4.  あなたは指示に従い、**新しいターミナルで連携用スクリプト (`solve_captcha.py`) を実行**します。
5.  連携スクリプトの案内に沿って、**Geminiに画像を見せます。**
6.  **Geminiが瞬時に画像を読み取り**、あなたに正しい6桁の数字を伝えます。
7.  あなたがその数字を入力すると、メインスクリプトに解答が渡され、**自動で更新が完了します。**

このハイブリッドシステムにより、**自動化の利便性**と**Geminiの高度な認識能力**を組み合わせ、100%に近い確率でサーバー更新を成功させることができます。

## 🚀 概要

2025年7月にリリースされたXserver無料VPSは高性能（4GB RAM、3コアCPU）ですが、2日ごとの手動更新が必要です。このスクリプトは、その更新プロセスを画像認証を含めて完全に自動化します。

### 💰 節約効果

- **Xserver VPS 6GBプラン**: 月額1,190円
- **無料VPS 4GBプラン**: 月額0円（このスクリプトで自動更新）
- **年間節約額**: **約14,000円**

## 📋 動作要件

- Python 3.7以上
- Google Chrome
- ChromeDriver
- Xserver無料VPSアカウント
- **Google Geminiのアカウント** (画像を見せるために必要です)

## 🛠️ インストール

### 1. リポジトリをクローン

```bash
git clone https://github.com/superdoccimo/xservervps.git
cd xservervps
```

### 2. 必要なパッケージをインストール

**画像認証対応のため、追加ライブラリが必要です。**

```bash
pip install -r requirements.txt
```
(`requirements.txt`には`selenium`, `easyocr`, `opencv-python`, `pillow`などが含まれます)

### 3. ChromeDriverをインストール

お使いのOSに合わせてChromeDriverをインストールし、PATHを通してください。

## ⚙️ 設定

スクリプト `xserver2.py` を開き、以下の項目をあなたの情報に書き換えてください。

```python
# ▼ 設定項目（必ず入力）
USERNAME = "your_username@example.com"  # ← 実際のユーザー名に変更
PASSWORD = "your_password"              # ← 実際のパスワードに変更
SERVER_ID = "40092988"                  # ← 実際のサーバーIDに変更

# ▼ 設定: 更新実行の条件（時間）
UPDATE_THRESHOLD_HOURS = 12  # 期限の何時間前から更新を実行するか
```

## 🚀 使用方法 (Gemini連携フロー)

1.  **メインスクリプトを実行**
    - ターミナルで `python xserver2.py` を実行します。スクリプトが自動でブラウザを操作し始めます。

2.  **Geminiの出番を待つ**
    - **OCRで自動成功した場合**: あなたは何もしなくてもOKです。更新は自動で完了します。
    - **OCRが失敗した場合**: スクリプトが一時停止し、コンソールに以下のようなメッセージが表示されます。
    ```
    🤖 OCRでの自動解決に失敗しました。Gemini連携モードに移行します。
    1. 新しいターミナルを開いてください。
    2. `python solve_captcha.py` を実行し、Geminiと連携してCAPTCHAを解決してください。
    3. このスクリプトは解答ファイルが作成されるまで待機します...
    ```

3.  **Geminiと連携する**
    - 指示に従い、**新しいターミナル**を開きます。
    - `python solve_captcha.py` を実行します。
    - 画面の指示に従い、指定された画像ファイル (`captcha_cropped.png`) をGeminiに見せてください。
    - Geminiが教えてくれた6桁の数字をターミナルに入力します。

4.  **自動で完了**
    - 数字を入力すると、待機していた `xserver2.py` が処理を自動で再開し、更新を完了させます。

## 🕒 定期実行の設定

cron (Linux/macOS) やタスクスケジューラー (Windows) を使って、`xserver2.py` を6〜12時間ごとに定期実行するように設定してください。Gemini連携が必要になった場合でも、ログファイルでメッセージを確認できます。

```bash
# (例) Linux/macOS (cron) で6時間ごとに実行
0 */6 * * * cd /path/to/xservervps && python xserver2.py >> update.log 2>&1
```

## 📖 詳細

本スクリプトの詳しい解説や背景については、以下の記事をご覧ください。

- **解説記事**: [Xserver無料VPSの「2日更新ルール」を自動化して永続利用する方法](https://minokamo.tokyo/2025/07/13/9135/)

近日中に、設定方法や動作の様子を解説するYouTube動画も公開予定です。お楽しみに！

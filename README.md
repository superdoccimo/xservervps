# Xserver無料VPS自動更新スクリプト

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

Xserver無料VPSの「2日ごと手動更新」を自動化し、永続利用を可能にするPythonスクリプトです。

## 🚀 概要

2025年7月にリリースされたXserver無料VPSは高性能（4GB RAM、3コアCPU）でありながら、2日ごとの手動更新が必要という制約があります。このスクリプトはSeleniumを使用してブラウザ操作を自動化し、更新処理を完全自動化します。

### 💰 節約効果

- **Xserver VPS 6GBプラン**: 月額1,190円
- **無料VPS 4GBプラン**: 月額0円（手動更新）
- **年間節約額**: 約14,000円

## ✨ 特徴

- 🤖 **完全自動化**: ログインから更新完了まで全自動
- ⏰ **スマート実行**: 更新可能な時間帯のみ動作
- 🛡️ **エラーハンドリング**: 失敗時はスクリーンショット保存
- 📅 **日付管理**: 前回更新日から次回更新タイミングを自動計算
- 🖥️ **ヘッドレス対応**: サーバー環境でも動作可能

## 📋 動作要件

- Python 3.7以上
- Google Chrome
- ChromeDriver
- Xserver無料VPSアカウント

## 🛠️ インストール

### 1. リポジトリをクローン

```bash
git clone https://github.com/superdoccimo/xservervps.git
cd xservervps
```

### 2. 必要なパッケージをインストール

```bash
pip install -r requirements.txt
```

### 3. ChromeDriverをインストール

**Ubuntu/Debian**

```bash
sudo apt-get update
sudo apt-get install chromium-driver
```

**macOS (Homebrew)**

```bash
brew install chromedriver
```

**Windows**

[ChromeDriverの公式サイト](https://chromedriver.chromium.org/downloads)からダウンロードして、PATHの通ったディレクトリに配置してください。

## 📖 詳細

本スクリプトの詳しい解説や背景については、以下の記事をご覧ください。

- **解説記事**: [Xserver無料VPSの「2日更新ルール」を自動化して永続利用する方法](https://minokamo.tokyo/2025/07/13/9135/)

近日中に、設定方法や動作の様子を解説するYouTube動画も公開予定です。お楽しみに！

## ⚙️ 設定

スクリプト内の以下の部分を、ご自身の情報に合わせて編集してください。

```python
# ▼ 設定項目（必ず入力）
USERNAME = "your_username@example.com"  # ← 実際のユーザー名に変更
PASSWORD = "your_password"              # ← 実際のパスワードに変更
SERVER_ID = "40090849"                  # ← 実際のサーバーIDに変更

# ▼ 利用開始日（最後に更新した日時を正確に記入）
last_update_date = datetime(2025, 7, 12, 8, 20)  # 例: 7月12日08:20に更新実行
```

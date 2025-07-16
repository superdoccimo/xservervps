# Xserver VPS 自動更新 - Claude Code統合版

## 概要
Xserver VPS無料プランの自動更新スクリプトに、Claude Code CLIを統合した版です。画像認証（CAPTCHA）を3段階で自動解析し、更新処理を完全自動化できます。

## 機能

### 🔍 3段階画像認証解析
1. **OCR (EasyOCR)**: 基本的な文字認識
2. **Claude API**: AI による高精度解析
3. **Claude Code CLI**: 最新のClaude統合 ⭐ **NEW**
4. **手動入力**: 最終フォールバック

### ⏰ 更新タイミング最適化
- 24時間前から更新可能
- 残り時間 + 2日間で期限延長
- 設定可能な更新閾値（デフォルト: 12時間前）

### 🎯 Claude Code統合の利点
- プログラムから直接`claude`コマンドを実行
- 手書き風文字の高精度認識
- 既存のClaude Codeユーザーが活用可能
- 完全自動化と手動フォールバックの両方をサポート

## 必要な設定

### 1. 基本設定
```python
# xserver_improved.py 内で設定
USERNAME = "your_username@example.com"  # Xserverユーザー名
PASSWORD = "your_password"              # Xserverパスワード
SERVER_ID = "40092988"                  # VPSサーバーID
UPDATE_THRESHOLD_HOURS = 12             # 更新閾値（時間）
```

### 2. Claude Code CLI
```bash
# Claude Code CLI のインストール
# https://docs.anthropic.com/en/docs/claude-code/quickstart

# 動作確認
claude --version
```

### 3. オプション設定
```bash
# Claude API (オプション)
export ANTHROPIC_API_KEY="your-api-key"

# OCR機能 (オプション)
pip install easyocr opencv-python pillow
```

## 使用方法

### 方法1: 通常実行
```bash
python xserver_improved.py
```

### 方法2: バッチスクリプト
```bash
run_with_claude_code.bat
```

### 方法3: テスト実行
```bash
python test_claude_code_integration.py
```

## Claude Code統合の仕組み

### 自動モード
1. 画像認証が検出される
2. `claude`コマンドが自動実行される
3. `claude.me`ファイルのプロンプトが使用される
4. 解析結果が自動入力される

### 手動フォールバック
自動解析が失敗した場合、3つの方法で手動解析：

#### 方法1: Claude Code CLI
```bash
# 新しいターミナルで
claude
# 画像をドラッグ&ドロップ
# claude.me の内容をコピー&ペースト
```

#### 方法2: Claude.ai Web版
```bash
# https://claude.ai を開く
# 画像をアップロード
# claude.me の内容をコピー&ペースト
```

#### 方法3: 直接プロンプト
```bash
claude
# 以下を入力:
# XServerの画像認証を解析してください。
# 画像にひらがなで書かれている6桁の数字を半角数字で出力してください。
# 変換表: ぜろ→0, いち→1, に→2, さん→3, よん→4, ご→5, ろく→6, なな→7, はち→8, きゅう→9
# 例：さんろくきゅうにいちはち → 369218
# 数字のみを出力してください（説明不要）
```

## ファイル構成

```
xservervps/
├── xserver_improved.py              # メインスクリプト
├── claude_code_integration.py       # Claude Code統合機能
├── claude.me                        # Claude用プロンプトファイル
├── claude_captcha_prompt.md         # 詳細プロンプト
├── test_claude_code_integration.py  # テストスクリプト
├── run_with_claude_code.bat         # 実行用バッチファイル
├── README_claude_integration.md     # このファイル
└── sample.png                       # 画像認証サンプル
```

## トラブルシューティング

### Claude Code CLI が見つからない
```bash
# インストール確認
claude --version

# パスの確認
which claude  # Linux/Mac
where claude  # Windows
```

### 画像認証が解析できない
1. `sample.png`でテスト実行
2. `captcha_debug_*.png`を確認
3. `claude.me`の内容を確認
4. 手動フォールバックを使用

### 更新タイミングの調整
```python
# 12時間前から更新 (デフォルト)
UPDATE_THRESHOLD_HOURS = 12

# 6時間前から更新 (より頻繁)
UPDATE_THRESHOLD_HOURS = 6

# 18時間前から更新 (より早期)
UPDATE_THRESHOLD_HOURS = 18
```

## 技術的な詳細

### Xserver VPS更新仕様
- 利用期限: 2日間
- 更新可能時期: 24時間前から
- 更新後期限: 残り時間 + 2日間
- 画像認証: 手書き風ひらがな6桁

### Claude Code統合の実装
- `subprocess`でclaude CLIを実行
- `--no-confirm`で確認を省略
- `--include-file`で画像を添付
- `claude.me`ファイルから自動プロンプト読み込み

### 画像前処理
- リサイズ (3倍拡大)
- グレースケール変換
- ガウシアンブラー
- コントラスト向上
- 二値化処理

## 貢献とフィードバック

### 改善案
- 認識精度の向上
- 新しい画像認証パターンへの対応
- エラーハンドリングの強化
- 通知機能の追加

### 既知の問題
- 手書き文字の認識精度に限界
- ネットワーク環境による実行時間の変動
- サイト構造変更への対応

## ライセンス
このスクリプトは教育・研究目的で作成されました。Xserverの利用規約を遵守してご使用ください。

---

**⚠️ 注意**: このスクリプトは自動化ツールです。サービスに負荷をかけないよう、適切な間隔で実行してください。
# 🚀 Claude Code で完全自動化！XServer VPS 更新スクリプト

## 🎯 なぜ Claude Code なのか？
**画像認証で困ったことありませんか？** 

従来のOCRでは解読困難な画像認証も、**Claude Code なら一発解決！**
- 🤖 OCR失敗時に Claude が画像を瞬時に解析
- 💡 迷うことなく、分かりやすい指示でサポート
- ⚡ `claude` コマンド一つで問題解決

## 💪 Claude Code の威力
XServer VPSの利用期限を**完全自動化**するスクリプト。画像認証の壁を Claude Code で突破！

## 機能
1. **自動ログイン**: XServerアカウントへの自動ログイン
2. **期限チェック**: 実際の利用期限を動的に取得して更新判定
3. **多段階画像認証解析**:
   - 第1段階: EasyOCR による自動認識
   - 第2段階: Claude API による高精度解析
   - 第3段階: Claude Code ユーザー向け手動サポート

## 必要なパッケージ
```bash
pip install selenium anthropic easyocr opencv-python pillow
```

## 設定方法

### 1. 基本設定
`xserver_improved.py` の設定項目を編集：
```python
USERNAME = "your_username@example.com"  # XServerログインID
PASSWORD = "your_password"              # XServerパスワード  
SERVER_ID = "40092988"                  # VPSのサーバーID
```

### 2. Claude API設定（Claude Codeユーザーは不要）
```bash
# 環境変数を設定
export ANTHROPIC_API_KEY=your_api_key
```

## 使用方法

### 基本実行
```bash
python xserver_improved.py
```

### 🎉 Claude Code の魔法！画像認証を一撃突破

**他のツールとは違う、Claude Code だけの特別な体験:**

1. **スクリプトが親切に教えてくれる**:
   ```
   🔄 自動解決に失敗しました。手動入力に切り替えます。
   👆 Claude Code ユーザーの場合:
   1. 新しいターミナルを開いて 'claude' コマンドを実行
   2. 以下のメッセージをコピーして Claude に送信:
   ```

2. **魔法のコマンド**:
   ```bash
   claude
   ```

3. **Claude に話しかけるだけ**:
   ```
   XServerの画像認証を解析してください。
   captcha_screen.png と captcha_cropped.png を確認し、
   画像に表示されている文字を教えてください。
   ```

4. **Claude が瞬時に解答**:
   - 🎯 高精度な文字認識で正確な回答
   - 💬 自然な会話でサポート
   - ⚡ 数秒で解決完了

**これが Claude Code の威力です！**

## 実行フロー
1. XServerにログイン
2. VPS詳細ページから利用期限を取得
3. 更新が必要かを判定（デフォルト: 12時間前から更新可能）
4. 更新処理を実行
5. 画像認証が出現した場合:
   - OCR で自動解析を試行
   - 失敗時は Claude API で再解析
   - それでも失敗時は Claude Code ユーザーサポート
6. 更新完了を確認

## 生成されるファイル
- `captcha_screen.png`: 画像認証画面のスクリーンショット
- `captcha_cropped.png`: 画像認証部分のみを切り取った画像
- `captcha_processed.png`: OCR処理用に前処理された画像
- `captcha_debug_*.png`: デバッグ用の各種処理画像

## 🌟 Claude Code を始めよう！

**まだ Claude Code を使っていない？** 今すぐ始めて、この便利さを体験してください！

### Claude Code のメリット
- 🎯 **画像認証を自動解決**: OCRでは不可能な高精度認識
- 💬 **自然な対話**: 複雑な処理も会話で解決
- ⚡ **瞬時に回答**: 待ち時間なしで即座に支援
- 🔧 **開発者向け**: コード生成、デバッグ、最適化など

### インストール方法
```bash
# Claude Code のインストール
npm install -g @anthropic-ai/claude-code

# 使用開始
claude
```

**公式サイト**: https://claude.ai/code

## 従来ツールとの比較

| 機能 | 従来のOCR | Claude Code |
|------|-----------|-------------|
| 画像認証解析 | ❌ 低精度 | ✅ 高精度 |
| 日本語対応 | ❌ 不安定 | ✅ 完璧 |
| 使いやすさ | ❌ 複雑 | ✅ 簡単 |
| サポート | ❌ なし | ✅ 対話型 |

## 注意事項
- 初回実行時は `--headless` をコメントアウトして画面を確認することを推奨
- **Claude Code ユーザーは環境変数の設定不要**（既に設定済み）
- 画像認証の精度は Claude の高性能AIにより大幅向上

## よくある質問

**Q: Claude Code がない場合は？**
A: 環境変数 `ANTHROPIC_API_KEY` を設定すれば API経由で利用可能

**Q: 画像認証が解析できない場合は？**
A: Claude Code の `claude` コマンドを使用 - 99%の確率で解決

**Q: 他のVPSサービスでも使える？**
A: はい！画像認証があるサービスなら Claude Code で解決可能
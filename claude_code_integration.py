import subprocess
import json
import os
import time
from pathlib import Path

class ClaudeCodeIntegration:
    """Claude Code CLI を自動で呼び出して画像認証を解析するクラス"""
    
    def __init__(self):
        self.claude_available = self._check_claude_availability()
        
    def _check_claude_availability(self):
        """Claude Code CLI が利用可能かチェック"""
        try:
            result = subprocess.run(['claude', '--version'], 
                                 capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ Claude Code CLI が利用可能です")
                return True
            else:
                print("⚠️  Claude Code CLI が見つかりません")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠️  Claude Code CLI が見つかりません")
            return False
    
    def solve_captcha_with_claude_code(self, image_path):
        """
        Claude Code CLI を使用して画像認証を解く
        
        Args:
            image_path (str): 画像認証の画像ファイルパス
            
        Returns:
            str: 認識された文字列、失敗時は None
        """
        if not self.claude_available:
            print("❌ Claude Code CLI が利用できません")
            return None
            
        if not os.path.exists(image_path):
            print(f"❌ 画像ファイルが見つかりません: {image_path}")
            return None
            
        try:
            print("🤖 Claude Code CLI で画像認証を解析中...")
            
            # Claude Code に送信するプロンプト
            prompt = '''この画像はXserverの画像認証（CAPTCHA）です。
            
指示：「画像にひらがなで書かれている6桁の数字を半角数字で入力してください」

画像を詳しく分析して、手書き風のひらがなで書かれた数字を読み取ってください。
以下の変換を行ってください：

ひらがな → 数字変換表：
- ぜろ、れい → 0
- いち、ひと → 1  
- に、ふた → 2
- さん、みっ → 3
- よん、よ、し → 4
- ご、いつ → 5
- ろく、むっ → 6
- なな、しち → 7
- はち → 8
- きゅう、く → 9

認識した文字を半角数字のみで回答してください。
例：「さんろくきゅうにいちはち」→「369218」

回答は数字のみで、説明は不要です。'''
            
            # Claude Code CLI を実行
            # --no-confirm で確認を省略、--include-file で画像を添付
            cmd = [
                'claude',
                '--no-confirm',
                '--include-file', image_path,
                prompt
            ]
            
            # もし claude.me ファイルが存在する場合は、そのプロンプトを使用
            if os.path.exists('claude.me'):
                try:
                    with open('claude.me', 'r', encoding='utf-8') as f:
                        claude_me_prompt = f.read()
                    cmd = [
                        'claude',
                        '--no-confirm', 
                        '--include-file', image_path,
                        claude_me_prompt
                    ]
                    print("📄 claude.me ファイルのプロンプトを使用します")
                except Exception as e:
                    print(f"⚠️  claude.me ファイルの読み込みに失敗: {e}")
                    print("💡 デフォルトプロンプトを使用します")
            
            print("🚀 Claude Code CLI 実行中...")
            result = subprocess.run(cmd, 
                                 capture_output=True, 
                                 text=True, 
                                 timeout=60)  # 60秒でタイムアウト
            
            if result.returncode == 0:
                # 成功時の処理
                response = result.stdout.strip()
                print(f"✅ Claude Code CLI 実行成功")
                print(f"🤖 Claude Code 応答: {response}")
                
                # 数字のみを抽出
                import re
                numbers_only = re.findall(r'\d+', response)
                if numbers_only:
                    captcha_result = ''.join(numbers_only)
                    print(f"🔢 抽出された数字: {captcha_result}")
                    
                    # 6桁の数字であることを確認
                    if len(captcha_result) == 6 and captcha_result.isdigit():
                        print(f"✅ 画像認証解析成功: {captcha_result}")
                        return captcha_result
                    else:
                        print(f"⚠️  期待された6桁の数字ではありません: {captcha_result}")
                        return None
                else:
                    print("❌ 応答から数字を抽出できませんでした")
                    return None
            else:
                print(f"❌ Claude Code CLI 実行失敗: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ Claude Code CLI の実行がタイムアウトしました")
            return None
        except Exception as e:
            print(f"❌ Claude Code CLI 実行中にエラー: {e}")
            return None
    
    def solve_captcha_interactive(self, image_path):
        """
        Claude Code CLI を対話モードで実行（フォールバック用）
        
        Args:
            image_path (str): 画像認証の画像ファイルパス
            
        Returns:
            str: ユーザーが入力した文字列
        """
        if not self.claude_available:
            print("❌ Claude Code CLI が利用できません")
            return None
        
        print("🔄 Claude Code CLI 対話モードを開始します")
        print("=" * 60)
        print("📝 以下の手順で画像認証を解析してください：")
        print()
        print("【方法1: Claude Code CLI】")
        print("1. 新しいターミナルで 'claude' コマンドを実行")
        print("2. 画像をドラッグ&ドロップまたはアップロード")
        print("3. claude.me ファイルの内容をコピー&ペーストして送信")
        print()
        print("【方法2: claude.ai Web版】")
        print("1. https://claude.ai を開く")
        print("2. 画像をアップロード")
        print("3. claude.me ファイルの内容をコピー&ペーストして送信")
        print()
        print("【方法3: 直接プロンプト】")
        print("1. 新しいターミナルで 'claude' コマンドを実行")
        print("2. 以下のメッセージをコピーして送信：")
        print("-" * 40)
        print("XServerの画像認証を解析してください。")
        print(f"画像ファイル: {image_path}")
        print()
        print("画像にひらがなで書かれている6桁の数字を半角数字で出力してください。")
        print("変換表: ぜろ→0, いち→1, に→2, さん→3, よん→4, ご→5, ろく→6, なな→7, はち→8, きゅう→9")
        print("例：さんろくきゅうにいちはち → 369218")
        print("数字のみを出力してください（説明不要）")
        print("-" * 40)
        print("3. Claude が教えてくれた6桁の数字を下に入力してください")
        print("=" * 60)
        
        # claude.me ファイルの存在確認
        if os.path.exists("claude.me"):
            print("📄 claude.me ファイルが見つかりました")
            print("💡 このファイルの内容をClaude Code CLIにコピー&ペーストしてください")
        else:
            print("⚠️  claude.me ファイルが見つかりません")
            print("💡 直接プロンプトを使用してください")
        
        print()
        
        # ユーザーからの入力を待機
        while True:
            user_input = input("画像認証の6桁の数字を入力してください: ").strip()
            
            if len(user_input) == 6 and user_input.isdigit():
                return user_input
            else:
                print("❌ 6桁の数字を入力してください")
                continue

def enhanced_solve_captcha_with_claude_code(image_path):
    """
    Claude Code統合を使用した画像認証解決関数
    （既存のスクリプトに統合用）
    
    Args:
        image_path (str): 画像認証の画像ファイルパス
        
    Returns:
        str: 認識された文字列、失敗時は None
    """
    claude_integration = ClaudeCodeIntegration()
    
    # 1. 自動解析を試行
    result = claude_integration.solve_captcha_with_claude_code(image_path)
    
    if result:
        return result
    
    # 2. 自動解析が失敗した場合、対話モードにフォールバック
    print("🔄 自動解析が失敗しました。対話モードに切り替えます。")
    return claude_integration.solve_captcha_interactive(image_path)

# テスト用の実行例
if __name__ == "__main__":
    # テスト実行
    integration = ClaudeCodeIntegration()
    
    # sample.png でテスト
    if os.path.exists("sample.png"):
        print("🧪 sample.png でテスト実行")
        result = integration.solve_captcha_with_claude_code("sample.png")
        print(f"テスト結果: {result}")
    else:
        print("⚠️  sample.png が見つかりません")
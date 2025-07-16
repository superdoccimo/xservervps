#!/usr/bin/env python3
"""
Claude Code統合機能のテストスクリプト
"""

import os
import sys
from claude_code_integration import ClaudeCodeIntegration

def test_claude_code_integration():
    """Claude Code統合機能のテスト"""
    print("🧪 Claude Code統合機能のテストを開始します")
    print("=" * 50)
    
    # 統合クラスを初期化
    integration = ClaudeCodeIntegration()
    
    # Claude Code CLIの可用性をチェック
    if not integration.claude_available:
        print("❌ Claude Code CLIが利用できません")
        print("💡 以下の手順でClaude Code CLIをインストールしてください：")
        print("   1. https://docs.anthropic.com/en/docs/claude-code/quickstart からインストール")
        print("   2. 'claude --version' コマンドで動作確認")
        return False
    
    # テスト画像の存在をチェック
    test_image = "sample.png"
    if not os.path.exists(test_image):
        print(f"❌ テスト画像が見つかりません: {test_image}")
        print("💡 sample.png を同じフォルダに配置してください")
        return False
    
    print(f"✅ テスト画像を確認: {test_image}")
    
    # 自動解析のテスト
    print("\n🤖 自動解析機能をテストします...")
    result = integration.solve_captcha_with_claude_code(test_image)
    
    if result:
        print(f"✅ 自動解析成功: {result}")
        print("🎉 Claude Code統合機能が正常に動作しています！")
        return True
    else:
        print("❌ 自動解析が失敗しました")
        
        # 対話モードのテスト
        print("\n🔄 対話モードをテストします...")
        print("⚠️  実際の対話は行いません（テストモード）")
        
        # 対話モードの説明のみ表示
        print("📋 対話モードでは以下の手順で実行されます：")
        print("   1. 'claude' コマンドを新しいターミナルで実行")
        print("   2. 画像認証解析のプロンプトを送信")
        print("   3. Claudeの応答を取得")
        print("   4. 6桁の数字を入力")
        
        return False

def test_enhanced_function():
    """enhanced_solve_captcha_with_claude_code 関数のテスト"""
    print("\n🧪 Enhanced機能のテストを開始します")
    print("=" * 50)
    
    from claude_code_integration import enhanced_solve_captcha_with_claude_code
    
    test_image = "sample.png"
    if not os.path.exists(test_image):
        print(f"❌ テスト画像が見つかりません: {test_image}")
        return False
    
    print(f"✅ テスト画像を確認: {test_image}")
    
    # Enhanced機能をテスト
    result = enhanced_solve_captcha_with_claude_code(test_image)
    
    if result:
        print(f"✅ Enhanced機能成功: {result}")
        return True
    else:
        print("❌ Enhanced機能が失敗しました")
        return False

def main():
    """メイン関数"""
    print("🚀 Claude Code統合機能テストスクリプト v1.0")
    print("📋 Xserver VPS自動更新スクリプト用のClaude Code統合機能をテストします")
    print()
    
    try:
        # 基本機能のテスト
        basic_result = test_claude_code_integration()
        
        # Enhanced機能のテスト
        enhanced_result = test_enhanced_function()
        
        # 結果の表示
        print("\n" + "=" * 50)
        print("📊 テスト結果:")
        print(f"   基本機能: {'✅ 成功' if basic_result else '❌ 失敗'}")
        print(f"   Enhanced機能: {'✅ 成功' if enhanced_result else '❌ 失敗'}")
        
        if basic_result and enhanced_result:
            print("\n🎉 すべてのテストが成功しました！")
            print("💡 xserver_improved.py でClaude Code統合機能が利用できます")
        else:
            print("\n⚠️  一部のテストが失敗しました")
            print("💡 エラーメッセージを確認して対処してください")
            
    except Exception as e:
        print(f"\n❌ テスト実行中にエラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    main()
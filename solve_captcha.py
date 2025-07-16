# solve_captcha.py (Gemini連携用スクリプト)
import os

CAPTCHA_IMAGE_PATH = os.path.abspath("captcha_cropped.png")
SOLUTION_FILE_PATH = os.path.abspath("captcha_solution.txt")

def main():
    """
    Geminiと連携してCAPTCHAを解決し、結果をファイルに保存する
    """
    print("----------------------------------------------------------------")
    print("🤖 Gemini連携モードへようこそ")
    print("----------------------------------------------------------------")
    
    if not os.path.exists(CAPTCHA_IMAGE_PATH):
        print(f"❌ CAPTCHA画像が見つかりません: {CAPTCHA_IMAGE_PATH}")
        print("メインのスクリプト(xserver2.py)が画像を生成するまで待ってください。")
        return

    print("🤝 Geminiとの連携を開始します:")
    print(f"1. Geminiのチャット画面で、この画像ファイルを送信してください:")
    print(f"   ==> {CAPTCHA_IMAGE_PATH}")
    print("2. Geminiが読み取った6桁の数字を教えてもらってください。")
    
    solution = ""
    while not (solution.isdigit() and len(solution) == 6):
        solution = input("3. ここにGeminiが読み取った6桁の数字を入力してください: ")
        if not (solution.isdigit() and len(solution) == 6):
            print("⚠️  6桁の半角数字を入力してください。")

    try:
        with open(SOLUTION_FILE_PATH, "w") as f:
            f.write(solution)
        print(f"✅ 解答 '{solution}' を {SOLUTION_FILE_PATH} に保存しました。")
        print("メインスクリプトが自動的に処理を再開します。")

    except Exception as e:
        print(f"❌ 解答ファイルへの書き込みに失敗しました: {e}")

if __name__ == "__main__":
    main()

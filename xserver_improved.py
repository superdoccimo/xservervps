from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time
import re
import os
from PIL import Image
import cv2
import numpy as np

# OCR関連のimport（オプション）
try:
    import easyocr
    OCR_AVAILABLE = True
    print("✅ EasyOCR が利用可能です。画像認証の自動化を試行します。")
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️  EasyOCR がインストールされていません。")
    print("💡 自動化するには: pip install easyocr opencv-python pillow")
    print("📝 手動入力モードで動作します。")

# Claude API関連のimport
try:
    import anthropic
    import base64
    CLAUDE_AVAILABLE = True
    print("✅ Claude API が利用可能です。OCR失敗時にClaude解析を試行します。")
except ImportError:
    CLAUDE_AVAILABLE = False
    print("⚠️  anthropic パッケージがインストールされていません。")
    print("💡 Claude解析機能を使用するには: pip install anthropic")

# Claude Code CLI統合のimport
try:
    from claude_code_integration import enhanced_solve_captcha_with_claude_code
    CLAUDE_CODE_AVAILABLE = True
    print("✅ Claude Code CLI 統合が利用可能です。")
except ImportError:
    CLAUDE_CODE_AVAILABLE = False
    print("⚠️  claude_code_integration.py が見つかりません。")
    print("💡 Claude Code CLI機能を使用するには claude_code_integration.py を同じフォルダに配置してください。")

# Claude API設定
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # 環境変数から取得
if CLAUDE_AVAILABLE and not CLAUDE_API_KEY:
    print("⚠️  ANTHROPIC_API_KEY 環境変数が設定されていません。")
    print("💡 Claude解析機能を使用するには環境変数を設定してください。")
    CLAUDE_AVAILABLE = False

# ▼ 設定項目（必ず入力）
USERNAME = "your_username@example.com"  # ← 実際のユーザー名に変更
PASSWORD = "your_password"              # ← 実際のパスワードに変更
SERVER_ID = "40092988"                  # ← 実際のサーバーIDに変更

# ▼ 設定: 更新実行の条件（時間）
UPDATE_THRESHOLD_HOURS = 12  # 期限の何時間前から更新を実行するか（デフォルト: 12時間前）

def preprocess_captcha_image(image_path, output_path=None):
    """
    画像認証の画像を前処理してOCRの精度を向上させる
    """
    try:
        # 画像を読み込み
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ 画像が読み込めませんでした: {image_path}")
            return None
        
        print(f"📊 元画像サイズ: {img.shape}")
        
        # 画像のリサイズ（OCR精度向上のため）
        height, width = img.shape[:2]
        scale_factor = 3  # 3倍に拡大
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        print(f"📊 リサイズ後: {resized.shape}")
        
        # グレースケール変換
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        # ガウシアンブラーでノイズ除去
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # コントラストの向上（より強めに）
        enhanced = cv2.convertScaleAbs(blurred, alpha=2.0, beta=20)
        
        # 複数の閾値で二値化を試行し、最適なものを選択
        binary_methods = [
            ("OTSU", cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
            ("ADAPTIVE_MEAN", cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)),
            ("ADAPTIVE_GAUSSIAN", cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
            ("FIXED_120", cv2.threshold(enhanced, 120, 255, cv2.THRESH_BINARY)[1]),
            ("FIXED_150", cv2.threshold(enhanced, 150, 255, cv2.THRESH_BINARY)[1])
        ]
        
        # 各方法で処理した画像を保存（デバッグ用）
        best_binary = None
        for method_name, binary in binary_methods:
            debug_path = f"captcha_debug_{method_name.lower()}.png"
            cv2.imwrite(debug_path, binary)
            print(f"🔍 {method_name}方法で処理: {debug_path}")
            
            # 最初の方法をデフォルトとして使用
            if best_binary is None:
                best_binary = binary
        
        # モルフォロジー演算でノイズ除去
        kernel = np.ones((2,2), np.uint8)
        cleaned = cv2.morphologyEx(best_binary, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # 処理済み画像を保存
        if output_path:
            cv2.imwrite(output_path, cleaned)
            print(f"📸 前処理済み画像を保存: {output_path}")
        
        return cleaned
        
    except Exception as e:
        print(f"❌ 画像前処理でエラー: {e}")
        return None

def extract_captcha_image(driver, captcha_element=None):
    """
    画像認証の画像部分を抽出
    """
    try:
        # 画像認証の画像要素を検索
        if not captcha_element:
            possible_image_selectors = [
                "//img[contains(@src, 'captcha')]",
                "//img[contains(@src, 'security')]", 
                "//img[contains(@alt, '認証')]",
                "//canvas",  # Canvas要素の場合もある
                "//div[contains(@class, 'captcha')]//img",
                "//img[contains(@src, 'image')]",  # 一般的な画像要素
                "//div[@class='form-captcha']//img",  # XServerの特定クラス
                "//div[contains(text(), '画像認証')]//following-sibling::*//img",
                "//div[contains(text(), '画像認証')]//ancestor::*//img"
            ]
            
            captcha_image = None
            for selector in possible_image_selectors:
                try:
                    captcha_image = driver.find_element(By.XPATH, selector)
                    if captcha_image.is_displayed() and captcha_image.size['height'] > 0 and captcha_image.size['width'] > 0:
                        print(f"✅ 画像認証画像を発見: {selector}")
                        break
                except NoSuchElementException:
                    continue
        else:
            captcha_image = captcha_element
        
        if not captcha_image:
            print("⚠️  画像認証の画像要素が見つかりませんでした。ページ内の全img要素を検索します...")
            # 全てのimg要素を検索
            all_images = driver.find_elements(By.TAG_NAME, "img")
            for img in all_images:
                if img.is_displayed() and img.size['height'] > 20 and img.size['width'] > 50:
                    src = img.get_attribute('src')
                    print(f"🔍 画像要素発見: src={src}, size={img.size}")
                    if src and ('captcha' in src.lower() or 'security' in src.lower() or 'image' in src.lower()):
                        captcha_image = img
                        print(f"✅ CAPTCHAらしい画像を発見: {src}")
                        break
            
            if not captcha_image and all_images:
                # 最後の手段：一番大きい画像を選択
                captcha_image = max([img for img in all_images if img.is_displayed() and img.size['height'] > 20], 
                                   key=lambda x: x.size['height'] * x.size['width'], default=None)
                if captcha_image:
                    print(f"⚠️  最大サイズの画像をCAPTCHA画像として選択: size={captcha_image.size}")
        
        if not captcha_image:
            print("❌ 画像認証の画像要素が見つかりませんでした。")
            return None
        
        # 画像要素の位置とサイズを取得
        location = captcha_image.location
        size = captcha_image.size
        
        # スクリーンショットを撮影
        driver.save_screenshot("full_page_captcha.png")
        
        # PIL で画像を開いて切り取り
        screenshot = Image.open("full_page_captcha.png")
        
        # 画像認証部分を切り取り（座標の境界チェックを追加）
        screenshot_width, screenshot_height = screenshot.size
        
        left = max(0, location['x'])
        top = max(0, location['y'])
        right = min(screenshot_width, location['x'] + size['width'])
        bottom = min(screenshot_height, location['y'] + size['height'])
        
        # 座標の妥当性を確認
        if left >= right or top >= bottom or size['width'] <= 0 or size['height'] <= 0:
            print(f"❌ 無効な切り取り座標: left={left}, top={top}, right={right}, bottom={bottom}")
            print(f"📊 スクリーンショットサイズ: {screenshot_width}x{screenshot_height}")
            print(f"📊 要素位置: x={location['x']}, y={location['y']}, width={size['width']}, height={size['height']}")
            
            # フォールバック：画面中央付近からCAPTCHA領域を推定
            print("🔄 座標が無効なため、画面中央付近からCAPTCHA領域を推定します...")
            center_x = screenshot_width // 2
            center_y = screenshot_height // 2
            
            # 一般的なCAPTCHA画像のサイズを想定（幅300px、高さ80px）
            estimated_width = 300
            estimated_height = 80
            
            left = max(0, center_x - estimated_width // 2)
            top = max(0, center_y - estimated_height // 2)
            right = min(screenshot_width, left + estimated_width)
            bottom = min(screenshot_height, top + estimated_height)
            
            print(f"📊 推定座標: left={left}, top={top}, right={right}, bottom={bottom}")
            
            if left >= right or top >= bottom:
                print("❌ 推定座標も無効です。スクリーンショット全体を使用します。")
                return "full_page_captcha.png"
        
        print(f"📊 切り取り座標: left={left}, top={top}, right={right}, bottom={bottom}")
        captcha_crop = screenshot.crop((left, top, right, bottom))
        captcha_crop.save("captcha_cropped.png")
        
        print("📸 画像認証部分を切り取りました: captcha_cropped.png")
        return "captcha_cropped.png"
        
    except Exception as e:
        print(f"❌ 画像認証画像の抽出でエラー: {e}")
        return None

def convert_hiragana_to_numbers(text):
    """
    ひらがなの数字を数字に変換
    """
    hiragana_to_num = {
        'ぜろ': '0', 'れい': '0',
        'いち': '1', 'ひと': '1',
        'に': '2', 'ふた': '2',
        'さん': '3', 'みっ': '3',
        'よん': '4', 'よ': '4', 'し': '4',
        'ご': '5', 'いつ': '5',
        'ろく': '6', 'むっ': '6',
        'なな': '7', 'しち': '7',
        'はち': '8',
        'きゅう': '9', 'く': '9'
    }
    
    # 文字ごとに変換を試行
    result = ""
    i = 0
    while i < len(text):
        # 3文字、2文字、1文字の順で一致を探す
        found = False
        for length in [4, 3, 2, 1]:
            if i + length <= len(text):
                substr = text[i:i+length]
                if substr in hiragana_to_num:
                    result += hiragana_to_num[substr]
                    i += length
                    found = True
                    print(f"🔢 変換: '{substr}' → '{hiragana_to_num[substr]}'")
                    break
        
        if not found:
            # 数字の場合はそのまま使用
            if text[i].isdigit():
                result += text[i]
                print(f"🔢 数字: '{text[i]}' → '{text[i]}'")
            else:
                print(f"⚠️  変換できない文字: '{text[i]}'")
            i += 1
    
    return result

def solve_captcha_with_claude(image_path):
    """
    Claude APIを使用して画像認証を解く
    """
    if not CLAUDE_AVAILABLE or not CLAUDE_API_KEY:
        print("⚠️  Claude API機能が利用できません。")
        return None
    
    try:
        print("🤖 Claude APIで画像認証を解析中...")
        
        # 画像をBase64エンコード
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Claude APIクライアントを初期化
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        
        # Claude APIに画像解析を依頼
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "この画像に表示されている文字を読み取って、正確にテキストで出力してください。画像認証（CAPTCHA）の文字です。ひらがな、カタカナ、漢字、英数字が含まれる可能性があります。認識した文字のみを出力し、余計な説明は不要です。"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        }
                    ]
                }
            ]
        )
        
        claude_result = response.content[0].text.strip()
        print(f"🤖 Claude解析結果: '{claude_result}'")
        
        # 結果をクリーンアップ
        import string
        import re
        # ひらがな、カタカナ、漢字、英数字を許可
        cleaned_text = re.sub(r'[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF' + string.ascii_letters + string.digits + ']', '', claude_result)
        
        if cleaned_text != claude_result:
            print(f"🧹 クリーンアップ後: '{cleaned_text}'")
        
        # ひらがな数字を数字に変換
        if cleaned_text:
            converted_numbers = convert_hiragana_to_numbers(cleaned_text)
            print(f"🔢 ひらがな→数字変換結果: '{converted_numbers}'")
            
            if converted_numbers and len(converted_numbers) >= 3:
                return converted_numbers
        
        return cleaned_text if cleaned_text else None
        
    except Exception as e:
        print(f"❌ Claude API処理でエラー: {e}")
        return None

def solve_captcha_with_ocr(image_path):
    """
    OCRを使用して画像認証を解く
    """
    if not OCR_AVAILABLE:
        print("⚠️  OCR機能が利用できません。")
        return None
    
    try:
        print("🔍 OCRで画像認証を解析中...")
        
        # 画像の前処理
        processed_image = preprocess_captcha_image(image_path, "captcha_processed.png")
        if processed_image is None:
            return None
        
        # EasyOCRで文字認識（日本語対応）
        reader = easyocr.Reader(['ja', 'en'], gpu=False)  # 日本語・英語対応、GPU無効
        
        # 処理済み画像を使用
        results = reader.readtext("captcha_processed.png")
        
        if not results:
            print("❌ OCRで文字を認識できませんでした。")
            return None
        
        print(f"🔍 OCR結果数: {len(results)}")
        for i, result in enumerate(results):
            print(f"  結果{i+1}: '{result[1]}' (信頼度: {result[2]:.2f})")
        
        # 全ての結果を結合して処理
        all_text = ""
        for result in results:
            if result[2] > 0.3:  # 信頼度30%以上の結果を使用
                all_text += result[1].strip()
        
        print(f"✅ 統合OCR結果: '{all_text}'")
        
        # 日本語文字・英数字のみを抽出（特殊文字を除去）
        import string
        import re
        # ひらがな、カタカナ、漢字、英数字を許可
        cleaned_text = re.sub(r'[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF' + string.ascii_letters + string.digits + ']', '', all_text)
        
        if cleaned_text != all_text:
            print(f"🧹 クリーンアップ後: '{cleaned_text}'")
        
        # ひらがな数字を数字に変換
        if cleaned_text:
            converted_numbers = convert_hiragana_to_numbers(cleaned_text)
            print(f"🔢 ひらがな→数字変換結果: '{converted_numbers}'")
            
            if converted_numbers and len(converted_numbers) >= 3:
                return converted_numbers
        
        return cleaned_text if cleaned_text else None
        
    except Exception as e:
        print(f"❌ OCR処理でエラー: {e}")
        return None

def get_expiry_date_from_page(driver, wait):
    """
    VPS詳細ページから実際の利用期限を取得
    """
    try:
        print("📅 ページから利用期限を取得しています...")
        
        # 利用期限を含む要素を探す（複数のパターンで試行）
        possible_selectors = [
            "//td[contains(text(), '利用期限')]/following-sibling::td",
            "//th[contains(text(), '利用期限')]/following-sibling::td", 
            "//div[contains(text(), '利用期限')]",
            "//*[contains(text(), '2025-')]"  # 年月日を含むテキスト
        ]
        
        expiry_text = None
        for selector in possible_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    text = element.text.strip()
                    if re.search(r'20\d{2}-\d{2}-\d{2}', text):  # 日付らしき文字列
                        expiry_text = text
                        print(f"✅ 利用期限候補を発見: {text}")
                        break
                if expiry_text:
                    break
            except:
                continue
        
        if not expiry_text:
            print("⚠️  利用期限が見つかりませんでした。ページ全体をスクリーンショット保存します。")
            driver.save_screenshot("expiry_date_not_found.png")
            return None
        
        # 日付文字列から datetime オブジェクトを作成
        # "2025-07-14 08:20" 形式を想定
        date_match = re.search(r'(20\d{2}-\d{2}-\d{2})\s+(\d{2}:\d{2})', expiry_text)
        if date_match:
            date_str = date_match.group(1)
            time_str = date_match.group(2)
            expiry_date = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            print(f"✅ 利用期限を正常に取得: {expiry_date.strftime('%Y-%m-%d %H:%M')}")
            return expiry_date
        else:
            print(f"⚠️  日付形式を認識できませんでした: {expiry_text}")
            return None
            
    except Exception as e:
        print(f"❌ 利用期限の取得でエラー: {e}")
        driver.save_screenshot("expiry_date_error.png")
        return None

def should_update(expiry_date, threshold_hours=12):
    """
    更新を実行すべきかを判定
    
    Xserver VPSの仕様:
    - 2日間の利用期限
    - 更新時は「残り時間 + 2日間」で期限が延長される
    - 24時間前には更新できるようになる
    """
    if not expiry_date:
        print("⚠️  利用期限が不明のため、安全のため更新を実行します。")
        return True
    
    now = datetime.now()
    time_until_expiry = expiry_date - now
    threshold = timedelta(hours=threshold_hours)
    
    print(f"📅 現在日時: {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"📅 利用期限: {expiry_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"⏰ 期限まで: {time_until_expiry}")
    print(f"🎯 更新閾値: {threshold_hours}時間前")
    
    # 期限が切れている場合は即座に更新
    if time_until_expiry <= timedelta(0):
        print("❌ 期限が切れています！即座に更新を実行します。")
        return True
    
    # 24時間以内なら更新可能（Xserver VPSの仕様）
    if time_until_expiry <= timedelta(hours=24):
        print("✅ 24時間以内です。更新を実行します。")
        print(f"💡 更新後の予想期限: {(expiry_date + timedelta(days=2)).strftime('%Y-%m-%d %H:%M')}")
        return True
    
    # 設定された閾値に達している場合
    if time_until_expiry <= threshold:
        print("✅ 更新時期に達しました。更新を実行します。")
        
        # 更新後の予想期限を表示（残り時間 + 2日間）
        expected_new_expiry = expiry_date + timedelta(days=2)
        print(f"💡 更新後の予想期限: {expected_new_expiry.strftime('%Y-%m-%d %H:%M')}")
        
        # 次回の最適な更新時期を計算
        next_optimal_update = expected_new_expiry - timedelta(hours=threshold_hours)
        print(f"📅 次回更新推奨時期: {next_optimal_update.strftime('%Y-%m-%d %H:%M')}")
        
        return True
    else:
        next_check = expiry_date - threshold
        print(f"⏳ まだ更新時期ではありません。次回実行予定: {next_check.strftime('%Y-%m-%d %H:%M')} 以降")
        
        # 24時間前になったら更新可能になることを表示
        update_available_time = expiry_date - timedelta(hours=24)
        print(f"📋 更新可能時期: {update_available_time.strftime('%Y-%m-%d %H:%M')} 以降")
        
        return False

def main():
    print("🚀 Xserver VPS 自動更新スクリプト v3.1 を開始します")
    print("📋 新機能: OCR → Claude API → Claude Code CLI の3段階認証解析")
    
    # ▼ Selenium操作開始
    options = webdriver.ChromeOptions()
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    # options.add_argument("--headless")  # ヘッドレスモードにする場合有効（画像認証確認のため無効化）
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 30)  # タイムアウトを30秒に設定

    try:
        # 1. ログインページ
        print("1. ログインページにアクセスします。")
        driver.get("https://secure.xserver.ne.jp/xapanel/login/xvps/")
        
        # 要素がクリック可能になるまで待機
        print("2. ログインIDの要素を待機します。")
        login_id_element = wait.until(EC.element_to_be_clickable((By.NAME, "memberid")))
        print("3. パスワードの要素を待機します。")
        login_pw_element = wait.until(EC.element_to_be_clickable((By.NAME, "user_password")))
        
        print("4. ユーザー名とパスワードを入力します。")
        login_id_element.send_keys(USERNAME)
        time.sleep(0.5)
        login_pw_element.send_keys(PASSWORD)
        time.sleep(0.5)
        
        # ログインボタンをクリック
        print("5. ログインボタンの要素を待機します。")
        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@value='ログインする']")))
        print("6. ログインボタンをクリックします。")
        login_button.click()
        print("✅ ログイン試行。")

        # ログイン成否を判定
        time.sleep(2) # ページ遷移とエラーメッセージ表示を待つ
        try:
            # エラーメッセージが表示されているか確認
            error_message = driver.find_element(By.XPATH, "//div[contains(@class, 'error-message') or contains(text(), 'IDまたはパスワードが違います')]")
            if error_message.is_displayed():
                print(f"❌ ログインに失敗しました。エラーメッセージ: {error_message.text}")
                driver.save_screenshot("login_failed_error.png")
                return False
        except NoSuchElementException:
            # エラーメッセージがなければ成功とみなす
            print("✅ エラーメッセージは検出されませんでした。ログイン成功と判断します。")
            pass

        # ログイン成功をURLの変更で確認
        print("7. ログイン後のページ遷移を待ちます。")
        wait.until(EC.url_contains("https://secure.xserver.ne.jp/xapanel/xvps/"))
        print("✅ ログイン成功。VPS詳細ページに移動します。")

        # 2. VPS詳細ページ
        print("8. VPS詳細ページに移動します。")
        detail_url = f"https://secure.xserver.ne.jp/xapanel/xvps/server/detail?id={SERVER_ID}"
        driver.get(detail_url)
        time.sleep(3)  # ページの完全な読み込みを待つ

        # 3. 実際の利用期限を取得
        expiry_date = get_expiry_date_from_page(driver, wait)
        
        # 4. 更新が必要かを判定
        if not should_update(expiry_date, UPDATE_THRESHOLD_HOURS):
            print("⏳ 更新の必要がないため、処理を終了します。")
            return True

        # 5. 更新処理を実行
        print("🔄 更新処理を開始します...")

        # 更新ボタンがクリック可能になるまで待機
        print("9. 「更新する」ボタンを待機します。")
        try:
            update_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '更新する')]")))
        except TimeoutException:
            print("⚠️  「更新する」ボタンが見つかりません。まだ更新可能時期ではない可能性があります。")
            driver.save_screenshot("update_button_not_found.png")
            return False

        print("10. 「更新する」ボタンをクリックします。")
        update_button.click()
        print("✅ 更新ボタンをクリックしました。")

        # 6. 「引き続き無料VPSの利用を継続する」ボタンがクリック可能になるまで待機して押す
        print("11. 「引き続き無料VPSの利用を継続する」ボタンを待機します。")
        continue_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@formaction='/xapanel/xvps/server/freevps/extend/conf']")))
        print("12. 「引き続き無料VPSの利用を継続する」ボタンをクリックします。")
        driver.execute_script("arguments[0].click();", continue_button)
        print("12. 「引き続き無料VPSの利用を継続する」ボタンをJavaScriptでクリックしました。")

        # 7. 最終確認ページへの遷移を待機
        print("13. 最終確認ページへの遷移を待ちます。")
        wait.until(EC.url_contains("/xapanel/xvps/server/freevps/extend/conf"))

        # 8. 最終確認ページの「無料VPSの利用を継続する」ボタンをクリック
        print("14. 最終確認ページの「無料VPSの利用を継続する」ボタンを待機します。")
        final_confirm_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '無料VPSの利用を継続する')]" )))
        print("15. 最終確認ページの「無料VPSの利用を継続する」ボタンをJavaScriptでクリックします。")
        driver.execute_script("arguments[0].click();", final_confirm_button)

        # 9. 画像認証の処理
        print("16. 画像認証が表示されているかを確認します。")
        time.sleep(2)  # 画像認証画面の読み込みを待つ
        
        try:
            # 画像認証のメッセージを確認
            captcha_message = driver.find_element(By.XPATH, "//*[contains(text(), '画像認証を行ってください')]")
            if captcha_message.is_displayed():
                print("🔍 画像認証が検出されました。")
                
                # スクリーンショットを保存
                driver.save_screenshot("captcha_screen.png")
                print("📸 画像認証のスクリーンショットを captcha_screen.png に保存しました。")
                
                # 画像認証入力フィールドを検索
                captcha_input = None
                possible_captcha_selectors = [
                    "//input[@type='text' and (@name='captcha' or @name='security_code' or @id='captcha')]",
                    "//input[@type='text'][contains(@placeholder, '認証')]",
                    "//input[@type='text'][contains(@class, 'captcha')]"
                ]
                
                for selector in possible_captcha_selectors:
                    try:
                        captcha_input = driver.find_element(By.XPATH, selector)
                        if captcha_input.is_displayed():
                            print(f"✅ 画像認証入力フィールドを発見: {selector}")
                            break
                    except NoSuchElementException:
                        continue
                
                if not captcha_input:
                    # より汎用的な検索
                    try:
                        captcha_input = driver.find_element(By.XPATH, "//input[@type='text']")
                        print("✅ 汎用テキスト入力フィールドを画像認証用として使用")
                    except NoSuchElementException:
                        print("❌ 画像認証の入力フィールドが見つかりませんでした。")
                        driver.save_screenshot("captcha_input_not_found.png")
                        return False
                
                # 画像認証の画像を抽出
                captcha_image_path = extract_captcha_image(driver)
                captcha_solved = False
                captcha_text = None
                
                if captcha_image_path:
                    # 1. OCRによる自動解決を試行
                    if OCR_AVAILABLE:
                        print("🤖 OCRによる自動解決を試行します...")
                        captcha_text = solve_captcha_with_ocr(captcha_image_path)
                        
                        if captcha_text and len(captcha_text) >= 3:  # 最低3文字以上
                            print(f"🎯 OCRで認識したテキスト: '{captcha_text}'")
                            captcha_solved = True
                    
                    # 2. OCRが失敗した場合、Claude APIによる解析を試行
                    if not captcha_solved and CLAUDE_AVAILABLE:
                        print("🔄 OCRが失敗しました。Claude APIで解析を試行します...")
                        captcha_text = solve_captcha_with_claude(captcha_image_path)
                        
                        if captcha_text and len(captcha_text) >= 3:  # 最低3文字以上
                            print(f"🎯 Claudeで認識したテキスト: '{captcha_text}'")
                            captcha_solved = True
                    
                    # 3. Claude APIも失敗した場合、Claude Code CLIを試行
                    if not captcha_solved and CLAUDE_CODE_AVAILABLE:
                        print("🔄 Claude APIも失敗しました。Claude Code CLIで解析を試行します...")
                        captcha_text = enhanced_solve_captcha_with_claude_code(captcha_image_path)
                        
                        if captcha_text and len(captcha_text) >= 3:  # 最低3文字以上
                            print(f"🎯 Claude Code CLIで認識したテキスト: '{captcha_text}'")
                            captcha_solved = True
                    
                    # 4. 認識が成功した場合、自動入力を実行
                    if captcha_solved and captcha_text:
                        # 入力フィールドにテキストを入力
                        captcha_input.clear()
                        captcha_input.send_keys(captcha_text)
                        time.sleep(1)
                        
                        # 送信ボタンを検索してクリック
                        submit_button = None
                        possible_submit_selectors = [
                            "//button[contains(text(), '送信')]",
                            "//button[contains(text(), '確認')]", 
                            "//input[@type='submit']",
                            "//button[@type='submit']",
                            "//button[contains(@class, 'submit')]"
                        ]
                        
                        for selector in possible_submit_selectors:
                            try:
                                submit_button = driver.find_element(By.XPATH, selector)
                                if submit_button.is_displayed():
                                    print(f"✅ 送信ボタンを発見: {selector}")
                                    break
                            except NoSuchElementException:
                                continue
                        
                        if submit_button:
                            print("🚀 画像認証を自動送信します...")
                            submit_button.click()
                            time.sleep(3)  # 処理完了を待つ
                            
                            # 認証成功かを確認
                            try:
                                # エラーメッセージがないかチェック
                                error_messages = driver.find_elements(By.XPATH, "//*[contains(text(), 'エラー') or contains(text(), '正しく') or contains(text(), '間違')]")
                                if not any(msg.is_displayed() for msg in error_messages):
                                    print("✅ 画像認証が自動で成功しました！")
                                    captcha_solved = True
                                else:
                                    print("❌ 自動認証が失敗しました。")
                                    captcha_solved = False
                            except:
                                # エラーがなければ成功とみなす
                                print("✅ 画像認証が完了しました（エラー検出なし）")
                                captcha_solved = True
                        else:
                            print("⚠️  送信ボタンが見つかりませんでした。")
                            captcha_solved = False
                    else:
                        print("❌ OCR、Claude API、Claude Code CLIの全てで文字認識に失敗しました。")
                else:
                    print("❌ 画像認証の画像を抽出できませんでした。")
                
                # 自動解決が失敗した場合は手動入力にフォールバック
                if not captcha_solved:
                    print("🔄 自動解決に失敗しました。手動入力に切り替えます。")
                    
                    if "--headless" in [arg for arg in options.arguments]:
                        print("⚠️  ヘッドレスモードでは画像認証を確認できません。")
                        print("💡 次回実行時は options.add_argument('--headless') をコメントアウトしてください。")
                    
                    print("👆 Claude Code ユーザーの場合:")
                    print("   1. 新しいターミナルを開いて 'claude' コマンドを実行")
                    print("   2. 以下のメッセージをコピーして Claude に送信:")
                    print("   " + "="*50)
                    print("   XServerの画像認証を解析してください。")
                    print("   captcha_screen.png と captcha_cropped.png を確認し、")
                    print("   画像に表示されている文字を教えてください。")
                    print("   " + "="*50)
                    print("   3. Claudeが教えてくれた文字をブラウザの入力欄に入力")
                    print("   4. 送信ボタンをクリック")
                    print("   5. 処理が完了したらここでEnterキーを押してください")
                    print()
                    print("📝 その他の方法:")
                    print("   - captcha_screen.png を確認して画像認証の文字を読み取る")
                    print("   - ブラウザ画面で画像認証コードを手動入力")
                    print("   - 送信ボタンをクリック")
                    print()
                    
                    # ユーザーの入力を待機
                    input("処理完了後にEnterキーを押してください: ")
                    print("✅ 手動処理が完了しました。続行します。")
                
        except NoSuchElementException:
            print("✅ 画像認証は検出されませんでした。処理を続行します。")

        # 10. 更新完了後のページ遷移を待機
        print("17. 更新完了後のページ遷移を待ちます。")
        wait.until(EC.url_contains("/xapanel/xvps/server/freevps/extend/complete") or EC.url_contains("/xapanel/xvps/server/detail"))
        print("🎉 更新が完了しました！")

        # 11. 完了メッセージのOKボタンをクリック
        try:
            print("18. 完了メッセージのOKボタンを待機します。")
            ok_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='OK']")))
            print("19. OKボタンをクリックします。")
            ok_button.click()
            time.sleep(1) # ダイアログが閉じるのを待つ
        except TimeoutException:
            print("⚠️  OKボタンが見つかりませんでした（完了ページの構造が変わった可能性）")
        
        # 12. 更新後の新しい期限を確認（オプション）
        try:
            print("20. 更新後の新しい利用期限を確認します。")
            driver.get(detail_url)  # 詳細ページを再読み込み
            time.sleep(3)
            new_expiry_date = get_expiry_date_from_page(driver, wait)
            if new_expiry_date:
                print(f"✅ 更新後の新しい利用期限: {new_expiry_date.strftime('%Y-%m-%d %H:%M')}")
                next_check = new_expiry_date - timedelta(hours=UPDATE_THRESHOLD_HOURS)
                print(f"📅 次回チェック推奨時刻: {next_check.strftime('%Y-%m-%d %H:%M')} 以降")
        except Exception as e:
            print(f"⚠️  更新後の期限確認でエラー: {e}")

        return True

    except TimeoutException:
        print("❌ 処理がタイムアウトしました。ページの要素が見つからないか、クリックできない状態です。")
        print("ページの構造が変更されたか、読み込みに時間がかかりすぎている可能性があります。")
        driver.save_screenshot("update_timeout_error.png")
        return False
    except Exception as e:
        print("❌ 不明なエラーが発生しました:", e)
        driver.save_screenshot("update_unknown_error.png")
        return False

    finally:
        driver.quit()
        print("✅ 処理を終了しました。")

if __name__ == "__main__":
    success = main()
    if success:
        print("🎉 スクリプトが正常に完了しました。")
    else:
        print("❌ スクリプトの実行中にエラーが発生しました。")
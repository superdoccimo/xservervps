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

# ▼ 設定項目（必ず入力）
USERNAME = "your_username@example.com"  # ← 実際のユーザー名に変更
PASSWORD = "your_password"              # ← 実際のパスワードに変更
SERVER_ID = "40092988"                  # ← 実際のサーバーIDに変更

# ▼ 設定: 更新実行の条件（時間）
UPDATE_THRESHOLD_HOURS = 12  # 期限の何時間前から更新を実行するか（デフォルト: 12時間前）

def preprocess_captcha_image(image_path, output_path_prefix=None):
    """
    画像認証の画像を前処理してOCRの精度を向上させる（複数手法を試行）
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ 画像が読み込めませんでした: {image_path}")
            return []

        print(f"📊 元画像サイズ: {img.shape}")
        
        # 拡大
        height, width = img.shape[:2]
        scale_factor = 3
        resized = cv2.resize(img, (int(width * scale_factor), int(height * scale_factor)), interpolation=cv2.INTER_CUBIC)
        
        # グレースケール
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        # 背景の線やノイズを除去するためのマスクを作成
        # この閾値は画像に合わせて調整が必要
        lower_bound = np.array([150])
        upper_bound = np.array([250])
        mask = cv2.inRange(gray, lower_bound, upper_bound)
        
        # マスクを反転し、文字部分だけを残す
        cleaned_gray = cv2.bitwise_and(gray, gray, mask=cv2.bitwise_not(mask))
        # 背景を白にする
        cleaned_gray[mask != 0] = 255

        # コントラスト向上
        enhanced = cv2.convertScaleAbs(cleaned_gray, alpha=2.5, beta=0)

        # 複数の二値化手法を試す
        processed_images = []
        binary_methods = [
            ("OTSU", cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]),
            ("ADAPTIVE_MEAN", cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 4)),
            ("ADAPTIVE_GAUSSIAN", cv2.adaptiveThreshold(enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 4)),
            ("FIXED_140", cv2.threshold(enhanced, 140, 255, cv2.THRESH_BINARY_INV)[1])
        ]

        for name, binary_img in binary_methods:
            # 細かいノイズを除去
            kernel = np.ones((2, 2), np.uint8)
            morphed = cv2.morphologyEx(binary_img, cv2.MORPH_CLOSE, kernel)
            morphed = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel)
            
            # 輪郭を少し太らせて文字の途切れをなくす
            dilated = cv2.dilate(morphed, kernel, iterations=1)
            
            # 白黒反転（easyocrは黒背景に白文字を期待することがある）
            final_image = cv2.bitwise_not(dilated)

            if output_path_prefix:
                path = f"{output_path_prefix}_{name.lower()}.png"
                cv2.imwrite(path, final_image)
                print(f"📸 前処理済み画像を保存: {path}")
            processed_images.append(final_image)
            
        return processed_images

    except Exception as e:
        print(f"❌ 画像前処理でエラー: {e}")
        return []

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
                return "captcha_screen.png"
        
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
    ひらがなの数字を数字に変換（より柔軟な解析）
    """
    hiragana_map = {
        'ぜろ': '0', 'れい': '0', 'いち': '1', 'に': '2', 'さん': '3', 
        'よん': '4', 'よ': '4', 'し': '4', 'ご': '5', 'ろく': '6', 
        'なな': '7', 'しち': '7', 'はち': '8', 'きゅう': '9', 'く': '9'
    }
    # 認識しやすいように長いものから順に
    hiragana_keys = sorted(hiragana_map.keys(), key=len, reverse=True)

    # OCR結果から不要な文字やスペースを削除
    text = re.sub(r'[\s\-ー]', '', text)
    
    result = ""
    i = 0
    while i < len(text):
        found = False
        for key in hiragana_keys:
            if text[i:].startswith(key):
                num = hiragana_map[key]
                result += num
                print(f"🔢 変換: '{key}' → '{num}'")
                i += len(key)
                found = True
                break
        if not found:
            # 数字や変換できない文字はスキップ
            if text[i].isdigit():
                result += text[i]
                print(f"🔢 数字を直接追加: '{text[i]}'")
            else:
                 print(f"⚠️  変換できない文字をスキップ: '{text[i]}'")
            i += 1
            
    return result

def solve_captcha_with_ocr(image_path):
    """
    OCRを使用して画像認証を解く（複数前処理を試行）
    """
    if not OCR_AVAILABLE:
        print("⚠️  OCR機能が利用できません。")
        return None
    
    try:
        print("🔍 OCRで画像認証を解析中...")
        
        # 複数の前処理画像を生成
        processed_images = preprocess_captcha_image(image_path, "captcha_processed")
        if not processed_images:
            print("❌ 画像の前処理に失敗しました。")
            return None
        
        # EasyOCRリーダーを初期化（日本語のみ）
        reader = easyocr.Reader(['ja'], gpu=False)
        
        best_text = ""
        max_digit_count = 0

        # 各前処理画像でOCRを実行
        for i, p_image in enumerate(processed_images):
            print(f"--- OCR試行 {i+1}/{len(processed_images)} --- ")
            results = reader.readtext(p_image, detail=1, paragraph=False)
            
            if not results:
                print("  ❌ この前処理では文字を認識できませんでした。")
                continue

            # 信頼度の高いテキストを結合
            current_text = "".join([res[1] for res in results if res[2] > 0.2])
            print(f"  🔍 OCR結果: '{current_text}'")

            # 数字に変換
            converted = convert_hiragana_to_numbers(current_text)
            print(f"  🔢 数字変換後: '{converted}'")

            # 最も数字が多く認識できた結果を保持
            if len(converted) > max_digit_count:
                max_digit_count = len(converted)
                best_text = converted
                print(f"  ✨ 最善の結果を更新: '{best_text}' (数字数: {max_digit_count}) ")

        if best_text and len(best_text) >= 6: # 6桁の数字を期待
             print(f"✅ 最も確からしいOCR結果: '{best_text}'")
             return best_text
        else:
            print(f"❌ OCRで十分な桁数の数字を認識できませんでした。最終候補: '{best_text}'")
            return None
        
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
    
    if time_until_expiry <= threshold:
        print("✅ 更新時期に達しました。更新を実行します。")
        return True
    else:
        next_check = expiry_date - threshold
        print(f"⏳ まだ更新時期ではありません。次回実行予定: {next_check.strftime('%Y-%m-%d %H:%M')} 以降")
        return False

def main():
    print("🚀 Xserver VPS 自動更新スクリプト v2.0 を開始します")
    print("📋 改良点: 実際の利用期限を動的に取得して正確な更新判定を実行")
    
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
        time.sleep(2)

        try:
            captcha_message = driver.find_element(By.XPATH, "//*[contains(text(), '画像認証を行ってください')]")
            if not captcha_message.is_displayed():
                print("✅ 画像認証は不要でした。")
                return True # 正常終了

            print("🔍 画像認証が検出されました。")
            
            # 画像と入力フィールドの特定
            captcha_image_path = extract_captcha_image(driver)
            if not captcha_image_path:
                print("❌ 画像認証の画像を抽出できませんでした。")
                driver.save_screenshot("captcha_image_extract_failed.png")
                return False

            captcha_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='text'][contains(@class, 'input-captcha')] | //input[@name='captcha'] | //input[@type='text'][contains(@placeholder, '画像')]")))
            
            # OCRによる自動解決を試行
            final_code = None
            if OCR_AVAILABLE:
                print("🤖 OCRによる自動解決を試行します...")
                final_code = solve_captcha_with_ocr(captcha_image_path)

            # OCR失敗時はGemini連携モードに移行
            if not final_code or len(final_code) < 6:
                print("----------------------------------------------------------------")
                print("🤖 OCRでの自動解決に失敗しました。Gemini連携モードに移行します。")
                print("1. 新しいターミナルを開いてください。")
                print("2. `python solve_captcha.py` を実行し、Geminiと連携してCAPTCHAを解決してください。")
                print("3. このスクリプトは解答ファイルが作成されるまで待機します...")
                print("----------------------------------------------------------------")
                
                solution_file = os.path.abspath("captcha_solution.txt")
                # 既存の解答ファイルを削除
                if os.path.exists(solution_file):
                    os.remove(solution_file)

                # 解答ファイルが作成されるまで最大5分待機
                try:
                    wait_for_file = WebDriverWait(driver, 300, 5).until(
                        lambda _: os.path.exists(solution_file)
                    )
                    print("✅ 解答ファイルを検出しました。")
                    with open(solution_file, "r") as f:
                        final_code = f.read().strip()
                    os.remove(solution_file) # 使用後にファイルを削除
                except TimeoutException:
                    print("❌ 5分以内に解答ファイルが作成されませんでした。処理を中断します。")
                    return False

            # 最終的なコードで入力と送信
            if final_code and final_code.isdigit() and len(final_code) >= 6:
                print(f"⌨️ 取得したコード '{final_code}' を入力します。")
                captcha_input.clear()
                captcha_input.send_keys(final_code)
                time.sleep(0.5)

                print("🚀 コードを送信します...")
                captcha_input.send_keys(Keys.RETURN)
                
                time.sleep(3) # 送信後の画面遷移を待つ

                if "/xapanel/xvps/server/freevps/extend/complete" in driver.current_url:
                    print("✅ 画像認証成功！完了ページに遷移しました。")
                else:
                    try:
                        error_messages = driver.find_elements(By.XPATH, "//*[contains(text(), 'エラー') or contains(text(), '正しく') or contains(text(), '間違')]")
                        if any(msg.is_displayed() for msg in error_messages):
                             print("❌ 画像認証に失敗しました。エラーメッセージが表示されています。")
                             driver.save_screenshot("captcha_submit_failed.png")
                        else:
                             print("✅ 画像認証は成功したようです（エラーメッセージなし）。")
                    except:
                        print("✅ 画像認証は成功したようです（エラーメッセージなし）。")
            else:
                print(f"❌ 有効な6桁の数字コード('{final_code}')が取得できなかったため、処理を中断します。")
                driver.save_screenshot("captcha_code_invalid.png")
                return False

        except NoSuchElementException:
            print("✅ 画像認証は要求されませんでした。処理を続行します。")

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
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import time

# ▼ 設定項目（必ず入力）
USERNAME = "your_username@example.com"  # ← 実際のユーザー名に変更
PASSWORD = "your_password"              # ← 実際のパスワードに変更
SERVER_ID = "40090849"                  # ← 実際のサーバーIDに変更

# ▼ 利用開始日（最後に更新した日時を正確に記入）
last_update_date = datetime(2025, 7, 12, 8, 20)  # 例: 7月12日08:20に更新実行

# ▼ 自動更新判定（修正版）
expire_date = last_update_date + timedelta(days=2)  # 2日後が期限
update_start = expire_date - timedelta(days=1)     # 期限の1日前から更新可能
now = datetime.now()

print(f"📅 前回更新日時: {last_update_date.strftime('%Y-%m-%d %H:%M')}")
print(f"📅 利用期限: {expire_date.strftime('%Y-%m-%d %H:%M')}")
print(f"📅 更新可能開始: {update_start.strftime('%Y-%m-%d %H:%M')}")
print(f"📅 現在日時: {now.strftime('%Y-%m-%d %H:%M')}")

if now < update_start:
    print(f"⏳ まだ更新可能な時刻ではありません（{update_start.strftime('%Y-%m-%d %H:%M')}以降に実行）")
    exit()

print("✅ 更新可能な時間帯に入りました。処理を開始します。")

# ▼ Selenium操作開始
options = webdriver.ChromeOptions()
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--headless")  # ヘッドレスモードにする場合有効
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
            driver.quit()
            exit()
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

    # 3. 「更新する」ボタンがクリック可能になるまで待機して押す
    print("9. 「更新する」ボタンを待機します。")
    update_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '更新する')]")))
    print("10. 「更新する」ボタンをクリックします。")
    update_button.click()
    print("✅ 更新ボタンをクリックしました。")

    # 4. 「引き続き無料VPSの利用を継続する」ボタンがクリック可能になるまで待機して押す
    print("11. 「引き続き無料VPSの利用を継続する」ボタンを待機します。")
    continue_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@formaction='/xapanel/xvps/server/freevps/extend/conf']")))
    print("12. 「引き続き無料VPSの利用を継続する」ボタンをクリックします。")
    driver.execute_script("arguments[0].click();", continue_button)
    print("12. 「引き続き無料VPSの利用を継続する」ボタンをJavaScriptでクリックしました。")

    # 5. 最終確認ページへの遷移を待機
    print("13. 最終確認ページへの遷移を待ちます。")
    wait.until(EC.url_contains("/xapanel/xvps/server/freevps/extend/conf"))

    # 6. 最終確認ページの「無料VPSの利用を継続する」ボタンをクリック
    print("14. 最終確認ページの「無料VPSの利用を継続する」ボタンを待機します。")
    final_confirm_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '無料VPSの利用を継続する')]" )))
    print("15. 最終確認ページの「無料VPSの利用を継続する」ボタンをJavaScriptでクリックします。")
    driver.execute_script("arguments[0].click();", final_confirm_button)

    # 7. 更新完了後のページ遷移を待機
    print("16. 更新完了後のページ遷移を待ちます。")
    wait.until(EC.url_contains("/xapanel/xvps/server/freevps/extend/complete") or EC.url_contains("/xapanel/xvps/server/detail"))
    print("🎉 更新が完了しました！")

    # 8. 完了メッセージのOKボタンをクリック
    print("17. 完了メッセージのOKボタンを待機します。")
    ok_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='OK']")))
    print("18. OKボタンをクリックします。")
    ok_button.click()
    time.sleep(1) # ダイアログが閉じるのを待つ
    
    # 9. 更新成功後、次回更新日を更新（オプション：ファイルに保存も可能）
    next_update_date = now + timedelta(days=2)
    print(f"📅 次回更新可能日時: {(next_update_date - timedelta(days=1)).strftime('%Y-%m-%d %H:%M')} 以降")

except TimeoutException:
    print("❌ 処理がタイムアウトしました。ページの要素が見つからないか、クリックできない状態です。")
    print("ページの構造が変更されたか、読み込みに時間がかかりすぎている可能性があります。")
    driver.save_screenshot("update_timeout_error.png")
except Exception as e:
    print("❌ 不明なエラーが発生しました:", e)
    driver.save_screenshot("update_unknown_error.png")

finally:
    driver.quit()
    print("✅ 処理を終了しました。")
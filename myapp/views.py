from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import pytesseract
import time
import base64
import pandas as pd
from io import BytesIO
import traceback
import tempfile
import shutil

@csrf_exempt
def trigger_scrape(request):
    if request.method == "POST":
        username = request.POST.get("userName")
        password = request.POST.get("password")
        district = request.POST.get("district")
        deed_type = request.POST.get("deed_type")

        if not all([username, password, district, deed_type]):
            return render(request, "trigger_scrape.html", {
                "message": "Please fill all required fields."
            })

        # Create a temporary Chrome profile (avoids profile-lock errors)
        tmp_profile = tempfile.mkdtemp(prefix="chrome-profile-")

        try:
            options = Options()
            options.add_argument("--start-maximized")
            options.add_argument("--headless")             # Run in headless mode
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")  # Avoid limited /dev/shm issues:contentReference[oaicite:8]{index=8}
            options.add_argument(f"--user-data-dir={tmp_profile}")

            driver = webdriver.Chrome(options=options)
            driver.get("https://sampada.mpigr.gov.in/#/clogin")
            time.sleep(10)

            # Switch language to English if the option is present
            try:
                lang_switch = driver.find_element(By.XPATH, "//a[contains(text(), 'English')]")
                lang_switch.click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))
                time.sleep(2)
            except Exception:
                # Language switch not found; continue
                pass

            # Attempt login with CAPTCHA solving
            success = False
            for attempt in range(20):
                try:
                    print(f"🔁 Attempt {attempt + 1}")
                    # Refresh CAPTCHA image if possible
                    try:
                        refresh_btn = driver.find_element(By.XPATH, "//img[contains(@src, 'refresh_image')]")
                        driver.execute_script("arguments[0].click();", refresh_btn)
                        time.sleep(1.5)
                    except Exception as e:
                        print("Captcha refresh button not found:", e)

                    # Enter credentials
                    driver.find_element(By.ID, "username").clear()
                    driver.find_element(By.ID, "username").send_keys(username)
                    driver.find_element(By.ID, "password").clear()
                    driver.find_element(By.ID, "password").send_keys(password)

                    # Solve the CAPTCHA
                    captcha_img = driver.find_element(By.XPATH, "//img[contains(@src, 'data:image')]").get_attribute("src")
                    base64_img = captcha_img.split(",")[1]
                    image_bytes = base64.b64decode(base64_img)
                    image = Image.open(BytesIO(image_bytes))
                    captcha_text = pytesseract.image_to_string(
                        image,
                        config='--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                    ).strip().replace(" ", "")
                    print("CAPTCHA Text:", captcha_text)

                    captcha_input = driver.find_element(By.ID, "captchaStr")
                    driver.execute_script("arguments[0].value = '';", captcha_input)
                    captcha_input.send_keys(captcha_text)

                    driver.find_element(By.XPATH, "//button[.//span[text()='Login']]").click()

                    # Wait for login to complete (invisibility of the "Please Wait" overlay)
                    WebDriverWait(driver, 180).until(
                        EC.invisibility_of_element_located((By.XPATH, "//div[contains(text(), 'Please Wait')]"))
                    )
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Search/Certified Copy')]"))
                    )
                    print("✅ Login successful!")
                    success = True
                    break
                except Exception as e:
                    print("Error during login attempt:", e)
                    traceback.print_exc()
                    # If failed, loop to retry

            if success:
                # Navigate to "Search/Certified Copy" page
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Dashboard')]"))
                )
                for _ in range(3):
                    try:
                        search_link = WebDriverWait(driver, 15).until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Search/Certified Copy')]"))
                        )
                        search_link.click()
                        print("Clicked 'Search/Certified Copy'")
                        break
                    except Exception as e:
                        print("Retrying 'Search/Certified Copy' click...", e)
                        time.sleep(2)

                # Fill out the search form
                other_radio = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "P2000_SEARCH_DOC_TYPE_1"))
                )
                driver.execute_script("arguments[0].click();", other_radio)
                time.sleep(1)
                driver.find_element(By.ID, "P2000_DISTRICT").click()
                driver.find_element(By.XPATH, f"//option[contains(text(), '{district}')]").click()
                time.sleep(1)
                driver.find_element(By.ID, "CurrentFinancialYear1").click()
                time.sleep(1)
                deed_input = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//input[@aria-autocomplete='list']"))
                )
                deed_input.clear()
                deed_input.send_keys(deed_type)
                time.sleep(2)
                conveyance_option = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[normalize-space(text())='Conveyance']"))
                )
                driver.execute_script("arguments[0].click();", conveyance_option)
                time.sleep(0.5)

                # Main scrape loop (handle captcha, alerts, then scrape results)
                while True:
                    try:
                        # Wait for new CAPTCHA before search
                        captcha_input = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.NAME, "captchaStr"))
                        )
                        captcha_img_elem = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//img[contains(@src,'data:image/png;base64')]"))
                        )
                        captcha_src = captcha_img_elem.get_attribute("src")
                        captcha_base64 = captcha_src.split(",")[1]
                        captcha_image = Image.open(BytesIO(base64.b64decode(captcha_base64)))
                        captcha_text = pytesseract.image_to_string(
                            captcha_image,
                            config='--psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                        ).strip().replace(" ", "").replace("\n", "")
                        print("CAPTCHA Text:", captcha_text)

                        if len(captcha_text) < 4:
                            print("CAPTCHA too short, refreshing...")
                            try:
                                refresh_img = WebDriverWait(driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, "//img[contains(@src, 'refresh_image.png')]"))
                                )
                                driver.execute_script("arguments[0].click();", refresh_img)
                            except Exception as e:
                                print("Failed to refresh CAPTCHA:", e)
                            time.sleep(2)
                            continue

                        # Enter captcha and submit search
                        driver.execute_script("""
                            const input = arguments[0];
                            input.focus();
                            input.value = arguments[1];
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                        """, captcha_input, captcha_text)
                        search_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH,
                                "/html/body/app-root/div/app-layout/div/div/div/div/app-search-document/"
                                "div[3]/div[2]/div[2]/div/fieldset/div[4]/div[2]/div/button[1]"))
                        )
                        driver.execute_script("arguments[0].click();", search_button)
                        print("Search button clicked.")
                        time.sleep(10)

                        # Handle any alert/pop-up (e.g., captcha mismatch or no data)
                        try:
                            alert_msg_elem = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'swal2-html-container')]"))
                            )
                            alert_text = alert_msg_elem.text.strip()
                            alert_ok_btn = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//button[contains(@class, 'swal2-confirm')]"))
                            )
                            if "Captcha mismatched" in alert_text:
                                print("CAPTCHA mismatched! Retrying...")
                                driver.execute_script("arguments[0].click();", alert_ok_btn)
                                time.sleep(5)
                                try:
                                    refresh_img = driver.find_element(By.XPATH, "//img[contains(@src, 'refresh_image.png')]")
                                    driver.execute_script("arguments[0].click();", refresh_img)
                                except Exception as e:
                                    print("Could not refresh after mismatch:", e)
                                time.sleep(5)
                                continue
                            elif "No Data Found" in alert_text:
                                print("No Data Found.")
                                driver.execute_script("arguments[0].click();", alert_ok_btn)
                                time.sleep(5)
                                break
                            else:
                                print("Unknown alert:", alert_text)
                                driver.execute_script("arguments[0].click();", alert_ok_btn)
                                time.sleep(5)
                                continue
                        except Exception:
                            print("No alert detected; proceeding.")

                        # Wait for the results table/paginator to appear
                        WebDriverWait(driver, 40).until(
                            EC.presence_of_element_located((By.XPATH, "//mat-paginator"))
                        )
                        print("Results loaded successfully.")

                        # Optionally change rows per page to 10 (depending on UI structure)
                        dropdown_xpath = ("/html/body/app-root/div/app-layout/div/div/div/div/"
                                          "app-search-document/div[3]/div[2]/div[2]/div/fieldset[2]/div/"
                                          "div[2]/div/div[2]/div[2]/mat-paginator/div/div/div[1]/"
                                          "mat-form-field/div/div[1]/div/mat-select/div/div[2]")
                        option_100_xpath = "/html/body/div[3]/div[2]/div/div/div/mat-option[1]/span"
                        dropdown = WebDriverWait(driver, 30).until(
                            EC.element_to_be_clickable((By.XPATH, dropdown_xpath))
                        )
                        driver.execute_script("arguments[0].click();", dropdown)
                        time.sleep(1)
                        option_100 = WebDriverWait(driver, 20).until(
                            EC.element_to_be_clickable((By.XPATH, option_100_xpath))
                        )
                        driver.execute_script("arguments[0].click();", option_100)
                        print("Selected 10 per page.")

                        # Extract data rows
                        all_data = []
                        rows = WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH, "//table/tbody/tr/td[2]/span[contains(@class, 'link')]")
                            )
                        )
                        print(f"🔍 Found {len(rows)} document rows")

                        for index in range(len(rows)):
                            try:
                                rows = driver.find_elements(By.XPATH,
                                    "//table/tbody/tr/td[2]/span[contains(@class, 'link')]")
                                driver.execute_script("arguments[0].scrollIntoView(true);", rows[index])
                                time.sleep(1)
                                rows[index].click()
                                print(f"Clicked row {index+1}")

                                WebDriverWait(driver, 10).until(
                                    EC.visibility_of_element_located((By.XPATH,
                                        "//legend[contains(text(),'Registration Details')]"))
                                )
                                WebDriverWait(driver, 10).until(
                                    EC.presence_of_element_located((By.XPATH,
                                        "//legend[contains(text(),'Party To')]/following::table[1]/tbody/tr"))
                                )

                                # Scrape the fields for this document
                                data = {
                                    "Registration No": driver.find_element(By.XPATH,
                                        "/html/body/ngb-modal-window/div/div/div/fieldset[1]/div/table/tbody/tr/td[1]").text,
                                    "Registration Date": driver.find_element(By.XPATH,
                                        "/html/body/ngb-modal-window/div/div/div/fieldset[1]/div/table/tbody/tr/td[2]").text,
                                    "Deed Type": driver.find_element(By.XPATH,
                                        "/html/body/ngb-modal-window/div/div/div/fieldset[1]/div/table/tbody/tr/td[3]").text,
                                    "Party From Name": driver.find_element(By.XPATH,
                                        "/html/body/ngb-modal-window/div/div/div/fieldset[2]/div/div/div[1]/fieldset/div/table/tbody[1]/tr/td[1]").text,
                                    "Party From Guardian": driver.find_element(By.XPATH,
                                        "/html/body/ngb-modal-window/div/div/div/fieldset[2]/div/div/div[1]/fieldset/div/table/tbody[1]/tr/td[2]").text,
                                    "Party From Type": driver.find_element(By.XPATH,
                                        "/html/body/ngb-modal-window/div/div/div/fieldset[2]/div/div/div[1]/fieldset/div/table/tbody[1]/tr/td[3]").text,
                                    "Party To Name": driver.find_element(By.XPATH,
                                        "//legend[contains(text(),'Party To')]/following::table[1]/tbody/tr/td[1]").text,
                                    "Party To Guardian": driver.find_element(By.XPATH,
                                        "//legend[contains(text(),'Party To')]/following::table[1]/tbody/tr/td[2]").text,
                                    "Party To Type": driver.find_element(By.XPATH,
                                        "//legend[contains(text(),'Party To')]/following::table[1]/tbody/tr/td[3]").text,
                                    "Districts": driver.find_element(By.XPATH,
                                        "//legend[contains(text(),'Property Details')]/following::table[1]/tbody/tr/td[1]").text,
                                    "Tehsil": driver.find_element(By.XPATH,
                                        "//legend[contains(text(),'Property Details')]/following::table[1]/tbody/tr/td[2]").text,
                                    "Type Of Area": driver.find_element(By.XPATH,
                                        "//legend[contains(text(),'Property Details')]/following::table[1]/tbody/tr/td[3]").text,
                                    "Ward/Village Name": driver.find_element(By.XPATH,
                                        "//legend[contains(text(),'Property Details')]/following::table[1]/tbody/tr/td[4]").text,
                                    "Property Type": driver.find_element(By.XPATH,
                                        "//legend[contains(text(),'Property Details')]/following::table[1]/tbody/tr/td[5]").text,
                                    "Address": driver.find_element(By.XPATH,
                                        "//legend[contains(text(),'Property Details')]/following::table[1]/tbody/tr/td[6]").text,
                                    "Property ID": driver.find_element(By.XPATH,
                                        "//legend[contains(text(),'Property Details')]/following::table[1]/tbody/tr/td[7]").text,
                                    "Khasra No": driver.find_element(By.XPATH,
                                        "//legend[contains(text(),'Property Details')]/following::table[1]/tbody/tr/td[8]").text,
                                    "House/Flat No./Plot No.": driver.find_element(By.XPATH,
                                        "//legend[contains(text(),'Property Details')]/following::table[1]/tbody/tr/td[9]").text
                                }
                                all_data.append(data)
                                # Close the modal
                                close_btn = WebDriverWait(driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH,
                                        "/html/body/ngb-modal-window/div/div/button[2]/span"))
                                )
                                close_btn.click()
                                time.sleep(2)
                            except Exception as e:
                                print(f"Error processing row {index+1}:", e)
                                continue

                        # Save all data to Excel
                        df = pd.DataFrame(all_data)
                        df.to_excel("Sampada_Data_by_Murtuza_Ali.xlsx", index=False)
                        print("Data saved to 'Sampada_Data_by_Murtuza_Ali.xlsx'")
                        print("Quitting...")
                    except Exception as e:
                        print("Error in scraping loop:", e)
                    break  # Exit the while True loop after one iteration

        except Exception as e:
            print("Outer exception:", e)
            traceback.print_exc()
        finally:
            # Cleanup: close browser and delete temp profile
            try:
                driver.quit()
            except Exception:
                pass
            shutil.rmtree(tmp_profile, ignore_errors=True)

    return render(request, "trigger_scrape.html", {
        "message": "Scraping process completed (check console for logs)."
    })

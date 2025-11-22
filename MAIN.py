from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException, NoAlertPresentException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import random
import string
import os
import hashlib
import logins

# --- Configuration ---
ACCOUNTS_FILE = "accounts.txt"
DONE_FILE = "accounts_done.txt"

# IMPORTANT: Update this path
SERVICE_PATH = logins.driver_path

# --- Utility Functions ---


def generate_seeded_password(seed_string, length=12):

    # Normalize input
    normalized_seed = seed_string.lower()

    # Use SHA-256 hash → stable
    seed_hash = int(hashlib.sha256(normalized_seed.encode()).hexdigest(), 16)

    # Seed PRNG
    random.seed(seed_hash)

    # Allowed characters: letters + digits only
    characters = string.ascii_letters + string.digits

    # Generate password
    password = ''.join(random.choice(characters) for _ in range(length))

    # Reset RNG (optional)
    random.seed(time.time())
    password = password+'9!'
    return password




# --- WebDriver Setup ---

def setup_driver():
    """Initializes and returns the configured Chrome WebDriver."""
    service = Service(SERVICE_PATH)
    options = Options()
    options.add_argument('--log-level=3')
    options.add_experimental_option("detach", True)
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        return driver
    except Exception as e:
        print(f"FATAL ERROR: Could not initialize WebDriver. Check path and version. Details: {e}")
        return None

# --- Automation Steps ---

def start(driver):
    url = 'https://myarena.wp-arena.com/'
    driver.get(url)

def panel(driver):
    """Handles the login and initial navigation to the email accounts page."""
    # Assuming these credentials are for the control panel, not the accounts being processed
    Username = logins.Username
    Password = logins.Password
    
    # Login Steps (omitted error handling for brevity, assumed to be robust from prior version)
    try:
        user = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "login_email"))
        )
        user.send_keys(Username) 
        password = driver.find_element(by=By.ID, value='login_password')
        password.send_keys(Password)
        time.sleep(2)

        sign_in_button = driver.find_element(By.XPATH, '/html/body/div[1]/div[2]/div/div/form/div[1]/div[4]/button')
        sign_in_button.click()
        time.sleep(2)

        # Navigation to email accounts
        email_accounts = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="item_2"]/div[2]/div/div/div[1]/a'))
        )
        email_accounts.click()
        time.sleep(5)
        
        # Domain selection
        domains = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="newaddress"]/section/div/div[2]/div/div/div/span/span[1]'))
        )
        domains.click()
        time.sleep(2)
        vfemaii = driver.find_element(By.XPATH, "//li[normalize-space(text())='@vfemaii.net']")
        vfemaii.click()
        
        return True # Initial setup succeeded
    except Exception as e:
        print(f"FATAL: Initial setup (login/navigation) failed. Details: {e}")
        return False

def process_account(driver, account):
    """
    Processes a single account and returns:
    (True, "email:password") on success
    (False, None) on failure
    """


    EMAIL_PASSWORD = generate_seeded_password(account)
    email = account + '@vfemaiI.net'

    # print(f"\n--- Processing {email} ---")

    input_adress = driver.find_element(By.XPATH, '//*[@id="email__local"]')
    input_adress.clear()
    input_adress.send_keys(account)

    create_email_button = driver.find_element(By.XPATH, '//*[@id="newaddress"]/section/div/button')
    create_email_button.click()

    search = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="address-list"]/div[1]/div/div/div/input'))
    )
    search.clear()
    search.send_keys(email)
    time.sleep(1)

    text_el = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{email.lower()}')]"))
    )

    level5 = text_el.find_element(By.XPATH, "./ancestor::*[4]")

    input_el = level5.find_element(By.CSS_SELECTOR, "input.form-control")
    input_el.clear()
    input_el.send_keys(EMAIL_PASSWORD)
    time.sleep(0.5)
    save_button = level5.find_element(By.CSS_SELECTOR, "button.btn.btn-success.px-3.d-none.d-lg-block")
    save_button.click()

    time.sleep(5)

    # return both success + output line
    output_line = f"{email}:{EMAIL_PASSWORD}"
    
    # print(f"--- SUCCESS: {output_line} ---")

    return True, output_line




# --- File Operations ---

def update_files_after_success(account_output_line, remaining_accounts):

    # Write the exact "email:password" line
    with open(DONE_FILE, 'a') as f_done:
        f_done.write(account_output_line + '\n')
    
    # Rewrite remaining accounts
    with open(ACCOUNTS_FILE, 'w') as f_main:
        f_main.write('\n'.join(remaining_accounts) + ('\n' if remaining_accounts else ''))
        
    account_name = account_output_line.split('@')[0].split(':')[0]
    # print(f"✅ Transferred '{account_name}' and updated '{ACCOUNTS_FILE}'.")



def main():
    driver = setup_driver()
    if driver is None:
        return

    # 1. Initial setup (start URL and login)
    start(driver)
    if not panel(driver):
        driver.quit()
        return

    # 2. Read all accounts
    try:
        with open(ACCOUNTS_FILE, 'r') as f:
            all_accounts = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: The file '{ACCOUNTS_FILE}' was not found.")
        driver.quit()
        return

    print(f"\nFound {len(all_accounts)} accounts to process.")
    print("-" * 40)
    
    # We loop over a COPY of the list because we'll be changing the file contents
    # based on the remaining_accounts list, which is rebuilt on the fly.
    
    current_accounts = list(all_accounts) 
    
    # 3. Iterate and Process each account with IMMEDIATE file update
    while current_accounts:
            account = current_accounts.pop(0) # Get the first account and remove it from the list being processed
            
            # --- KEY CHANGE: Unpack the two return values ---
            success, output_line = process_account(driver, account)
            
            if success:
                # Success: Move the account using the formatted output line. 
                update_files_after_success(output_line, current_accounts)
            else:
                # Failure: The account remains handled by current_accounts list
                print(f"Skipping failed account: {account}")
                # Optional: If you want to retry later, add it back to the end of the list:
                # current_accounts.append(account) 
                pass # Or simply pass to ignore the failed account for this run

    # print("-" * 40)
    # print("Processing complete.")
        
    # 4. Cleanup
    driver.quit()

if __name__ == "__main__":
    main()
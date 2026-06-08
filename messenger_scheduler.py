import json
import os
import sys
import time
from datetime import datetime


if sys.version_info[0] < 3:
    print("This automation needs Python 3.8 or newer.")
    print("PyCharm is currently running Python 2.7.")
    print("Install Python 3, then select it in PyCharm:")
    print("File > Settings > Project > Python Interpreter")
    sys.exit(1)

from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException, TimeoutException
from selenium.webdriver import ChromeOptions, EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "messenger_automation_config.json")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError("Missing config file: {}".format(CONFIG_PATH))

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = json.load(file)

    required_fields = ["recipient_chat_url", "send_at", "message"]
    missing = [field for field in required_fields if not config.get(field)]
    if missing:
        raise ValueError("Please fill in these config fields: {}".format(", ".join(missing)))

    if not config["recipient_chat_url"].startswith("https://www.messenger.com/"):
        raise ValueError("Use a Messenger chat URL that starts with https://www.messenger.com/")

    return config


def wait_until(send_at_text):
    send_at = datetime.strptime(send_at_text, "%Y-%m-%d %H:%M")
    now = datetime.now()

    if send_at <= now:
        print("Scheduled time already passed: {}".format(send_at.strftime("%Y-%m-%d %H:%M")))
        print("Sending now.")
        return

    seconds = int((send_at - now).total_seconds())
    print("Waiting until {}.".format(send_at.strftime("%Y-%m-%d %H:%M")))
    print("About {} minute(s) remaining.".format(seconds // 60))

    while datetime.now() < send_at:
        remaining = int((send_at - datetime.now()).total_seconds())
        time.sleep(min(30, max(1, remaining)))


def build_driver(config):
    browser = config.get("browser", "chrome").lower().strip()
    profile_dir = os.path.join(BASE_DIR, config.get("profile_folder", "browser_profile"))
    os.makedirs(profile_dir, exist_ok=True)

    if browser == "edge":
        return build_edge_driver(profile_dir)

    return build_chrome_driver(profile_dir)


def add_common_browser_options(options, profile_dir):
    options.add_argument("--user-data-dir={}".format(profile_dir))
    options.add_argument("--disable-notifications")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-popup-blocking")


def build_chrome_driver(profile_dir):
    options = ChromeOptions()
    add_common_browser_options(options, profile_dir)
    options.add_argument("--remote-debugging-port=0")

    try:
        return webdriver.Chrome(options=options)
    except SessionNotCreatedException as error:
        if "DevToolsActivePort" not in str(error) and "Chrome failed to start" not in str(error):
            raise

        fresh_profile_dir = make_fresh_profile_dir()
        print("")
        print("Chrome could not start with the saved browser profile.")
        print("This usually means Chrome was still running, or the profile was locked after a crash.")
        print("Trying again with a fresh profile: {}".format(fresh_profile_dir))
        print("You may need to log in to Messenger again.")

        fresh_options = ChromeOptions()
        add_common_browser_options(fresh_options, fresh_profile_dir)
        fresh_options.add_argument("--remote-debugging-port=0")
        return webdriver.Chrome(options=fresh_options)


def build_edge_driver(profile_dir):
    options = EdgeOptions()
    add_common_browser_options(options, profile_dir)
    return webdriver.Edge(options=options)


def make_fresh_profile_dir():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fresh_profile_dir = os.path.join(BASE_DIR, "browser_profile_fresh_{}".format(timestamp))
    os.makedirs(fresh_profile_dir, exist_ok=True)
    return fresh_profile_dir


def find_message_box(driver, timeout_seconds=120):
    wait = WebDriverWait(driver, timeout_seconds)
    selectors = [
        (By.CSS_SELECTOR, "div[role='textbox'][contenteditable='true']"),
        (By.XPATH, "//div[@contenteditable='true' and @role='textbox']"),
        (By.XPATH, "//div[@aria-label='Message' and @contenteditable='true']"),
    ]

    last_error = None
    for selector in selectors:
        try:
            return wait.until(EC.element_to_be_clickable(selector))
        except TimeoutException as error:
            last_error = error

    raise TimeoutException("Could not find the Messenger message box.") from last_error


def send_message(driver, chat_url, message):
    driver.get(chat_url)
    print("Opening Messenger chat.")
    print("If Messenger asks you to log in, do it in the opened browser window.")
    print("If Messenger asks for a PIN to restore chats, enter it in the browser window.")

    message_box = find_message_box(driver)
    message_box.click()

    for line_number, line in enumerate(message.splitlines()):
        if line_number:
            message_box.send_keys(Keys.SHIFT, Keys.ENTER)
        message_box.send_keys(line)

    message_box.send_keys(Keys.ENTER)
    print("Message sent.")


def wait_before_closing():
    print("")
    print("The browser will stay open while this program is waiting.")
    print("Press Enter here only after you are done checking the browser.")
    try:
        input()
    except EOFError:
        time.sleep(600)


def wait_after_send(config):
    wait_seconds = int(config.get("wait_after_send_seconds", 10))
    wait_seconds = max(5, min(wait_seconds, 10))
    print("Waiting {} seconds so Messenger can finish sending.".format(wait_seconds))
    time.sleep(wait_seconds)


def main():
    driver = None
    try:
        config = load_config()
        wait_until(config["send_at"])
        driver = build_driver(config)
        try:
            send_message(driver, config["recipient_chat_url"], config["message"])
            wait_after_send(config)
            if config.get("close_after_send", False):
                driver.quit()
        except Exception:
            print("Messenger did not reach the message box yet.")
            print("Finish any login, PIN, or restore-chat step in the opened browser.")
            print("Then run this script again; it should reuse the same browser profile.")
            wait_before_closing()
            raise
        return 0
    except KeyboardInterrupt:
        print("Stopped by user.")
        return 130
    except Exception as error:
        print("Error: {}".format(error))
        if driver is not None:
            wait_before_closing()
        return 1


if __name__ == "__main__":
    sys.exit(main())

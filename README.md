# Messenger Scheduled Sender

Small Python/Selenium automation that opens Messenger at a specific time and sends a configured message.

## Important

Do not upload your real `messenger_automation_config.json` or `browser_profile` folder to GitHub. They may contain private chat links or browser session data.

This repo includes `messenger_automation_config.example.json` as a safe template.

## Setup

1. Install Python 3.8 or newer.
2. Install Selenium:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Copy the example config:

   ```powershell
   copy messenger_automation_config.example.json messenger_automation_config.json
   ```

4. Edit `messenger_automation_config.json`.

   ```json
   {
     "recipient_chat_url": "https://www.messenger.com/t/example.name",
     "send_at": "2026-06-09 21:30",
     "message": "Hello!",
     "browser": "chrome",
     "profile_folder": "browser_profile",
     "wait_after_send_seconds": 10,
     "close_after_send": false
   }
   ```

5. Run:

   ```powershell
   python messenger_scheduler.py
   ```

The first time the browser opens, log in to Messenger manually. If Messenger asks for a PIN to restore chats, enter it in the browser window.

## Notes

- Keep the computer awake and connected to the internet before the scheduled time.
- Keep the script running until the message is sent.
- The script waits 5 to 10 seconds after pressing send so Messenger can finish sending.
- If Chrome does not work, change `"browser": "chrome"` to `"browser": "edge"`.
- Use this only for your own account and messages you are allowed to send.

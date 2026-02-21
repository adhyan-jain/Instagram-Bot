# Instagram Auto-Reply Bot

An Instagram bot that monitors a specific chat and automatically responds to every message with a predefined text.

## Features

- Monitors a specific Instagram user's messages
- Automatically responds to every message received
- Session management (stays logged in)
- Configurable response message and check interval
- Tracks processed messages to avoid duplicate responses

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the bot:**

   Edit `.env` file and add your credentials:

   ```env
   YOUR_USERNAME=your_instagram_username
   YOUR_PASSWORD=your_instagram_password
   TARGET_USERNAME=username_to_monitor
   RESPONSE_MESSAGE=Your auto-reply message here
   CHECK_INTERVAL=10
   ```

   - `YOUR_USERNAME`: Your Instagram username
   - `YOUR_PASSWORD`: Your Instagram password
   - `TARGET_USERNAME`: The Instagram username you want to monitor
   - `RESPONSE_MESSAGE`: The text message to send as a response
   - `CHECK_INTERVAL`: How often to check for new messages (in seconds)

3. **Run the bot:**
   ```bash
   python bot.py
   ```

## How It Works

1. Logs into your Instagram account
2. Finds the conversation thread with the target user
3. Continuously monitors for new messages
4. When a new message is received from the target user, it automatically sends your configured response
5. Keeps track of processed messages to avoid sending duplicate responses

## Important Notes

- **Instagram Rate Limits:** Be cautious with the check interval. Setting it too low may trigger Instagram's spam detection
- **Session File:** A `session.json` file will be created to keep you logged in between runs
- **Security:** Keep your `.env` file secure and never share it (contains your password)
- **2FA:** If you have two-factor authentication enabled, the bot will prompt you for the verification code during first login. You may also need to approve the login from the Instagram app
- **Terms of Service:** Use responsibly and be aware of Instagram's Terms of Service regarding automation

## Troubleshooting

- **Login fails:** Check your username and password in `config.json`
- **Can't find thread:** Make sure you have an existing conversation with the target user
- **Rate limiting:** Increase the `check_interval` value
- **Challenge required:** Instagram may ask you to verify it's you - check your email/phone

## Stop the Bot

Press `Ctrl+C` to stop the bot gracefully.

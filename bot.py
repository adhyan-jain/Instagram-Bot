#!/usr/bin/env python3
"""
Instagram Bot - Monitors a specific chat and auto-responds to messages
"""

import time
import os
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InstagramBot:
    def __init__(self, username, password, target_username, response_message):
        """
        Initialize the Instagram bot
        
        Args:
            username: Your Instagram username
            password: Your Instagram password
            target_username: The Instagram username to monitor
            response_message: The message to send as a response
        """
        self.client = Client()
        self.username = username
        self.password = password
        self.target_username = target_username
        self.response_message = response_message
        self.target_user_id = None
        self.thread_id = None
        self.processed_messages = set()
        
    def login(self):
        """Login to Instagram with 2FA support"""
        try:
            logger.info(f"Logging in as {self.username}...")
            
            # Try to load session
            session_exists = os.path.exists("session.json")
            if session_exists:
                try:
                    self.client.load_settings("session.json")
                    self.client.login(self.username, self.password)
                    logger.info("Logged in using saved session")
                    return True
                except Exception as e:
                    logger.warning(f"Session login failed: {e}. Trying fresh login...")
            
            # Fresh login
            try:
                self.client.login(self.username, self.password)
                self.client.dump_settings("session.json")
                logger.info("Logged in successfully and saved new session")
                return True
            except ChallengeRequired as e:
                logger.warning("Instagram is asking for verification (2FA or Challenge)")
                logger.info("Attempting to handle challenge...")
                
                # Try to get verification code from user
                verification_code = input("Enter the verification code sent to your phone/email: ")
                self.client.challenge_code_handler(self.username, verification_code)
                self.client.dump_settings("session.json")
                logger.info("Challenge completed successfully!")
                return True
            
        except ChallengeRequired:
            logger.error("2FA verification required. Please check your phone/email for verification code.")
            logger.error("You may also need to approve the login from the Instagram app.")
            return False
        except Exception as e:
            error_message = str(e).lower()
            
            # Check for specific error types
            if "can't find an account" in error_message or "user not found" in error_message:
                logger.error(f"Login failed: {e}")
                logger.error("")
                logger.error("⚠️  ACCOUNT NOT FOUND - Instagram can't find this account")
                logger.error("📧 Note: You're using an EMAIL as username. Instagram accepts BOTH email and username.")
                logger.error("✅ Try updating YOUR_USERNAME in .env file to your Instagram username (e.g., @yourhandle)")
                logger.error("   Or make sure the email matches your Instagram account exactly")
            elif "password" in error_message or "incorrect" in error_message or "wrong" in error_message:
                logger.error(f"Login failed: {e}")
                logger.error("")
                logger.error("🔒 INCORRECT PASSWORD")
                logger.error("✅ Double-check YOUR_PASSWORD in .env file")
                logger.error("   Make sure there are no extra spaces or quotes")
            elif "checkpoint" in error_message or "challenge" in error_message:
                logger.error(f"Login failed: {e}")
                logger.error("")
                logger.error("🛡️  SECURITY CHECK REQUIRED")
                logger.error("✅ Instagram needs to verify it's you")
                logger.error("   Check your email/phone for verification code")
                logger.error("   You may need to verify from the Instagram app")
            elif "rate limit" in error_message or "too many" in error_message:
                logger.error(f"Login failed: {e}")
                logger.error("")
                logger.error("⏱️  TOO MANY LOGIN ATTEMPTS")
                logger.error("✅ Wait 10-15 minutes before trying again")
                logger.error("   Instagram has temporarily blocked login attempts")
            else:
                logger.error(f"Login failed: {e}")
                logger.error("")
                logger.error("💡 TROUBLESHOOTING TIPS:")
                logger.error("   1. Check YOUR_USERNAME in .env (can be email OR username)")
                logger.error("   2. Check YOUR_PASSWORD in .env (make sure it's correct)")
                logger.error("   3. If you have 2FA, the bot will prompt for verification code")
                logger.error("   4. You may need to approve login from Instagram app")
            
            return False
    
    def get_target_user_id(self):
        """Get the user ID of the target username"""
        try:
            logger.info(f"Getting user ID for {self.target_username}...")
            user_info = self.client.user_info_by_username(self.target_username)
            self.target_user_id = user_info.pk
            logger.info(f"Target user ID: {self.target_user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to get user ID: {e}")
            return False
    
    def get_thread_id(self):
        """Get the thread ID for the conversation with the target user"""
        try:
            logger.info("Getting thread ID...")
            threads = self.client.direct_threads(amount=100)
            
            for thread in threads:
                # Check if this thread is with our target user
                for user in thread.users:
                    if user.pk == self.target_user_id:
                        self.thread_id = thread.id
                        logger.info(f"Found thread ID: {self.thread_id}")
                        
                        # Mark all existing messages as processed to avoid replying to old messages
                        logger.info("Marking existing messages as already processed...")
                        existing_thread = self.client.direct_thread(self.thread_id)
                        for msg in existing_thread.messages:
                            self.processed_messages.add(msg.id)
                        logger.info(f"Marked {len(existing_thread.messages)} existing messages. Will only respond to NEW messages.")
                        
                        return True
            
            logger.warning("No existing thread found with target user")
            return False
        except Exception as e:
            logger.error(f"Failed to get thread ID: {e}")
            return False
    
    def check_and_respond(self):
        """Check for new messages and respond"""
        try:
            if not self.thread_id:
                logger.warning("No thread ID available")
                return
            
            # Get messages from the thread
            thread = self.client.direct_thread(self.thread_id)
            messages = thread.messages
            
            # Get current time (for checking message age)
            import datetime
            current_time = datetime.datetime.now(datetime.timezone.utc)
            
            # Process messages (newest first)
            for message in messages:
                message_id = message.id
                
                # Skip if already processed
                if message_id in self.processed_messages:
                    continue
                
                # Skip messages sent by us
                if message.user_id == self.client.user_id:
                    self.processed_messages.add(message_id)
                    continue
                
                # Check if message is from target user
                if message.user_id == self.target_user_id:
                    # Check message timestamp - only respond to recent messages (within last 5 minutes)
                    message_time = message.timestamp
                    
                    # Make sure message_time is timezone-aware
                    if message_time.tzinfo is None:
                        message_time = message_time.replace(tzinfo=datetime.timezone.utc)
                    
                    time_diff = (current_time - message_time).total_seconds()
                    
                    # If message is older than 5 minutes, mark as processed but don't respond
                    if time_diff > 300:  # 300 seconds = 5 minutes
                        logger.debug(f"Skipping old message from {int(time_diff/60)} minutes ago")
                        self.processed_messages.add(message_id)
                        continue
                    
                    logger.info(f"New message from {self.target_username}: {message.text}")
                    
                    # Send response
                    self.client.direct_send(self.response_message, [self.target_user_id])
                    logger.info(f"Sent response: {self.response_message}")
                    
                    # Mark as processed
                    self.processed_messages.add(message_id)
                    
                    # Keep only last 100 message IDs in memory
                    if len(self.processed_messages) > 100:
                        self.processed_messages = set(list(self.processed_messages)[-100:])
        
        except Exception as e:
            logger.error(f"Error checking messages: {e}")
    
    def run(self, check_interval=10):
        """
        Run the bot continuously
        
        Args:
            check_interval: Time in seconds between checks (default: 10)
        """
        logger.info("Starting Instagram Bot...")
        
        if not self.login():
            logger.error("Failed to login. Exiting.")
            return
        
        if not self.get_target_user_id():
            logger.error("Failed to get target user ID. Exiting.")
            return
        
        if not self.get_thread_id():
            logger.warning("No existing conversation found. Will try to send first message when they message you.")
        
        logger.info(f"Bot is now running. Monitoring messages from @{self.target_username}")
        logger.info(f"Will respond with: '{self.response_message}'")
        logger.info(f"Checking every {check_interval} seconds. Press Ctrl+C to stop.")
        
        try:
            while True:
                # Refresh thread ID if we don't have one
                if not self.thread_id:
                    self.get_thread_id()
                
                if self.thread_id:
                    self.check_and_respond()
                
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            logger.info("\nBot stopped by user.")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")


def main():
    """Main function to run the bot"""
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    username = os.getenv('YOUR_USERNAME')
    password = os.getenv('YOUR_PASSWORD')
    target_username = os.getenv('TARGET_USERNAME')
    response_message = os.getenv('RESPONSE_MESSAGE', 'Thanks for your message!')
    check_interval = int(os.getenv('CHECK_INTERVAL', '10'))
    
    # Validate required variables
    if not all([username, password, target_username]):
        logger.error("Missing required environment variables in .env file")
        logger.error("Please set: YOUR_USERNAME, YOUR_PASSWORD, TARGET_USERNAME")
        return
    
    # Create and run bot
    bot = InstagramBot(
        username=username,
        password=password,
        target_username=target_username,
        response_message=response_message
    )
    
    bot.run(check_interval=check_interval)


if __name__ == "__main__":
    main()

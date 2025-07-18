"""
Configuration file for UPSC Vault Bot
Contains bot credentials and settings.
"""

import os

# Bot credentials
BOT_TOKEN = os.getenv("BOT_TOKEN", "8012989049:AAF1C299k6dYCdOfiOL-u6q3MRgvAdEZz84")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7520583263"))

# Bot messages
WELCOME_MESSAGE = """👋 Welcome to UPSC Vault
I am your UPSC assistant for Prarambh 2028 batch.
I am created with love by @supriya_jaatnii @prernajoshi1 @utkarshtiwari27
Choose a section below ⬇️"""

# Database configuration
DATABASE_PATH = "upsc_vault.db"

# Default subjects with emojis
DEFAULT_SUBJECTS = [
    "🏛️ Ancient History",
    "🕌 Medieval History", 
    "🏫 Modern History",
    "🧠 Polity",
    "🌍 Geography",
    "📕 Ethics"
]

# Bot states for conversation handling
class BotState:
    NORMAL = "normal"
    ADDING_SUBJECT = "adding_subject"
    ADDING_LECTURE_NUMBER = "adding_lecture_number"
    ADDING_LECTURE_CONTENT = "adding_lecture_content"
    EDITING_LECTURE = "editing_lecture"
    RENAMING_SUBJECT = "renaming_subject"
    ADDING_BOOK_NAME = "adding_book_name"
    ADDING_BOOK_CONTENT = "adding_book_content"
    EDITING_BOOK = "editing_book"
    CHANGING_WELCOME = "changing_welcome"
    SEARCHING_CONTENT = "searching_content"
    SEARCHING_LECTURES = "searching_lectures"
    IMPORTING_JSON = "importing_json"

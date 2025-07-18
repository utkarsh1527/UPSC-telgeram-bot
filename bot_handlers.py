# Applying the requested changes to bot_handlers.py, including adding the enhanced admin interface handler and modifying the admin callback handling.
"""Enhanced bot handlers with new bot states for enhanced features."""
import logging
import time
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from config import ADMIN_ID, WELCOME_MESSAGE, BotState
from database import DatabaseManager
from keyboards import Keyboards

logger = logging.getLogger(__name__)

class BotHandlers:
    """Handles all bot interactions."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.user_states = {}  # Track user conversation states
        self.temp_data = {}    # Temporary data storage for multi-step operations
        self.state_timestamps = {}  # Track when states were last updated
        self._start_time = time.time()  # Track bot start time

        # Cleanup old states every hour
        self._last_cleanup = time.time()
        self._cleanup_interval = 3600  # 1 hour

    def _cleanup_old_states(self) -> None:
        """Clean up old user states to prevent memory leaks."""
        current_time = time.time()

        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        # Remove states older than 2 hours
        cutoff_time = current_time - 7200
        expired_users = [
            user_id for user_id, timestamp in self.state_timestamps.items()
            if timestamp < cutoff_time
        ]

        for user_id in expired_users:
            self.user_states.pop(user_id, None)
            self.temp_data.pop(user_id, None)
            self.state_timestamps.pop(user_id, None)

        self._last_cleanup = current_time

        if expired_users:
            logger.info(f"Cleaned up {len(expired_users)} expired user states")

    def _update_user_state(self, user_id: int, state: str) -> None:
        """Update user state with timestamp tracking."""
        self.user_states[user_id] = state
        self.state_timestamps[user_id] = time.time()
        self._cleanup_old_states()

    def _reset_user_state(self, user_id: int) -> None:
        """Reset user state and clean up temporary data."""
        self.user_states.pop(user_id, None)
        self.temp_data.pop(user_id, None)
        self.state_timestamps.pop(user_id, None)

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return user_id == ADMIN_ID

    async def _safe_edit_message(self, query, text: str, reply_markup=None, parse_mode=None):
        """Safely edit message with error handling."""
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            return True
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            # Try to send a new message if editing fails
            try:
                await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
                return True
            except Exception as e2:
                logger.error(f"Failed to send fallback message: {e2}")
                return False

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        try:
            user = update.effective_user
            is_admin = self.is_admin(user.id)

            # Reset user state
            self._reset_user_state(user.id)

            await update.message.reply_text(
                WELCOME_MESSAGE,
                reply_markup=Keyboards.main_menu(is_admin)
            )

            logger.info(f"User {user.id} ({user.username}) started the bot")

        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await update.message.reply_text("❌ Sorry, something went wrong. Please try again.")

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle all button callbacks."""
        try:
            query = update.callback_query
            await query.answer()

            user_id = query.from_user.id
            is_admin = self.is_admin(user_id)
            data = query.data

            logger.info(f"Button callback: {data} from user {user_id}")

            # Main menu handlers
            if data == "main_menu":
                await self._show_main_menu(query, is_admin)
            elif data == "lectures":
                await self._show_subjects(query, is_admin)
            elif data == "books":
                await self._show_books(query, is_admin)

            # Subject and lecture handlers
            elif data.startswith("subject_"):
                subject_id = int(data.split("_")[1])
                await self._show_lectures(query, subject_id, is_admin)
            elif data.startswith("lecture_"):
                lecture_id = int(data.split("_")[1])
                await self._show_lecture_content(query, lecture_id)

            # Books navigation
            elif data == "ncert_wallah":
                await self._show_ncert_wallah(query, is_admin)
            elif data == "upsc_wallah":
                await self._show_upsc_wallah(query, is_admin)
            elif data.startswith("ncert_book_"):
                book_id = int(data.split("_")[2])
                await self._show_book_content(query, book_id, "ncert")
            elif data.startswith("upsc_book_"):
                book_id = int(data.split("_")[2])
                await self._show_book_content(query, book_id, "upsc")
            elif data == "other_books":
                await self._show_other_books(query, is_admin)
            elif data.startswith("other_book_"):
                book_id = int(data.split("_")[2])
                await self._show_book_content(query, book_id, "other")

            # Admin handlers
            elif data == "admin_settings" and is_admin:
                await self._show_admin_menu(query)
            elif data == "enhanced_admin" and is_admin:
                await self._show_enhanced_admin_menu(query)
            elif is_admin:
                await self._handle_admin_callback(query, data)
            else:
                await self._safe_edit_message(query, "❌ Access denied or invalid option.")

        except Exception as e:
            logger.error(f"Error in button_callback: {e}")
            await self._safe_edit_message(query, "❌ Something went wrong. Please try again.")

    async def _show_main_menu(self, query, is_admin: bool) -> None:
        """Show main menu."""
        await self._safe_edit_message(
            query,
            WELCOME_MESSAGE,
            reply_markup=Keyboards.main_menu(is_admin)
        )

    async def _show_subjects(self, query, is_admin: bool) -> None:
        """Show subjects list."""
        try:
            subjects = self.db.get_subjects()

            if not subjects:
                text = "📚 No subjects available yet."
                if is_admin:
                    text += "\n\nUse ➕ Add Subject to create your first subject."
            else:
                text = "📚 Choose a subject:"

            await self._safe_edit_message(
                query,
                text,
                reply_markup=Keyboards.subjects_menu(subjects, is_admin)
            )
        except Exception as e:
            logger.error(f"Error showing subjects: {e}")
            await self._safe_edit_message(query, "❌ Error loading subjects. Please try again.")

    async def _show_lectures(self, query, subject_id: int, is_admin: bool) -> None:
        """Show lectures for a subject."""
        try:
            subject_name = self.db.get_subject_name(subject_id)
            if not subject_name:
                await self._safe_edit_message(query, "❌ Subject not found.")
                return

            lectures = self.db.get_lectures(subject_id)

            if not lectures:
                text = f"📖 {subject_name}\n\nNo lectures available yet."
                if is_admin:
                    text += "\n\nUse ➕ Add Lecture to create your first lecture."
            else:
                text = f"📖 {subject_name}\n\nChoose a lecture:"

            await self._safe_edit_message(
                query,
                text,
                reply_markup=Keyboards.lectures_menu(subject_id, lectures, is_admin)
            )
        except Exception as e:
            logger.error(f"Error showing lectures: {e}")
            await self._safe_edit_message(query, "❌ Error loading lectures. Please try again.")

    async def _show_lecture_content(self, query, lecture_id: int) -> None:
        """Show lecture content."""
        try:
            lecture = self.db.get_lecture(lecture_id)
            if not lecture:
                await self._safe_edit_message(query, "❌ Lecture not found.")
                return

            _, subject_id, lecture_no, content = lecture

            # Clean content for markdown parsing
            cleaned_content = self._clean_markdown(content)

            # Try with markdown first, fallback to plain text
            success = await self._safe_edit_message(
                query,
                cleaned_content,
                reply_markup=Keyboards.lecture_view(subject_id),
                parse_mode=ParseMode.MARKDOWN
            )

            if not success:
                await self._safe_edit_message(
                    query,
                    content,
                    reply_markup=Keyboards.lecture_view(subject_id)
                )

        except Exception as e:
            logger.error(f"Error showing lecture content: {e}")
            await self._safe_edit_message(query, "❌ Error loading lecture. Please try again.")

    async def _show_books(self, query, is_admin: bool) -> None:
        """Show books section main menu."""
        await self._safe_edit_message(
            query,
            "📘 Books Section\n\nChoose a category:",
            reply_markup=Keyboards.books_menu(is_admin)
        )

    async def _show_ncert_wallah(self, query, is_admin: bool) -> None:
        """Show NCERT Wallah books."""
        try:
            books = self.db.get_books("ncert")

            if not books:
                text = "📖 NCERT Wallah\n\nNo books available yet."
                if is_admin:
                    text += "\n\nUse ➕ Add NCERT Book to add your first book."
            else:
                text = "📖 NCERT Wallah\n\nChoose a book:"

            await self._safe_edit_message(
                query,
                text,
                reply_markup=Keyboards.ncert_wallah_menu(books, is_admin)
            )
        except Exception as e:
            logger.error(f"Error showing NCERT books: {e}")
            await self._safe_edit_message(query, "❌ Error loading books. Please try again.")

    async def _show_upsc_wallah(self, query, is_admin: bool) -> None:
        """Show UPSC Wallah books."""
        try:
            books = self.db.get_books("upsc")

            if not books:
                text = "📚 UPSC Wallah\n\nNo books available yet."
                if is_admin:
                    text += "\n\nUse ➕ Add UPSC Book to add your first book."
            else:
                text = "📚 UPSC Wallah\n\nChoose a book:"

            await self._safe_edit_message(
                query,
                text,
                reply_markup=Keyboards.upsc_wallah_menu(books, is_admin)
            )
        except Exception as e:
            logger.error(f"Error showing UPSC books: {e}")
            await self._safe_edit_message(query, "❌ Error loading books. Please try again.")

    async def _show_other_books(self, query, is_admin: bool) -> None:
        """Show Other books."""
        try:
            books = self.db.get_books("other")

            if not books:
                text = "📄 Other Books\n\nNo books available yet."
                if is_admin:
                    text += "\n\nUse ➕ Add Other Book to add your first book."
            else:
                text = "📄 Other Books\n\nChoose a book:"

            await self._safe_edit_message(
                query,
                text,
                reply_markup=Keyboards.other_books_menu(books, is_admin)
            )
        except Exception as e:
            logger.error(f"Error showing Other books: {e}")
            await self._safe_edit_message(query, "❌ Error loading books. Please try again.")

    async def _show_book_content(self, query, book_id: int, book_type: str) -> None:
        """Show book content."""
        try:
            book = self.db.get_book(book_id)
            if not book:
                await self._safe_edit_message(query, "❌ Book not found.")
                return

            _, book_name, _, content = book

            # Clean content for markdown parsing
            cleaned_content = self._clean_markdown(content)

            # Try with markdown first, fallback to plain text
            success = await self._safe_edit_message(
                query,
                cleaned_content,
                reply_markup=Keyboards.book_view(book_type),
                parse_mode=ParseMode.MARKDOWN
            )

            if not success:
                await self._safe_edit_message(
                    query,
                    content,
                    reply_markup=Keyboards.book_view(book_type)
                )

        except Exception as e:
            logger.error(f"Error showing book content: {e}")
            await self._safe_edit_message(query, "❌ Error loading book. Please try again.")

    async def _show_admin_menu(self, query) -> None:
        """Show admin menu."""
        stats = self.db.get_database_stats()
        text = "🛠️ Admin Control Panel\n\n"
        text += f"📊 Current Stats:\n"
        text += f"• {stats.get('subjects_count', 0)} subjects\n"
        text += f"• {stats.get('lectures_count', 0)} lectures\n"
        text += f"• {stats.get('total_books_count', 0)} books\n\n"
        text += "Choose an action:"

        await self._safe_edit_message(
            query,
            text,
            reply_markup=Keyboards.admin_menu()
        )

    async def _show_enhanced_admin_menu(self, query) -> None:
        """Show enhanced admin menu with quick add buttons."""
        stats = self.db.get_database_stats()
        text = "🚀 Enhanced Admin Panel\n\n"
        text += f"📊 Quick Stats:\n"
        text += f"• {stats.get('subjects_count', 0)} subjects\n"
        text += f"• {stats.get('lectures_count', 0)} lectures\n"
        text += f"• {stats.get('total_books_count', 0)} books\n\n"
        text += "🎯 Quick add buttons for fast content creation:"

        await self._safe_edit_message(
            query,
            text,
            reply_markup=Keyboards.admin_with_add_buttons()
        )

    async def _handle_admin_callback(self, query, data: str) -> None:
        """Handle admin-specific callbacks."""
        user_id = query.from_user.id

        try:
            # Add operations
            if data == "add_subject":
                self._update_user_state(user_id, BotState.ADDING_SUBJECT)
                await self._safe_edit_message(
                    query,
                    "📝 Enter the name of the new subject (with emoji if desired):",
                    reply_markup=Keyboards.main_menu(True)
                )

            elif data.startswith("add_lecture_"):
                subject_id = int(data.split("_")[2])
                self._update_user_state(user_id, BotState.ADDING_LECTURE_NUMBER)
                self.temp_data[user_id] = {"subject_id": subject_id}
                await self._safe_edit_message(
                    query,
                    "📝 Enter lecture number (e.g., 'Lecture 3'):",
                    reply_markup=Keyboards.main_menu(True)
                )

            # Management operations
            elif data == "manage_subjects":
                subjects = self.db.get_subjects()
                await self._safe_edit_message(
                    query,
                    "🗂️ Manage Subjects\n\nChoose an action:",
                    reply_markup=Keyboards.manage_subjects(subjects)
                )

            elif data == "manage_lectures":
                subjects = self.db.get_subjects()
                await self._safe_edit_message(
                    query,
                    "🗃️ Manage Lectures\n\nChoose a subject:",
                    reply_markup=Keyboards.manage_lectures_subjects(subjects)
                )

            elif data.startswith("manage_lectures_subject_"):
                subject_id = int(data.split("_")[3])
                subject_name = self.db.get_subject_name(subject_id)
                lectures = self.db.get_lectures(subject_id)
                await self._safe_edit_message(
                    query,
                    f"🗃️ Manage Lectures - {subject_name}",
                    reply_markup=Keyboards.manage_lectures_list(subject_id, lectures)
                )

            # Database operations
            elif data == "view_all_data":
                await self._handle_view_all_data(query)

            elif data == "database_tools":
                await self._handle_database_tools(query)

            elif data == "backup_database":
                await self._handle_backup_database(query)

            elif data == "optimize_database":
                await self._handle_optimize_database(query)

            elif data == "reset_database":
                await self._handle_reset_database_confirm(query)

            elif data == "confirm_reset_database":
                await self._handle_reset_database(query)

            # Bot management
            elif data == "bot_settings":
                await self._handle_bot_settings(query)

            elif data == "change_welcome_message":
                self._update_user_state(user_id, BotState.CHANGING_WELCOME)
                await self._safe_edit_message(
                    query,
                    "📝 Send the new welcome message:\n\n"
                    "Current message:\n" + WELCOME_MESSAGE,
                    reply_markup=Keyboards.admin_menu()
                )

            elif data == "view_bot_info":
                await self._handle_view_bot_info(query)

            elif data == "user_analytics":
                await self._handle_user_analytics(query)

            # Delete operations
            elif data.startswith("delete_subject_"):
                await self._handle_delete_confirmation(query, data, "subject")

            elif data.startswith("confirm_delete_subject_"):
                await self._handle_delete_subject(query, data)

            elif data.startswith("delete_lecture_"):
                await self._handle_delete_confirmation(query, data, "lecture")

            elif data.startswith("confirm_delete_lecture_"):
                await self._handle_delete_lecture(query, data)

            # Edit operations
            elif data.startswith("edit_lecture_"):
                lecture_id = int(data.split("_")[2])
                self._update_user_state(user_id, BotState.EDITING_LECTURE)
                self.temp_data[user_id] = {"lecture_id": lecture_id}
                await self._safe_edit_message(
                    query,
                    "📝 Send the new lecture content in Markdown format:\n\n"
                    "💡 For clickable links, use this format:\n"
                    "[LECTURE](https://youtu.be/example)\n"
                    "[CLASS NOTES](https://example.com/notes.pdf)\n\n"
                    "✅ Correct: [LECTURE](https://youtu.be/example)\n"
                    "❌ Wrong: [LECTURE (https://youtu.be/example)]",
                    reply_markup=Keyboards.admin_menu()
                )

            elif data.startswith("rename_subject_"):
                subject_id = int(data.split("_")[2])
                self._update_user_state(user_id, BotState.RENAMING_SUBJECT)
                self.temp_data[user_id] = {"subject_id": subject_id}
                await self._safe_edit_message(
                    query,
                    "📝 Enter the new name for the subject:",
                    reply_markup=Keyboards.admin_menu()
                )

            # Books management
            elif data == "manage_books":
                await self._safe_edit_message(
                    query,
                    "📚 Manage Books\n\nChoose a category:",
                    reply_markup=Keyboards.manage_books_menu()
                )

            elif data in ["manage_ncert_books", "manage_upsc_books", "manage_other_books"]:
                if "ncert" in data:
                    book_type = "ncert"
                    label = "NCERT"
                elif "upsc" in data:
                    book_type = "upsc"
                    label = "UPSC"
                else:
                    book_type = "other"
                    label = "Other"
                    
                books = self.db.get_books(book_type)
                await self._safe_edit_message(
                    query,
                    f"📖 Manage {label} Books",
                    reply_markup=Keyboards.manage_book_list(books, book_type)
                )

            elif data in ["add_ncert_book", "add_upsc_book", "add_other_book"]:
                if "ncert" in data:
                    book_type = "ncert"
                    label = "NCERT"
                elif "upsc" in data:
                    book_type = "upsc"
                    label = "UPSC"
                else:
                    book_type = "other"
                    label = "Other"
                    
                self._update_user_state(user_id, BotState.ADDING_BOOK_NAME)
                self.temp_data[user_id] = {"book_type": book_type}
                await self._safe_edit_message(
                    query,
                    f"📝 Enter the name of the {label} book:",
                    reply_markup=Keyboards.main_menu(True)
                )

            # Book delete/edit operations
            elif data.startswith(("delete_ncert_book_", "delete_upsc_book_", "delete_other_book_")):
                await self._handle_book_delete_confirmation(query, data)

            elif data.startswith(("confirm_delete_ncert_book_", "confirm_delete_upsc_book_", "confirm_delete_other_book_")):
                await self._handle_delete_book(query, data)

            elif data.startswith(("edit_ncert_book_", "edit_upsc_book_", "edit_other_book_")):
                book_id = int(data.split("_")[3])
                self._update_user_state(user_id, BotState.EDITING_BOOK)
                self.temp_data[user_id] = {"book_id": book_id}
                await self._safe_edit_message(
                    query,
                    "📝 Send the new book content in Markdown format:\n\n"
                    "💡 For clickable links, use this format:\n"
                    "[DOWNLOAD LINK](https://example.com/book.pdf)\n"
                    "[READ ONLINE](https://example.com/read)\n\n"
                    "✅ Correct: [DOWNLOAD](https://example.com/book.pdf)\n"
                    "❌ Wrong: [DOWNLOAD (https://example.com/book.pdf)]",
                    reply_markup=Keyboards.manage_books_menu()
                )
            elif data == "search_content":
                self._update_user_state(user_id, "SEARCHING_CONTENT")
                await self._safe_edit_message(
                    query,
                    "📝 Enter the content you want to search for:",
                    reply_markup=Keyboards.admin_menu()
                )
            elif data == "search_lectures":
                 self._update_user_state(user_id, "SEARCHING_LECTURES")
                 await self._safe_edit_message(
                    query,
                    "📝 Enter the lecture you want to search for:",
                    reply_markup=Keyboards.admin_menu()
            )

            elif data == "import_json":
                self._update_user_state(user_id, "IMPORTING_JSON")
                await self._safe_edit_message(
                    query,
                    "📝 Send the JSON file containing the data to import:",
                    reply_markup=Keyboards.admin_menu()
                )

        except Exception as e:
            logger.error(f"Error in admin callback {data}: {e}")
            await self._safe_edit_message(query, "❌ Error processing request. Please try again.")

    async def _handle_delete_confirmation(self, query, data: str, item_type: str) -> None:
        """Handle delete confirmation dialogs."""
        try:
            if item_type == "subject":
                subject_id = int(data.split("_")[2])
                subject_name = self.db.get_subject_name(subject_id)
                if subject_name:
                    await self._safe_edit_message(
                        query,
                        f"🗑️ Are you sure you want to delete '{subject_name}' and all its lectures?",
                        reply_markup=Keyboards.confirmation("delete_subject", subject_id)
                    )
            elif item_type == "lecture":
                lecture_id = int(data.split("_")[2])
                lecture = self.db.get_lecture(lecture_id)
                if lecture:
                    await self._safe_edit_message(
                        query,
                        f"🗑️ Are you sure you want to delete '{lecture[2]}'?",
                        reply_markup=Keyboards.confirmation("delete_lecture", lecture_id)
                    )
        except Exception as e:
            logger.error(f"Error in delete confirmation: {e}")
            await self._safe_edit_message(query, "❌ Error loading item details.")

    async def _handle_delete_subject(self, query, data: str) -> None:
        """Handle subject deletion."""
        try:
            subject_id = int(data.split("_")[3])
            if self.db.delete_subject(subject_id):
                await self._safe_edit_message(
                    query,
                    "✅ Subject deleted successfully!",
                    reply_markup=Keyboards.admin_menu()
                )
            else:
                await self._safe_edit_message(
                    query,
                    "❌ Failed to delete subject.",
                    reply_markup=Keyboards.admin_menu()
                )
        except Exception as e:
            logger.error(f"Error deleting subject: {e}")
            await self._safe_edit_message(query, "❌ Error deleting subject.")

    async def _handle_delete_lecture(self, query, data: str) -> None:
        """Handle lecture deletion."""
        try:
            lecture_id = int(data.split("_")[3])
            if self.db.delete_lecture(lecture_id):
                await self._safe_edit_message(
                    query,
                    "✅ Lecture deleted successfully!",
                    reply_markup=Keyboards.admin_menu()
                )
            else:
                await self._safe_edit_message(
                    query,
                    "❌ Failed to delete lecture.",
                    reply_markup=Keyboards.admin_menu()
                )
        except Exception as e:
            logger.error(f"Error deleting lecture: {e}")
            await self._safe_edit_message(query, "❌ Error deleting lecture.")

    async def _handle_book_delete_confirmation(self, query, data: str) -> None:
        """Handle book delete confirmation."""
        try:
            parts = data.split("_")
            book_type = parts[1]
            book_id = int(parts[3])
            book = self.db.get_book(book_id)
            if book:
                await self._safe_edit_message(
                    query,
                    f"🗑️ Are you sure you want to delete '{book[1]}'?",
                    reply_markup=Keyboards.confirmation(f"delete_{book_type}_book", book_id)
                )
        except Exception as e:
            logger.error(f"Error in book delete confirmation: {e}")
            await self._safe_edit_message(query, "❌ Error loading book details.")

    async def _handle_delete_book(self, query, data: str) -> None:
        """Handle book deletion."""
        try:
            parts = data.split("_")
            book_id = int(parts[4])
            if self.db.delete_book(book_id):
                await self._safe_edit_message(
                    query,
                    "✅ Book deleted successfully!",
                    reply_markup=Keyboards.manage_books_menu()
                )
            else:
                await self._safe_edit_message(
                    query,
                    "❌ Failed to delete book.",
                    reply_markup=Keyboards.manage_books_menu()
                )
        except Exception as e:
            logger.error(f"Error deleting book: {e}")
            await self._safe_edit_message(query, "❌ Error deleting book.")

    async def _handle_view_all_data(self, query) -> None:
        """Handle view all data request."""
        try:
            subjects = self.db.get_subjects()
            text = "🧾 Database Overview\n\n"

            total_lectures = 0
            total_books = 0

            for subject_id, subject_name in subjects:
                lectures = self.db.get_lectures(subject_id)
                lecture_count = len(lectures)
                total_lectures += lecture_count
                text += f"📚 {subject_name} ({lecture_count} lectures)\n"

            # Count books
            ncert_books = self.db.get_books("ncert")
            upsc_books = self.db.get_books("upsc")
            other_books = self.db.get_books("other")
            total_books = len(ncert_books) + len(upsc_books) + len(other_books)

            if not subjects:
                text += "No subjects available.\n"

            text += f"\n📊 Summary:\n"
            text += f"• {len(subjects)} subjects\n"
            text += f"• {total_lectures} lectures\n"
            text += f"• {total_books} books ({len(ncert_books)} NCERT, {len(upsc_books)} UPSC, {len(other_books)} Other)"

            await self._safe_edit_message(
                query,
                text,
                reply_markup=Keyboards.admin_menu()
            )
        except Exception as e:
            logger.error(f"Error viewing all data: {e}")
            await self._safe_edit_message(query, "❌ Error loading data overview.")

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages based on user state."""
        try:
            user = update.effective_user
            user_id = user.id
            text = update.message.text

            if not self.is_admin(user_id):
                await update.message.reply_text("❌ This bot only responds to button interactions.")
                return

            state = self.user_states.get(user_id, BotState.NORMAL)

            # Route to appropriate handler based on state
            handlers = {
                BotState.ADDING_SUBJECT: self._handle_add_subject,
                BotState.ADDING_LECTURE_NUMBER: self._handle_add_lecture_number,
                BotState.ADDING_LECTURE_CONTENT: self._handle_add_lecture_content,
                BotState.EDITING_LECTURE: self._handle_edit_lecture,
                BotState.RENAMING_SUBJECT: self._handle_rename_subject,
                BotState.ADDING_BOOK_NAME: self._handle_add_book_name,
                BotState.ADDING_BOOK_CONTENT: self._handle_add_book_content,
                BotState.EDITING_BOOK: self._handle_edit_book,
                BotState.CHANGING_WELCOME: self._handle_change_welcome_message,
                "SEARCHING_CONTENT": self._handle_search_content_input,
                "SEARCHING_LECTURES": self._handle_search_lectures_input,
                "IMPORTING_JSON": self._handle_import_json_file,
        }

            handler = handlers.get(state)
            if handler:
                await handler(update, text)
            else:
                await update.message.reply_text(
                    "Use the buttons to navigate the bot.",
                    reply_markup=Keyboards.main_menu(True)
                )

        except Exception as e:
            logger.error(f"Error in handle_text_message: {e}")
            await update.message.reply_text("❌ Something went wrong. Please try again.")

    def _clean_markdown(self, content: str) -> str:
        """Clean markdown content to fix common parsing issues while preserving links."""
        import re

        try:
            # Store links to preserve them
            links = []
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'

            def store_link(match):
                links.append(match.group(0))
                return f"__LINK_{len(links)-1}__"

            # Extract and store all valid markdown links
            content = re.sub(link_pattern, store_link, content)

            # Fix common malformed patterns
            content = re.sub(r'\[([^\]]+)\s+\(([^)]+)\)\]', r'[\1](\2)', content)
            content = re.sub(r'\[([^\]]+)\]\(([^)]+)\]', r'[\1](\2)', content)
            content = re.sub(r'([A-Z\s]+)\s+\(([^)]+)\)', r'[\1](\2)', content)

            # Escape problematic characters
            content = re.sub(r'(?<!__LINK_\d)_(?!_)(?!\d+__)', r'\_', content)
            content = re.sub(r'(?<!__LINK_\d)\*(?!\*)(?!\d+__)', r'\*', content)

            # Restore the links
            for i, link in enumerate(links):
                content = content.replace(f"__LINK_{i}__", link)

            return content
        except Exception as e:
            logger.error(f"Error cleaning markdown: {e}")
            return content  # Return original if cleaning fails

    # Text message handlers
    async def _handle_add_subject(self, update: Update, subject_name: str) -> None:
        """Handle adding a new subject."""
        user_id = update.effective_user.id

        try:
            if self.db.add_subject(subject_name):
                self._reset_user_state(user_id)
                await update.message.reply_text(
                    f"✅ Subject '{subject_name}' added successfully!",
                    reply_markup=Keyboards.main_menu(True)
                )
            else:
                await update.message.reply_text(
                    f"❌ Subject '{subject_name}' already exists or could not be added.",
                    reply_markup=Keyboards.main_menu(True)
                )
        except Exception as e:
            logger.error(f"Error adding subject: {e}")
            await update.message.reply_text("❌ Error adding subject. Please try again.")

    async def _handle_add_lecture_number(self, update: Update, lecture_no: str) -> None:
        """Handle lecture number input."""
        user_id = update.effective_user.id
        self.temp_data[user_id]["lecture_no"] = lecture_no
        self._update_user_state(user_id, BotState.ADDING_LECTURE_CONTENT)

        await update.message.reply_text(
            f"📝 Now send the full lecture content for '{lecture_no}' in Markdown format:\n\n"
            f"💡 For clickable links, use this format:\n"
            f"[LECTURE](https://youtu.be/example)\n"
            f"[CLASS NOTES](https://example.com/notes.pdf)\n\n"
            f"✅ Correct: [LECTURE](https://youtu.be/example)\n"
            f"❌ Wrong: [LECTURE (https://youtu.be/example)]",
            reply_markup=Keyboards.main_menu(True))

    async def _handle_add_lecture_content(self, update: Update, content: str) -> None:
        """Handle lecture content input."""
        user_id = update.effective_user.id
        temp_data = self.temp_data.get(user_id, {})

        try:
            if "subject_id" in temp_data and "lecture_no" in temp_data:
                subject_id = temp_data["subject_id"]
                lecture_no = temp_data["lecture_no"]

                if self.db.add_lecture(subject_id, lecture_no, content):
                    self._reset_user_state(user_id)
                    await update.message.reply_text(
                        f"✅ Lecture '{lecture_no}' added successfully!",
                        reply_markup=Keyboards.main_menu(True)
                    )
                else:
                    await update.message.reply_text(
                        "❌ Failed to add lecture. Please try again.",
                        reply_markup=Keyboards.main_menu(True)
                    )
            else:
                self._reset_user_state(user_id)
                await update.message.reply_text(
                    "❌ Session expired. Please start over.",
                    reply_markup=Keyboards.main_menu(True)
                )
        except Exception as e:
            logger.error(f"Error adding lecture content: {e}")
            await update.message.reply_text("❌ Error adding lecture. Please try again.")

    async def _handle_edit_lecture(self, update: Update, content: str) -> None:
        """Handle lecture editing."""
        user_id = update.effective_user.id
        temp_data = self.temp_data.get(user_id, {})

        try:
            if "lecture_id" in temp_data:
                lecture_id = temp_data["lecture_id"]

                if self.db.update_lecture(lecture_id, content):
                    self._reset_user_state(user_id)
                    await update.message.reply_text(
                        "✅ Lecture updated successfully!",
                        reply_markup=Keyboards.main_menu(True)
                    )
                else:
                    await update.message.reply_text(
                        "❌ Failed to update lecture.",
                        reply_markup=Keyboards.main_menu(True)
                    )
            else:
                self._reset_user_state(user_id)
                await update.message.reply_text(
                    "❌ Session expired. Please start over.",
                    reply_markup=Keyboards.main_menu(True)
                )
        except Exception as e:
            logger.error(f"Error editing lecture: {e}")
            await update.message.reply_text("❌ Error updating lecture. Please try again.")

    async def _handle_rename_subject(self, update: Update, new_name: str) -> None:
        """Handle subject renaming."""
        user_id = update.effective_user.id
        temp_data = self.temp_data.get(user_id, {})

        try:
            if "subject_id" in temp_data:
                subject_id = temp_data["subject_id"]

                if self.db.rename_subject(subject_id, new_name):
                    self._reset_user_state(user_id)
                    await update.message.reply_text(
                        f"✅ Subject renamed to '{new_name}' successfully!",
                        reply_markup=Keyboards.main_menu(True)
                    )
                else:
                    await update.message.reply_text(
                        "❌ Failed to rename subject.",
                        reply_markup=Keyboards.main_menu(True)
                    )
            else:
                self._reset_user_state(user_id)
                await update.message.reply_text(
                    "❌ Session expired. Please start over.",
                    reply_markup=Keyboards.main_menu(True)
                )
        except Exception as e:
            logger.error(f"Error renaming subject: {e}")
            await update.message.reply_text("❌ Error renaming subject. Please try again.")

    async def _handle_add_book_name(self, update: Update, book_name: str) -> None:
        """Handle book name input."""
        user_id = update.effective_user.id
        self.temp_data[user_id]["book_name"] = book_name
        self._update_user_state(user_id, BotState.ADDING_BOOK_CONTENT)

        book_type = self.temp_data[user_id]["book_type"]
        book_label = "NCERT" if book_type == "ncert" else "UPSC"

        await update.message.reply_text(
            f"📝 Now send the content for '{book_name}' in Markdown format:\n\n"
            f"💡 For clickable links, use this format:\n"
            f"[DOWNLOAD LINK](https://example.com/book.pdf)\n"
            f"[READ ONLINE](https://example.com/read)\n\n"
            f"✅ Correct: [DOWNLOAD](https://example.com/book.pdf)\n"
            f"❌ Wrong: [DOWNLOAD (https://example.com/book.pdf)]",
            reply_markup=Keyboards.main_menu(True)
        )

    async def _handle_add_book_content(self, update: Update, content: str) -> None:
        """Handle book content input."""
        user_id = update.effective_user.id
        temp_data = self.temp_data.get(user_id, {})

        try:
            if "book_type" in temp_data and "book_name" in temp_data:
                book_type = temp_data["book_type"]
                book_name = temp_data["book_name"]

                if self.db.add_book(book_name, book_type, content):
                    self._reset_user_state(user_id)
                    book_label = "NCERT" if book_type == "ncert" else "UPSC"
                    await update.message.reply_text(
                        f"✅ {book_label} book '{book_name}' added successfully!",
                        reply_markup=Keyboards.main_menu(True)
                    )
                else:
                    await update.message.reply_text(
                        "❌ Failed to add book. Please try again.",
                        reply_markup=Keyboards.main_menu(True)
                    )
            else:
                self._reset_user_state(user_id)
                await update.message.reply_text(
                    "❌ Session expired. Please start over.",
                    reply_markup=Keyboards.main_menu(True)
                )
        except Exception as e:
            logger.error(f"Error adding book content: {e}")
            await update.message.reply_text("❌ Error adding book. Please try again.")

    async def _handle_edit_book(self, update: Update, content: str) -> None:
        """Handle book editing."""
        user_id = update.effective_user.id
        temp_data = self.temp_data.get(user_id, {})

        try:
            if "book_id" in temp_data:
                book_id = temp_data["book_id"]

                if self.db.update_book(book_id, content):
                    self._reset_user_state(user_id)
                    await update.message.reply_text(
                        "✅ Book updated successfully!",
                        reply_markup=Keyboards.main_menu(True)
                    )
                else:
                    await update.message.reply_text(
                        "❌ Failed to update book.",
                        reply_markup=Keyboards.main_menu(True)
                    )
            else:
                self._reset_user_state(user_id)
                await update.message.reply_text(
                    "❌ Session expired. Please start over.",
                    reply_markup=Keyboards.main_menu(True)
                )
        except Exception as e:
            logger.error(f"Error editing book: {e}")
            await update.message.reply_text("❌ Error updating book. Please try again.")

    async def _handle_database_tools(self, query) -> None:
        """Show database tools menu."""
        await self._safe_edit_message(
            query,
            "🗄️ Database Tools\n\nChoose an operation:",
            reply_markup=Keyboards.database_tools_menu()
        )

    async def _handle_backup_database(self, query) -> None:
        """Handle database backup."""
        try:
            backup_text = self.db.export_database()

            # Create backup as text file
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"upsc_vault_backup_{timestamp}.txt"

            await query.message.reply_document(
                document=backup_text.encode('utf-8'),
                filename=filename,
                caption="💾 Database backup created successfully!\n\n"
                       "This backup contains all your data in text format."
            )

            await self._safe_edit_message(
                query,
                "✅ Backup created and sent!",
                reply_markup=Keyboards.database_tools_menu()
            )
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            await self._safe_edit_message(query, "❌ Backup failed. Please try again.")

    async def _handle_optimize_database(self, query) -> None:
        """Handle database optimization."""
        try:
            if self.db.vacuum_database():
                await self._safe_edit_message(
                    query,
                    "✅ Database optimized successfully!\n\n"
                    "The database has been cleaned and performance improved.",
                    reply_markup=Keyboards.database_tools_menu()
                )
            else:
                await self._safe_edit_message(
                    query,
                    "❌ Database optimization failed.",
                    reply_markup=Keyboards.database_tools_menu()
                )
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            await self._safe_edit_message(query, "❌ Optimization failed. Please try again.")

    async def _handle_reset_database_confirm(self, query) -> None:
        """Show database reset confirmation."""
        await self._safe_edit_message(
            query,
            "⚠️ **DANGER ZONE**\n\n"
            "Are you sure you want to reset the entire database?\n\n"
            "**This will permanently delete:**\n"
            "• All subjects\n"
            "• All lectures\n"
            "• All books\n\n"
            "**This action cannot be undone!**",
            reply_markup=Keyboards.dangerous_confirmation("reset_database"),
            parse_mode='Markdown'
        )

    async def _handle_reset_database(self, query) -> None:
        """Handle database reset."""
        try:
            if self.db.reset_database():
                await self._safe_edit_message(
                    query,
                    "✅ Database reset successfully!\n\n"
                    "All data has been cleared and default subjects restored.",
                    reply_markup=Keyboards.admin_menu()
                )
            else:
                await self._safe_edit_message(
                    query,
                    "❌ Database reset failed.",
                    reply_markup=Keyboards.admin_menu()
                )
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            await self._safe_edit_message(query, "❌ Reset failed. Please try again.")

    async def _handle_bot_settings(self, query) -> None:
        """Show bot settings menu."""
        await self._safe_edit_message(
            query,
            "⚙️ Bot Settings\n\nConfigure bot behavior:",
            reply_markup=Keyboards.bot_settings_menu()
        )

    async def _handle_view_bot_info(self, query) -> None:
        """Show bot information."""
        import time
        uptime = time.time() - getattr(self, '_start_time', time.time())
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)

        text = "🤖 Bot Information\n\n"
        text += f"📊 Uptime: {hours}h {minutes}m\n"
        text += f"👤 Admin ID: {ADMIN_ID}\n"
        text += f"📝 Active States: {len(self.user_states)}\n"
        text += f"💾 Temp Data: {len(self.temp_data)}\n\n"
        text += "🔧 Features:\n"
        text += "• Multi-step operations\n"
        text += "• State management\n"
        text += "• Auto cleanup\n"
        text += "• Error recovery\n"
        text += "• Markdown support"

        await self._safe_edit_message(
            query,
            text,
            reply_markup=Keyboards.bot_settings_menu()
        )

    async def _handle_user_analytics(self, query) -> None:
        """Show user analytics."""
        try:
            stats = self.db.get_database_stats()

            text = "📈 Analytics Dashboard\n\n"
            text += f"📚 Content Stats:\n"
            text += f"• {stats.get('subjects_count', 0)} subjects created\n"
            text += f"• {stats.get('lectures_count', 0)} lectures published\n"
            text += f"• {stats.get('ncert_books_count', 0)} NCERT books\n"
            text += f"• {stats.get('upsc_books_count', 0)} UPSC books\n"
            text += f"• {stats.get('other_books_count', 0)} other books\n\n"

            text += f"💾 Database:\n"
            text += f"• Size: {stats.get('database_size_bytes', 0) / 1024:.1f} KB\n"

            # Calculate average lectures per subject
            subjects_count = stats.get('subjects_count', 1)
            lectures_count = stats.get('lectures_count', 0)
            avg_lectures = lectures_count / subjects_count if subjects_count > 0 else 0
            text += f"• Avg lectures/subject: {avg_lectures:.1f}\n\n"

            text += f"🎯 Usage Patterns:\n"
            text += f"• Most active admin features\n"
            text += f"• Content creation trends\n"
            text += f"• Error frequency: Low ✅"

            await self._safe_edit_message(
                query,
                text,
                reply_markup=Keyboards.admin_menu()
            )
        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            await self._safe_edit_message(query, "❌ Failed to load analytics.")

    async def _handle_change_welcome_message(self, update: Update, new_message: str) -> None:
        """Handle welcome message change."""
        user_id = update.effective_user.id

        try:
            # Update the welcome message in config (for this session)
            import config
            config.WELCOME_MESSAGE = new_message.strip()

            self._reset_user_state(user_id)
            await update.message.reply_text(
                f"✅ Welcome message updated successfully!\n\n"
                f"New message:\n{new_message}",
                reply_markup=Keyboards.admin_menu()
            )
        except Exception as e:
            logger.error(f"Error updating welcome message: {e}")
            await update.message.reply_text("❌ Error updating welcome message. Please try again.")

    async def _handle_search_content_input(self, update: Update, search_query: str) -> None:
        """Handle content search input."""
        user_id = update.effective_user.id
        try:
            # Search for content across all subjects and books
            search_results = self.db.search_content(search_query)

            if search_results:
                text = f"🔍 Search results for '{search_query}':\n\n"
                for item_type, item_id, item_name, context_snippet in search_results:
                    text += f"- {item_type.capitalize()}: {item_name}\n"
                    text += f"  Context: {context_snippet}\n\n"
            else:
                text = f"❌ No results found for '{search_query}'.\n\n"

            self._reset_user_state(user_id)
            await update.message.reply_text(
                text,
                reply_markup=Keyboards.admin_menu()  # Or a more appropriate keyboard
            )
        except Exception as e:
            logger.error(f"Error during content search: {e}")
            await update.message.reply_text("❌ Error searching content. Please try again.")

    async def _handle_search_lectures_input(self, update: Update, search_query: str) -> None:
        """Handle lectures search input."""
        user_id = update.effective_user.id
        try:
            # Search for lectures based on the query
            search_results = self.db.search_lectures(search_query)

            if search_results:
                text = f"🔍 Lecture search results for '{search_query}':\n\n"
                for lecture_id, subject_name, lecture_no in search_results:
                    text += f"- Lecture: {lecture_no} (Subject: {subject_name})\n"
                    text += f"  /view_lecture_{lecture_id}\n\n"  # Example command to view lecture
            else:
                text = f"❌ No lectures found for '{search_query}'.\n\n"

            self._reset_user_state(user_id)
            await update.message.reply_text(
                text,
                reply_markup=Keyboards.admin_menu()  # Or a more appropriate keyboard
            )
        except Exception as e:
            logger.error(f"Error during lecture search: {e}")
            await update.message.reply_text("❌ Error searching lectures. Please try again.")

    async def _handle_import_json_file(self, update: Update, file_content: str) -> None:
        """Handle importing data from a JSON file."""
        user_id = update.effective_user.id
        try:
            import json
            try:
                data = json.loads(file_content)
            except json.JSONDecodeError:
                await update.message.reply_text(
                    "❌ Invalid JSON format. Please provide a valid JSON file.",
                    reply_markup=Keyboards.admin_menu()
                )
                return

            # Validate data structure (example - adjust as per your data structure)
            if not isinstance(data, list):
                await update.message.reply_text(
                    "❌ Invalid data structure. Expected a list of items.",
                    reply_markup=Keyboards.admin_menu()
                )
                return

            # Process each item in the list and import it to the database
            imported_count = 0
            for item in data:
                # Example: Assuming each item has subject_name, lecture_no, content
                subject_name = item.get("subject_name")
                lecture_no = item.get("lecture_no")
                content = item.get("content")

                if subject_name and lecture_no and content:
                    # First, check if the subject exists, if not, create it
                    subject_id = self.db.get_subject_id(subject_name)
                    if not subject_id:
                        subject_id = self.db.add_subject(subject_name)

                    if subject_id:
                        # Now add the lecture to the subject
                        if self.db.add_lecture(subject_id, lecture_no, content):
                            imported_count += 1

            self._reset_user_state(user_id)
            await update.message.reply_text(
                f"✅ Successfully imported {imported_count} items from the JSON file.",
                reply_markup=Keyboards.admin_menu()
            )

        except Exception as e:
            logger.error(f"Error importing JSON data: {e}")
            await update.message.reply_text("❌ Error importing JSON data. Please try again.")
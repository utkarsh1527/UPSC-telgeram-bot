"""
Keyboard layouts for UPSC Vault Bot
Contains all inline keyboard configurations.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Tuple

class Keyboards:
    """Static class for keyboard layouts."""
    
    @staticmethod
    def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        """Main menu keyboard."""
        keyboard = [
            [InlineKeyboardButton("📚 Lectures", callback_data="lectures")],
            [InlineKeyboardButton("📘 Books", callback_data="books")]
        ]
        
        if is_admin:
            keyboard.append([InlineKeyboardButton("🛠️ Admin Settings", callback_data="admin_settings")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def subjects_menu(subjects: List[Tuple[int, str]], is_admin: bool = False) -> InlineKeyboardMarkup:
        """Subjects list keyboard."""
        keyboard = []
        
        for subject_id, subject_name in subjects:
            keyboard.append([InlineKeyboardButton(subject_name, callback_data=f"subject_{subject_id}")])
        
        if is_admin:
            keyboard.append([InlineKeyboardButton("➕ Add Subject", callback_data="add_subject")])
        
        keyboard.append([InlineKeyboardButton("↩️ Back", callback_data="main_menu")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def lectures_menu(subject_id: int, lectures: List[Tuple[int, str, str]], is_admin: bool = False) -> InlineKeyboardMarkup:
        """Lectures list keyboard."""
        keyboard = []
        
        for lecture_id, lecture_no, _ in lectures:
            keyboard.append([InlineKeyboardButton(f"▶️ {lecture_no}", callback_data=f"lecture_{lecture_id}")])
        
        if is_admin:
            keyboard.append([InlineKeyboardButton("➕ Add Lecture", callback_data=f"add_lecture_{subject_id}")])
        
        keyboard.append([InlineKeyboardButton("↩️ Back to Subjects", callback_data="lectures")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def lecture_view(subject_id: int) -> InlineKeyboardMarkup:
        """Lecture view keyboard."""
        keyboard = [
            [InlineKeyboardButton("↩️ Back to Lectures", callback_data=f"subject_{subject_id}")],
            [InlineKeyboardButton("📂 Menu", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        """Enhanced admin control panel."""
        keyboard = [
            [InlineKeyboardButton("📚 Content Management", callback_data="manage_subjects"),
             InlineKeyboardButton("📖 Books Management", callback_data="manage_books")],
            [InlineKeyboardButton("🗄️ Database Tools", callback_data="database_tools"),
             InlineKeyboardButton("⚙️ Bot Settings", callback_data="bot_settings")],
            [InlineKeyboardButton("📈 Analytics", callback_data="user_analytics"),
             InlineKeyboardButton("🧾 View All Data", callback_data="view_all_data")],
            [InlineKeyboardButton("🔧 Quick Actions", callback_data="quick_actions"),
             InlineKeyboardButton("📤 Import/Export", callback_data="import_export")],
            [InlineKeyboardButton("↩️ Back to Menu", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def manage_subjects(subjects: List[Tuple[int, str]]) -> InlineKeyboardMarkup:
        """Manage subjects keyboard."""
        keyboard = []
        
        for subject_id, subject_name in subjects:
            keyboard.append([
                InlineKeyboardButton(f"🗑️ Delete {subject_name}", callback_data=f"delete_subject_{subject_id}"),
                InlineKeyboardButton(f"📝 Rename", callback_data=f"rename_subject_{subject_id}")
            ])
        
        # Add "Add New Subject" button
        keyboard.append([InlineKeyboardButton("➕ Add New Subject", callback_data="add_subject")])
        keyboard.append([InlineKeyboardButton("↩️ Back", callback_data="admin_settings")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def manage_lectures_subjects(subjects: List[Tuple[int, str]]) -> InlineKeyboardMarkup:
        """Choose subject for lecture management."""
        keyboard = []
        
        for subject_id, subject_name in subjects:
            keyboard.append([InlineKeyboardButton(subject_name, callback_data=f"manage_lectures_subject_{subject_id}")])
        
        keyboard.append([InlineKeyboardButton("↩️ Back", callback_data="admin_settings")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def manage_lectures_list(subject_id: int, lectures: List[Tuple[int, str, str]]) -> InlineKeyboardMarkup:
        """Manage lectures for a subject."""
        keyboard = []
        
        for lecture_id, lecture_no, _ in lectures:
            keyboard.append([
                InlineKeyboardButton(f"🗑️ Delete {lecture_no}", callback_data=f"delete_lecture_{lecture_id}"),
                InlineKeyboardButton(f"📝 Edit", callback_data=f"edit_lecture_{lecture_id}")
            ])
        
        # Add "Add New Lecture" button
        keyboard.append([InlineKeyboardButton("➕ Add New Lecture", callback_data=f"add_lecture_{subject_id}")])
        keyboard.append([InlineKeyboardButton("↩️ Back", callback_data="manage_lectures")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def books_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
        """Books section main menu."""
        keyboard = [
            [InlineKeyboardButton("📖 NCERT Wallah", callback_data="ncert_wallah")],
            [InlineKeyboardButton("📚 UPSC Wallah", callback_data="upsc_wallah")],
            [InlineKeyboardButton("📄 Other Books", callback_data="other_books")]
        ]
        
        if is_admin:
            keyboard.append([InlineKeyboardButton("🛠️ Manage Books", callback_data="manage_books")])
            keyboard.append([InlineKeyboardButton("➕ Add Book", callback_data="add_other_book")])
        
        keyboard.append([InlineKeyboardButton("↩️ Back", callback_data="main_menu")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def ncert_wallah_menu(books: List[Tuple[int, str]], is_admin: bool = False) -> InlineKeyboardMarkup:
        """NCERT Wallah books menu."""
        keyboard = []
        
        for book_id, book_name in books:
            keyboard.append([InlineKeyboardButton(book_name, callback_data=f"ncert_book_{book_id}")])
        
        if is_admin:
            keyboard.append([InlineKeyboardButton("➕ Add NCERT Book", callback_data="add_ncert_book")])
        
        keyboard.append([InlineKeyboardButton("↩️ Back to Books", callback_data="books")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def upsc_wallah_menu(books: List[Tuple[int, str]], is_admin: bool = False) -> InlineKeyboardMarkup:
        """UPSC Wallah books menu."""
        keyboard = []
        
        for book_id, book_name in books:
            keyboard.append([InlineKeyboardButton(book_name, callback_data=f"upsc_book_{book_id}")])
        
        if is_admin:
            keyboard.append([InlineKeyboardButton("➕ Add UPSC Book", callback_data="add_upsc_book")])
        
        keyboard.append([InlineKeyboardButton("↩️ Back to Books", callback_data="books")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def book_view(book_type: str) -> InlineKeyboardMarkup:
        """Book view with back navigation."""
        if book_type == "ncert":
            back_data = "ncert_wallah"
            back_label = "NCERT"
        elif book_type == "upsc":
            back_data = "upsc_wallah"
            back_label = "UPSC"
        else:
            back_data = "other_books"
            back_label = "Other Books"
            
        keyboard = [
            [InlineKeyboardButton(f"↩️ Back to {back_label}", callback_data=back_data)],
            [InlineKeyboardButton("📂 Menu", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def other_books_menu(books: List[Tuple[int, str]], is_admin: bool = False) -> InlineKeyboardMarkup:
        """Other books menu."""
        keyboard = []
        
        for book_id, book_name in books:
            keyboard.append([InlineKeyboardButton(book_name, callback_data=f"other_book_{book_id}")])
        
        if is_admin:
            keyboard.append([InlineKeyboardButton("➕ Add Other Book", callback_data="add_other_book")])
        
        keyboard.append([InlineKeyboardButton("↩️ Back to Books", callback_data="books")])
        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def manage_books_menu() -> InlineKeyboardMarkup:
        """Manage books admin menu."""
        keyboard = [
            [InlineKeyboardButton("📖 Manage NCERT Books", callback_data="manage_ncert_books")],
            [InlineKeyboardButton("📚 Manage UPSC Books", callback_data="manage_upsc_books")],
            [InlineKeyboardButton("📄 Manage Other Books", callback_data="manage_other_books")],
            [InlineKeyboardButton("➕ Add NCERT Book", callback_data="add_ncert_book"),
             InlineKeyboardButton("➕ Add UPSC Book", callback_data="add_upsc_book")],
            [InlineKeyboardButton("➕ Add Other Book", callback_data="add_other_book")],
            [InlineKeyboardButton("↩️ Back", callback_data="admin_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def manage_book_list(books: List[Tuple[int, str]], book_type: str) -> InlineKeyboardMarkup:
        """Manage individual books."""
        keyboard = []
        
        for book_id, book_name in books:
            keyboard.append([
                InlineKeyboardButton(f"🗑️ Delete {book_name}", callback_data=f"delete_{book_type}_book_{book_id}"),
                InlineKeyboardButton(f"📝 Edit", callback_data=f"edit_{book_type}_book_{book_id}")
            ])
        
        # Add "Add New Book" button
        book_label = "NCERT" if book_type == "ncert" else "UPSC"
        keyboard.append([InlineKeyboardButton(f"➕ Add New {book_label} Book", callback_data=f"add_{book_type}_book")])
        keyboard.append([InlineKeyboardButton("↩️ Back", callback_data="manage_books")])
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def confirmation(action: str, item_id: int) -> InlineKeyboardMarkup:
        """Confirmation keyboard for destructive actions."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{action}_{item_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data="admin_settings")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def database_tools_menu() -> InlineKeyboardMarkup:
        """Database tools and management."""
        keyboard = [
            [InlineKeyboardButton("💾 Create Backup", callback_data="backup_database")],
            [InlineKeyboardButton("⚡ Optimize Database", callback_data="optimize_database")],
            [InlineKeyboardButton("🗑️ Reset Database", callback_data="reset_database")],
            [InlineKeyboardButton("↩️ Back", callback_data="admin_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def bot_settings_menu() -> InlineKeyboardMarkup:
        """Bot configuration settings."""
        keyboard = [
            [InlineKeyboardButton("💬 Change Welcome Message", callback_data="change_welcome_message")],
            [InlineKeyboardButton("🤖 View Bot Info", callback_data="view_bot_info")],
            [InlineKeyboardButton("📊 Performance Stats", callback_data="user_analytics")],
            [InlineKeyboardButton("↩️ Back", callback_data="admin_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def dangerous_confirmation(action: str) -> InlineKeyboardMarkup:
        """Dangerous action confirmation with extra warning."""
        keyboard = [
            [InlineKeyboardButton("⚠️ YES, DELETE EVERYTHING", callback_data=f"confirm_{action}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="database_tools")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def quick_actions_menu() -> InlineKeyboardMarkup:
        """Quick actions for common admin tasks."""
        keyboard = [
            [InlineKeyboardButton("➕ Add Subject", callback_data="add_subject"),
             InlineKeyboardButton("➕ Add NCERT Book", callback_data="add_ncert_book")],
            [InlineKeyboardButton("➕ Add UPSC Book", callback_data="add_upsc_book"),
             InlineKeyboardButton("📊 Quick Stats", callback_data="quick_stats")],
            [InlineKeyboardButton("🔍 Search Content", callback_data="search_content"),
             InlineKeyboardButton("🎯 Recent Activity", callback_data="recent_activity")],
            [InlineKeyboardButton("↩️ Back", callback_data="admin_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def import_export_menu() -> InlineKeyboardMarkup:
        """Import/Export data management."""
        keyboard = [
            [InlineKeyboardButton("📤 Export Database", callback_data="export_database"),
             InlineKeyboardButton("📥 Import Data", callback_data="import_data")],
            [InlineKeyboardButton("💾 Create Full Backup", callback_data="backup_database"),
             InlineKeyboardButton("🔄 Restore Backup", callback_data="restore_backup")],
            [InlineKeyboardButton("📋 Export JSON", callback_data="export_json"),
             InlineKeyboardButton("📁 Import JSON", callback_data="import_json")],
            [InlineKeyboardButton("↩️ Back", callback_data="admin_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def content_type_selection() -> InlineKeyboardMarkup:
        """Select content type for bulk operations."""
        keyboard = [
            [InlineKeyboardButton("📚 Subjects", callback_data="bulk_subjects"),
             InlineKeyboardButton("📖 Lectures", callback_data="bulk_lectures")],
            [InlineKeyboardButton("📘 NCERT Books", callback_data="bulk_ncert"),
             InlineKeyboardButton("📗 UPSC Books", callback_data="bulk_upsc")],
            [InlineKeyboardButton("↩️ Back", callback_data="admin_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def manage_lectures_menu() -> InlineKeyboardMarkup:
        """Enhanced lecture management menu."""
        keyboard = [
            [InlineKeyboardButton("📚 Manage by Subject", callback_data="manage_lectures"),
             InlineKeyboardButton("📝 Add New Lecture", callback_data="add_lecture_select_subject")],
            [InlineKeyboardButton("🔍 Search Lectures", callback_data="search_lectures"),
             InlineKeyboardButton("📊 Lecture Statistics", callback_data="lecture_stats")],
            [InlineKeyboardButton("↩️ Back", callback_data="admin_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def enhanced_admin_menu() -> InlineKeyboardMarkup:
        """Enhanced admin menu with all features."""
        keyboard = [
            [InlineKeyboardButton("📚 Subjects", callback_data="manage_subjects"),
             InlineKeyboardButton("📖 Lectures", callback_data="manage_lectures_enhanced")],
            [InlineKeyboardButton("📘 Books", callback_data="manage_books"),
             InlineKeyboardButton("🔧 Quick Add", callback_data="quick_actions")],
            [InlineKeyboardButton("🗄️ Database", callback_data="database_tools"),
             InlineKeyboardButton("⚙️ Settings", callback_data="bot_settings")],
            [InlineKeyboardButton("📈 Analytics", callback_data="user_analytics"),
             InlineKeyboardButton("📤 Import/Export", callback_data="import_export")],
            [InlineKeyboardButton("↩️ Back to Menu", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def admin_with_add_buttons() -> InlineKeyboardMarkup:
        """Admin menu with prominent add buttons for each section."""
        keyboard = [
            [InlineKeyboardButton("➕ Add Subject", callback_data="add_subject"),
             InlineKeyboardButton("➕ Add NCERT Book", callback_data="add_ncert_book")],
            [InlineKeyboardButton("➕ Add UPSC Book", callback_data="add_upsc_book"),
             InlineKeyboardButton("📚 Manage All", callback_data="admin_settings")],
            [InlineKeyboardButton("🔧 Quick Actions", callback_data="quick_actions"),
             InlineKeyboardButton("📊 View Stats", callback_data="user_analytics")],
            [InlineKeyboardButton("↩️ Back to Menu", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

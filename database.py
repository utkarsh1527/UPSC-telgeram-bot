
"""
Database manager for UPSC Vault Bot
Handles all SQLite operations for subjects and lectures.
"""

import sqlite3
import logging
import threading
from typing import List, Optional, Tuple
from contextlib import contextmanager
from config import DATABASE_PATH, DEFAULT_SUBJECTS

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages all database operations for the bot."""
    
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._local = threading.local()
        self._lock = threading.Lock()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.conn.execute("PRAGMA foreign_keys = ON")
            self._local.conn.execute("PRAGMA journal_mode = WAL")
            self._local.conn.execute("PRAGMA synchronous = NORMAL")
            self._local.conn.execute("PRAGMA cache_size = 1000")
        return self._local.conn
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with proper error handling."""
        conn = None
        try:
            conn = self._get_connection()
            yield conn
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                logger.warning("Database locked, retrying...")
                # Reset connection and retry once
                self._close_connection()
                conn = self._get_connection()
                yield conn
            else:
                raise
        except Exception as e:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                try:
                    conn.commit()
                except Exception as e:
                    logger.error(f"Error committing transaction: {e}")
                    conn.rollback()
    
    def _close_connection(self):
        """Close thread-local connection."""
        if hasattr(self._local, 'conn') and self._local.conn:
            try:
                self._local.conn.close()
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
            finally:
                self._local.conn = None
    
    def init_database(self) -> None:
        """Initialize database with required tables."""
        try:
            with self.get_connection() as conn:
                # Create subjects table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS subjects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create lectures table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS lectures (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        subject_id INTEGER NOT NULL,
                        lecture_no TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
                    )
                """)
                
                # Create books table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS books (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL CHECK (type IN ('ncert', 'upsc', 'other')),
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_lectures_subject_id ON lectures(subject_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_books_type ON books(type)")
                
                # Insert default subjects if database is empty
                cursor = conn.execute("SELECT COUNT(*) FROM subjects")
                if cursor.fetchone()[0] == 0:
                    for subject in DEFAULT_SUBJECTS:
                        try:
                            conn.execute("INSERT INTO subjects (name) VALUES (?)", (subject,))
                        except sqlite3.IntegrityError:
                            pass  # Subject already exists
                
                logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def add_subject(self, name: str) -> bool:
        """Add a new subject."""
        if not name or not name.strip():
            return False
        
        try:
            with self.get_connection() as conn:
                conn.execute("INSERT INTO subjects (name) VALUES (?)", (name.strip(),))
                logger.info(f"Added subject: {name}")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Subject already exists: {name}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Error adding subject: {e}")
            return False
    
    def get_subjects(self) -> List[Tuple[int, str]]:
        """Get all subjects ordered by name."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT id, name FROM subjects ORDER BY name")
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching subjects: {e}")
            return []
    
    def delete_subject(self, subject_id: int) -> bool:
        """Delete a subject and its lectures."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
                if cursor.rowcount > 0:
                    logger.info(f"Deleted subject with ID: {subject_id}")
                    return True
                return False
        except sqlite3.Error as e:
            logger.error(f"Error deleting subject: {e}")
            return False
    
    def rename_subject(self, subject_id: int, new_name: str) -> bool:
        """Rename a subject."""
        if not new_name or not new_name.strip():
            return False
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "UPDATE subjects SET name = ? WHERE id = ?", 
                    (new_name.strip(), subject_id)
                )
                if cursor.rowcount > 0:
                    logger.info(f"Renamed subject ID {subject_id} to: {new_name}")
                    return True
                return False
        except sqlite3.IntegrityError:
            logger.warning(f"Subject name already exists: {new_name}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Error renaming subject: {e}")
            return False
    
    def add_lecture(self, subject_id: int, lecture_no: str, content: str) -> bool:
        """Add a lecture to a subject."""
        if not lecture_no or not lecture_no.strip() or not content or not content.strip():
            return False
        
        try:
            with self.get_connection() as conn:
                # Check if subject exists
                cursor = conn.execute("SELECT 1 FROM subjects WHERE id = ?", (subject_id,))
                if not cursor.fetchone():
                    logger.warning(f"Subject with ID {subject_id} does not exist")
                    return False
                
                conn.execute(
                    "INSERT INTO lectures (subject_id, lecture_no, content) VALUES (?, ?, ?)",
                    (subject_id, lecture_no.strip(), content.strip())
                )
                logger.info(f"Added lecture {lecture_no} to subject ID {subject_id}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error adding lecture: {e}")
            return False
    
    def get_lectures(self, subject_id: int) -> List[Tuple[int, str, str]]:
        """Get all lectures for a subject ordered by lecture number."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, lecture_no, content FROM lectures WHERE subject_id = ? ORDER BY lecture_no",
                    (subject_id,)
                )
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching lectures: {e}")
            return []
    
    def get_lecture(self, lecture_id: int) -> Optional[Tuple[int, int, str, str]]:
        """Get a specific lecture."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, subject_id, lecture_no, content FROM lectures WHERE id = ?",
                    (lecture_id,)
                )
                return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Error fetching lecture: {e}")
            return None
    
    def update_lecture(self, lecture_id: int, content: str) -> bool:
        """Update lecture content."""
        if not content or not content.strip():
            return False
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "UPDATE lectures SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (content.strip(), lecture_id)
                )
                if cursor.rowcount > 0:
                    logger.info(f"Updated lecture ID: {lecture_id}")
                    return True
                return False
        except sqlite3.Error as e:
            logger.error(f"Error updating lecture: {e}")
            return False
    
    def delete_lecture(self, lecture_id: int) -> bool:
        """Delete a lecture."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("DELETE FROM lectures WHERE id = ?", (lecture_id,))
                if cursor.rowcount > 0:
                    logger.info(f"Deleted lecture ID: {lecture_id}")
                    return True
                return False
        except sqlite3.Error as e:
            logger.error(f"Error deleting lecture: {e}")
            return False
    
    def get_subject_name(self, subject_id: int) -> Optional[str]:
        """Get subject name by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT name FROM subjects WHERE id = ?", (subject_id,))
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error as e:
            logger.error(f"Error fetching subject name: {e}")
            return None
    
    def add_book(self, name: str, book_type: str, content: str) -> bool:
        """Add a new book."""
        if not name or not name.strip() or not content or not content.strip():
            return False
        
        if book_type not in ['ncert', 'upsc', 'other']:
            logger.error(f"Invalid book type: {book_type}")
            return False
        
        try:
            with self.get_connection() as conn:
                conn.execute(
                    "INSERT INTO books (name, type, content) VALUES (?, ?, ?)", 
                    (name.strip(), book_type, content.strip())
                )
                logger.info(f"Added {book_type} book: {name}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error adding book: {e}")
            return False
    
    def get_books(self, book_type: str) -> List[Tuple[int, str]]:
        """Get all books of a specific type."""
        if book_type not in ['ncert', 'upsc', 'other']:
            logger.error(f"Invalid book type: {book_type}")
            return []
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, name FROM books WHERE type = ? ORDER BY name", 
                    (book_type,)
                )
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error fetching books: {e}")
            return []
    
    def get_book(self, book_id: int) -> Optional[Tuple[int, str, str, str]]:
        """Get a specific book."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, name, type, content FROM books WHERE id = ?", 
                    (book_id,)
                )
                return cursor.fetchone()
        except sqlite3.Error as e:
            logger.error(f"Error fetching book: {e}")
            return None
    
    def update_book(self, book_id: int, content: str) -> bool:
        """Update book content."""
        if not content or not content.strip():
            return False
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "UPDATE books SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                    (content.strip(), book_id)
                )
                if cursor.rowcount > 0:
                    logger.info(f"Updated book ID: {book_id}")
                    return True
                return False
        except sqlite3.Error as e:
            logger.error(f"Error updating book: {e}")
            return False
    
    def delete_book(self, book_id: int) -> bool:
        """Delete a book."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
                if cursor.rowcount > 0:
                    logger.info(f"Deleted book ID: {book_id}")
                    return True
                return False
        except sqlite3.Error as e:
            logger.error(f"Error deleting book: {e}")
            return False
    
    def export_database(self) -> str:
        """Export all database data as formatted text."""
        try:
            with self.get_connection() as conn:
                result = "📊 UPSC Vault Database Export\n"
                result += "=" * 30 + "\n\n"
                
                # Get all subjects and their lectures
                subjects = self.get_subjects()
                total_lectures = 0
                
                for subject_id, subject_name in subjects:
                    result += f"📚 {subject_name}\n"
                    lectures = self.get_lectures(subject_id)
                    if lectures:
                        for lecture_id, lecture_no, content in lectures:
                            result += f"  ▶️ {lecture_no}\n"
                            total_lectures += 1
                    else:
                        result += "  (No lectures)\n"
                    result += "\n"
                
                # Get all books
                ncert_books = self.get_books("ncert")
                upsc_books = self.get_books("upsc")
                other_books = self.get_books("other")
                
                if ncert_books or upsc_books or other_books:
                    result += "📖 BOOKS\n"
                    result += "-" * 20 + "\n"
                    
                    if ncert_books:
                        result += "📖 NCERT Wallah:\n"
                        for book_id, book_name in ncert_books:
                            result += f"  📄 {book_name}\n"
                    
                    if upsc_books:
                        result += "📚 UPSC Wallah:\n"
                        for book_id, book_name in upsc_books:
                            result += f"  📄 {book_name}\n"
                    
                    if other_books:
                        result += "📄 Other Books:\n"
                        for book_id, book_name in other_books:
                            result += f"  📄 {book_name}\n"
                
                # Add summary
                result += f"\n📊 SUMMARY\n"
                result += f"• {len(subjects)} subjects\n"
                result += f"• {total_lectures} lectures\n"
                result += f"• {len(ncert_books) + len(upsc_books) + len(other_books)} books\n"
                
                return result
        except Exception as e:
            logger.error(f"Error exporting database: {e}")
            return "❌ Error exporting database"
    
    def export_database_json(self) -> dict:
        """Export all database data as JSON for bulk operations."""
        try:
            with self.get_connection() as conn:
                export_data = {
                    "subjects": [],
                    "lectures": [],
                    "books": [],
                    "export_timestamp": None
                }
                
                # Add timestamp
                cursor = conn.execute("SELECT datetime('now')")
                export_data["export_timestamp"] = cursor.fetchone()[0]
                
                # Export subjects
                subjects = self.get_subjects()
                for subject_id, subject_name in subjects:
                    export_data["subjects"].append({
                        "id": subject_id,
                        "name": subject_name
                    })
                    
                    # Export lectures for this subject
                    lectures = self.get_lectures(subject_id)
                    for lecture_id, lecture_no, content in lectures:
                        export_data["lectures"].append({
                            "id": lecture_id,
                            "subject_id": subject_id,
                            "subject_name": subject_name,
                            "lecture_no": lecture_no,
                            "content": content
                        })
                
                # Export books
                for book_type in ["ncert", "upsc", "other"]:
                    books = self.get_books(book_type)
                    for book_id, book_name in books:
                        book_data = self.get_book(book_id)
                        if book_data:
                            export_data["books"].append({
                                "id": book_id,
                                "name": book_name,
                                "type": book_type,
                                "content": book_data[3]
                            })
                
                return export_data
        except Exception as e:
            logger.error(f"Error exporting JSON: {e}")
            return {"error": str(e)}
    
    def import_database_json(self, import_data: dict) -> dict:
        """Import data from JSON format."""
        result = {
            "subjects_imported": 0,
            "lectures_imported": 0,
            "books_imported": 0,
            "errors": []
        }
        
        if not isinstance(import_data, dict):
            return {"error": "Invalid data format. Expected JSON object."}
        
        try:
            with self.get_connection() as conn:
                # Import subjects
                if "subjects" in import_data and isinstance(import_data["subjects"], list):
                    for subject in import_data["subjects"]:
                        if isinstance(subject, dict) and "name" in subject:
                            if self.add_subject(subject["name"]):
                                result["subjects_imported"] += 1
                            else:
                                result["errors"].append(f"Subject '{subject['name']}' already exists or failed to import")
                
                # Import lectures
                if "lectures" in import_data and isinstance(import_data["lectures"], list):
                    for lecture in import_data["lectures"]:
                        if isinstance(lecture, dict) and all(key in lecture for key in ["subject_name", "lecture_no", "content"]):
                            # Find subject by name
                            subjects = self.get_subjects()
                            subject_id = None
                            for s_id, s_name in subjects:
                                if s_name == lecture["subject_name"]:
                                    subject_id = s_id
                                    break
                            
                            if subject_id:
                                if self.add_lecture(subject_id, lecture["lecture_no"], lecture["content"]):
                                    result["lectures_imported"] += 1
                                else:
                                    result["errors"].append(f"Failed to import lecture '{lecture['lecture_no']}'")
                            else:
                                result["errors"].append(f"Subject '{lecture['subject_name']}' not found for lecture '{lecture['lecture_no']}'")
                
                # Import books
                if "books" in import_data and isinstance(import_data["books"], list):
                    for book in import_data["books"]:
                        if isinstance(book, dict) and all(key in book for key in ["name", "type", "content"]):
                            if self.add_book(book["name"], book["type"], book["content"]):
                                result["books_imported"] += 1
                            else:
                                result["errors"].append(f"Failed to import book '{book['name']}'")
                
                return result
        except Exception as e:
            logger.error(f"Error importing JSON: {e}")
            return {"error": str(e)}
    
    def get_database_stats(self) -> dict:
        """Get database statistics."""
        try:
            with self.get_connection() as conn:
                stats = {}
                
                # Count subjects
                cursor = conn.execute("SELECT COUNT(*) FROM subjects")
                stats["subjects_count"] = cursor.fetchone()[0]
                
                # Count lectures
                cursor = conn.execute("SELECT COUNT(*) FROM lectures")
                stats["lectures_count"] = cursor.fetchone()[0]
                
                # Count books by type
                cursor = conn.execute("SELECT type, COUNT(*) FROM books GROUP BY type")
                book_counts = dict(cursor.fetchall())
                stats["ncert_books_count"] = book_counts.get("ncert", 0)
                stats["upsc_books_count"] = book_counts.get("upsc", 0)
                stats["other_books_count"] = book_counts.get("other", 0)
                stats["total_books_count"] = sum(book_counts.values())
                
                # Database size
                cursor = conn.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                stats["database_size_bytes"] = cursor.fetchone()[0]
                
                return stats
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 90) -> dict:
        """Clean up old temporary data (if any cleanup is needed)."""
        # This method can be extended for future cleanup needs
        # For now, it's a placeholder for potential future features
        return {"message": "No cleanup needed for current schema"}
    
    def vacuum_database(self) -> bool:
        """Vacuum the database to reclaim space and optimize performance."""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                logger.info("Database vacuumed successfully")
                return True
        except Exception as e:
            logger.error(f"Error vacuuming database: {e}")
            return False
    
    def reset_database(self) -> bool:
        """Reset the entire database and restore defaults."""
        try:
            with self.get_connection() as conn:
                # Drop all tables
                conn.execute("DROP TABLE IF EXISTS lectures")
                conn.execute("DROP TABLE IF EXISTS books")
                conn.execute("DROP TABLE IF EXISTS subjects")
                
                # Recreate with init
                self.init_database()
                
                logger.info("Database reset successfully")
                return True
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            return False
    
    def get_content_statistics(self) -> dict:
        """Get detailed content statistics."""
        try:
            with self.get_connection() as conn:
                stats = {}
                
                # Subject statistics
                cursor = conn.execute("SELECT COUNT(*) FROM subjects")
                stats["total_subjects"] = cursor.fetchone()[0]
                
                # Lecture statistics
                cursor = conn.execute("SELECT COUNT(*) FROM lectures")
                stats["total_lectures"] = cursor.fetchone()[0]
                
                # Most lectures per subject
                cursor = conn.execute("""
                    SELECT s.name, COUNT(l.id) as lecture_count 
                    FROM subjects s 
                    LEFT JOIN lectures l ON s.id = l.subject_id 
                    GROUP BY s.id, s.name 
                    ORDER BY lecture_count DESC 
                    LIMIT 1
                """)
                result = cursor.fetchone()
                if result:
                    stats["most_lectures_subject"] = result[0]
                    stats["most_lectures_count"] = result[1]
                
                # Book statistics by type
                cursor = conn.execute("SELECT type, COUNT(*) FROM books GROUP BY type")
                book_stats = dict(cursor.fetchall())
                stats["ncert_books"] = book_stats.get("ncert", 0)
                stats["upsc_books"] = book_stats.get("upsc", 0)
                
                # Recent activity (subjects created in last 7 days if timestamps exist)
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM subjects 
                    WHERE created_at > datetime('now', '-7 days')
                """)
                stats["recent_subjects"] = cursor.fetchone()[0]
                
                return stats
        except Exception as e:
            logger.error(f"Error getting content statistics: {e}")
            return {}
    
    def search_content(self, query: str) -> List[Tuple[str, int, str, str]]:
        """Search for content across subjects, lectures, and books."""
        if not query or not query.strip():
            return []
        
        search_term = f"%{query.strip().lower()}%"
        results = []
        
        try:
            with self.get_connection() as conn:
                # Search in subjects
                cursor = conn.execute(
                    "SELECT 'subject', id, name, name FROM subjects WHERE LOWER(name) LIKE ?",
                    (search_term,)
                )
                for row in cursor.fetchall():
                    results.append((row[0], row[1], row[2], row[3][:100] + "..." if len(row[3]) > 100 else row[3]))
                
                # Search in lectures
                cursor = conn.execute("""
                    SELECT 'lecture', l.id, l.lecture_no, l.content 
                    FROM lectures l 
                    WHERE LOWER(l.lecture_no) LIKE ? OR LOWER(l.content) LIKE ?
                """, (search_term, search_term))
                for row in cursor.fetchall():
                    results.append((row[0], row[1], row[2], row[3][:100] + "..." if len(row[3]) > 100 else row[3]))
                
                # Search in books
                cursor = conn.execute(
                    "SELECT 'book', id, name, content FROM books WHERE LOWER(name) LIKE ? OR LOWER(content) LIKE ?",
                    (search_term, search_term)
                )
                for row in cursor.fetchall():
                    results.append((row[0], row[1], row[2], row[3][:100] + "..." if len(row[3]) > 100 else row[3]))
                
                return results
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            return []
    
    def search_lectures(self, query: str) -> List[Tuple[int, str, str]]:
        """Search for lectures specifically."""
        if not query or not query.strip():
            return []
        
        search_term = f"%{query.strip().lower()}%"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT l.id, s.name, l.lecture_no 
                    FROM lectures l 
                    JOIN subjects s ON l.subject_id = s.id 
                    WHERE LOWER(l.lecture_no) LIKE ? OR LOWER(l.content) LIKE ?
                    ORDER BY s.name, l.lecture_no
                """, (search_term, search_term))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error searching lectures: {e}")
            return []
    
    def get_subject_id(self, subject_name: str) -> Optional[int]:
        """Get subject ID by name."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting subject ID: {e}")
            return None

    def __del__(self):
        """Cleanup connections on destruction."""
        try:
            self._close_connection()
        except:
            pass

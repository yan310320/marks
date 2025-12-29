"""Backend utilities for marks project."""

import os
from dotenv import load_dotenv
import sqlite3 as sql
import uuid
import random as rnd
from datetime import datetime, date
from typing import List, Optional

try:
    import telebot as tb
    from telebot import types
except ImportError:
    tb = None
    types = None


# Load environment variables from .env file if present
load_dotenv()

# Filenames definitions
DBASE = "db.db"
LOGFILE = "logs.txt"

def log(text: str):
    try:
        with open(LOGFILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {text}\n")
    except Exception as e:
        print("Error writing logs: ", e)

# Bot init (read token from environment for safety)
_TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if tb is not None and _TELEGRAM_TOKEN:
    bot = tb.TeleBot(token=_TELEGRAM_TOKEN)
else:
    bot = None

def init_database():
    """Initialize database tables if they don't exist."""
    conn = sql.connect(DBASE)
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            name TEXT
        )
    ''')

    # Subjects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            FOREIGN KEY (user_id) REFERENCES users (telegram_id)
        )
    ''')

    # Schedule table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            weekday INTEGER,
            lesson_number INTEGER,
            subject_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (telegram_id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id)
        )
    ''')

    # Terms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            start_date DATE,
            end_date DATE,
            FOREIGN KEY (user_id) REFERENCES users (telegram_id)
        )
    ''')

    # Grades table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject_id INTEGER,
            value INTEGER,
            grade_type TEXT,
            date DATE,
            term_id INTEGER,
            confirmed INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (telegram_id),
            FOREIGN KEY (subject_id) REFERENCES subjects (id),
            FOREIGN KEY (term_id) REFERENCES terms (id)
        )
    ''')

    conn.commit()
    conn.close()

# Initialize database on import
init_database()

# CONFIRMATION CODE SENDING FUNC BEGIN
def send_code(chat_id: Optional[int]):
    if chat_id is None:
        log("Chat ID cannot be None.")
        return None
    code = rnd.randint(100000, 999999)
    text = f"Your confirmation code for #ThDev Marks is {code}."
    if bot:
        bot.send_message(chat_id=chat_id, text=text)
    else:
        log(f"[send_code] Would send to {chat_id}: {text}")
    return code
# CONFIRMATION CODE SENDING FUNC END

class User(object):
    def __init__(self, tg_id: Optional[int], name: str = "", id_: str = ""):

        self.id_ = id_ or str(uuid.uuid4())  # Ensure id_ is generated if None
        self.tgID = tg_id
        self.name = name

    def sign_up(self):
        if not self.id_:
            self.id_ = str(uuid.uuid4())
        conn = sql.connect(DBASE)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (id, telegram_id, name) VALUES (?, ?, ?);",
                (self.id_, self.tgID, self.name)
            )
            conn.commit()
            log(f"User {self.name} ({self.tgID}) signed up")
        except sql.IntegrityError:
            log(f"User {self.tgID} already exists")
        finally:
            conn.close()

    @staticmethod
    def get_user_by_telegram_id(tg_id: int) -> Optional['User']:
        conn = sql.connect(DBASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, telegram_id, name FROM users WHERE telegram_id = ?", (tg_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(tg_id=row[1], name=row[2], id_=row[0])
        return None

class Subject:
    def __init__(self, id_: Optional[int] = None, user_id: Optional[int] = None, name: str = ""):
        self.id = id_
        self.user_id = user_id
        self.name = name

    def save(self):
        if self.user_id is None:
            log("User ID cannot be None when saving a subject.")
            return
        conn = sql.connect(DBASE)
        cursor = conn.cursor()
        if self.id:
            cursor.execute(
                "UPDATE subjects SET name = ? WHERE id = ? AND user_id = ?",
                (self.name, self.id, self.user_id)
            )
        else:
            cursor.execute(
                "INSERT INTO subjects (user_id, name) VALUES (?, ?)",
                (self.user_id, self.name)
            )
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    @staticmethod
    def get_subjects_by_user(user_id: int) -> List['Subject']:
        conn = sql.connect(DBASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, name FROM subjects WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [Subject(id_=row[0], user_id=row[1], name=row[2]) for row in rows]

    
    @staticmethod
    def get_subject_by_id(subject_id: int, user_id: int) -> Optional['Subject']:
        conn = sql.connect(DBASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, name FROM subjects WHERE id = ? AND user_id = ?", (subject_id, user_id))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Subject(id_=row[0], user_id=row[1], name=row[2])
        return None

class Grade:
    def __init__(self, id_: Optional[int] = None, user_id: Optional[int] = None, subject_id: Optional[int] = None,
                 value: Optional[int] = None, grade_type: str = "", date_: Optional[date] = None,
                 term_id: Optional[int] = None, confirmed: bool = False):
        self.id = id_
        self.user_id = user_id
        self.subject_id = subject_id
        self.value = value
        self.grade_type = grade_type
        self.date = date_
        self.term_id = term_id
        self.confirmed = confirmed

    def save(self):
        conn = sql.connect(DBASE)
        cursor = conn.cursor()
        if self.id:
            cursor.execute("""
                UPDATE grades SET subject_id = ?, value = ?, grade_type = ?,
                date = ?, term_id = ?, confirmed = ? WHERE id = ? AND user_id = ?
            """, (self.subject_id, self.value, self.grade_type, self.date,
                  self.term_id, self.confirmed, self.id, self.user_id))
        else:
            cursor.execute("""
                INSERT INTO grades (user_id, subject_id, value, grade_type, date, term_id, confirmed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.user_id, self.subject_id, self.value, self.grade_type,
                  self.date, self.term_id, self.confirmed))
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    @staticmethod
    def get_grades_by_user(user_id: int, subject_id: Optional[int] = None, term_id: Optional[int] = None) -> List['Grade']:
        conn = sql.connect(DBASE)
        cursor = conn.cursor()
        query = "SELECT id, user_id, subject_id, value, grade_type, date, term_id, confirmed FROM grades WHERE user_id = ?"
        params = [user_id]

        if subject_id:
            query += " AND subject_id = ?"
            params.append(subject_id)
        if term_id:
            query += " AND term_id = ?"
            params.append(term_id)

        query += " ORDER BY date DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [Grade(id_=row[0], user_id=row[1], subject_id=row[2], value=row[3],
                     grade_type=row[4], date_=row[5], term_id=row[6], confirmed=row[7]) for row in rows]

class Term:
    def __init__(self, id_: Optional[int] = None, user_id: Optional[int] = None, name: str = "",
                 start_date: Optional[date] = None, end_date: Optional[date] = None):
        self.id = id_
        self.user_id = user_id
        self.name = name
        self.start_date = start_date
        self.end_date = end_date

    def save(self):
        conn = sql.connect(DBASE)
        cursor = conn.cursor()
        if self.id:
            cursor.execute(
                "UPDATE terms SET name = ?, start_date = ?, end_date = ? WHERE id = ? AND user_id = ?",
                (self.name, self.start_date, self.end_date, self.id, self.user_id)
            )
        else:
            cursor.execute(
                "INSERT INTO terms (user_id, name, start_date, end_date) VALUES (?, ?, ?, ?)",
                (self.user_id, self.name, self.start_date, self.end_date)
            )
            self.id = cursor.lastrowid
        conn.commit()
        conn.close()

    @staticmethod
    def get_terms_by_user(user_id: int) -> List['Term']:
        conn = sql.connect(DBASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, name, start_date, end_date FROM terms WHERE user_id = ? ORDER BY start_date DESC", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [Term(id_=row[0], user_id=row[1], name=row[2], start_date=row[3], end_date=row[4]) for row in rows]

    @staticmethod
    def get_current_term(user_id: int) -> Optional['Term']:
        today = date.today()
        conn = sql.connect(DBASE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, name, start_date, end_date FROM terms WHERE user_id = ? AND start_date <= ? AND end_date >= ?",
            (user_id, today, today)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return Term(id_=row[0], user_id=row[1], name=row[2], start_date=row[3], end_date=row[4])
        return None


# Bot handlers
from typing import Dict, Any
user_states: Dict[int, Dict[str, Any]] = {}  # Store user states for conversation flow

if bot:

    from telebot.types import Message, CallbackQuery

    # type: ignore is used to suppress type checker errors for dynamic decorators
    @bot.message_handler(commands=['start'])  # type: ignore[attr-defined]
    def handle_start(message: Message) -> None:
        if not hasattr(message, 'chat') or not hasattr(message.chat, 'id'):
            return
        user = User.get_user_by_telegram_id(message.chat.id)
        first_name = getattr(getattr(message, 'from_user', None), 'first_name', None)
        if not user:
            user = User(tg_id=message.chat.id, name=first_name or "Unknown")
            user.sign_up()
            if bot:
                bot.reply_to(message, f"Welcome to Marks E-Daybook, {user.name}!\n\nUse /help to see available commands.")
        else:
            if bot:
                bot.reply_to(message, f"Welcome back, {user.name}!\n\nUse /help to see available commands.")

    @bot.message_handler(commands=['help'])  # type: ignore[attr-defined]
    def handle_help(message: Message) -> None:
        help_text = """<b>📚 Marks E-Daybook Commands:</b>

<b>📝 Subject Management:</b>
/add_subject - Add a new subject
/list_subjects - List all your subjects

<b>📊 Grade Management:</b>
/add_grade - Add a new grade
/view_grades - View your grades
/average - Calculate average grades

<b>📅 Terms:</b>
/add_term - Add a new academic term
/list_terms - List all terms

<b>❓ Other:</b>
/help - Show this help message
/cancel - Cancel current operation
"""
        if bot and hasattr(message, 'chat') and hasattr(message.chat, 'id'):
            bot.send_message(message.chat.id, help_text, parse_mode='HTML')

    @bot.message_handler(commands=['add_subject'])  # type: ignore[attr-defined]
    def handle_add_subject(message: Message) -> None:
        if not hasattr(message, 'chat') or not hasattr(message.chat, 'id'):
            return
        user_states[message.chat.id] = {'state': 'waiting_subject_name'}
        if bot:
            bot.reply_to(message, "Please enter the name of the subject:")

    @bot.message_handler(commands=['list_subjects'])  # type: ignore[attr-defined]
    def handle_list_subjects(message: Message) -> None:
        if not hasattr(message, 'chat') or not hasattr(message.chat, 'id'):
            return
        subjects = Subject.get_subjects_by_user(message.chat.id)
        if not subjects:
            if bot:
                bot.reply_to(message, "You don't have any subjects yet. Use /add_subject to add one.")
            return

        text = "📚 Your Subjects:\n\n"
        for i, subject in enumerate(subjects, 1):
            text += f"{i}. {subject.name}\n"
        if bot:
            bot.send_message(message.chat.id, text)

    @bot.message_handler(commands=['add_term'])  # type: ignore[attr-defined]
    def handle_add_term(message: Message) -> None:
        if not hasattr(message, 'chat') or not hasattr(message.chat, 'id'):
            return
        user_states[message.chat.id] = {'state': 'waiting_term_name'}
        if bot:
            bot.reply_to(message, "Please enter the name of the term (e.g., 'Fall 2023'):")

    @bot.message_handler(commands=['list_terms'])  # type: ignore[attr-defined]
    def handle_list_terms(message: Message) -> None:
        if not hasattr(message, 'chat') or not hasattr(message.chat, 'id'):
            return
        terms = Term.get_terms_by_user(message.chat.id)
        if not terms:
            if bot:
                bot.reply_to(message, "You don't have any terms yet. Use /add_term to add one.")
            return

        text = "📅 Your Terms:\n\n"
        for term in terms:
            text += f"• {term.name}: {term.start_date} - {term.end_date}\n"
        if bot:
            bot.send_message(message.chat.id, text)

    @bot.message_handler(commands=['add_grade'])  # type: ignore[attr-defined]
    def handle_add_grade(message: Message) -> None:
        if not hasattr(message, 'chat') or not hasattr(message.chat, 'id'):
            return
        subjects = Subject.get_subjects_by_user(message.chat.id)
        if not subjects:
            if bot:
                bot.reply_to(message, "You need to add subjects first. Use /add_subject.")
            return
        if types is None:
            return
        markup = types.InlineKeyboardMarkup()
        for subject in subjects:
            markup.add(types.InlineKeyboardButton(subject.name, callback_data=f"grade_subject_{subject.id}"))
        if bot:
            bot.send_message(message.chat.id, "Select a subject for the grade:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: hasattr(call, 'data') and isinstance(call.data, str) and call.data.startswith('grade_subject_'))  # type: ignore[attr-defined]
    def handle_grade_subject_selection(call: CallbackQuery) -> None:
        if not hasattr(call, 'data') or not hasattr(call, 'message') or not hasattr(call.message, 'chat') or not hasattr(call.message.chat, 'id'):
            return
        subject_id = int(call.data.split('_')[2])
        user_states[call.message.chat.id] = {'state': 'waiting_grade_value', 'subject_id': subject_id}
        if bot:
            bot.edit_message_text("Enter the grade value (1-12):", call.message.chat.id, call.message.message_id)

    @bot.message_handler(commands=['view_grades'])  # type: ignore[attr-defined]
    def handle_view_grades(message: Message) -> None:
        if not hasattr(message, 'chat') or not hasattr(message.chat, 'id'):
            return
        subjects = Subject.get_subjects_by_user(message.chat.id)
        if not subjects:
            if bot:
                bot.reply_to(message, "You don't have any subjects yet.")
            return
        if types is None:
            return
        markup = types.InlineKeyboardMarkup()
        for subject in subjects:
            markup.add(types.InlineKeyboardButton(subject.name, callback_data=f"view_grades_{subject.id}"))
        markup.add(types.InlineKeyboardButton("All Subjects", callback_data="view_grades_all"))
        if bot:
            bot.send_message(message.chat.id, "Select a subject to view grades:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: hasattr(call, 'data') and isinstance(call.data, str) and call.data.startswith('view_grades_'))  # type: ignore[attr-defined]
    def handle_view_grades_selection(call: CallbackQuery) -> None:
        if not hasattr(call, 'data') or not hasattr(call, 'message') or not hasattr(call.message, 'chat') or not hasattr(call.message.chat, 'id'):
            return
        if call.data == 'view_grades_all':
            grades = Grade.get_grades_by_user(call.message.chat.id)
            subject_name = "All Subjects"
        else:
            subject_id = int(call.data.split('_')[2])
            grades = Grade.get_grades_by_user(call.message.chat.id, subject_id=subject_id)
            subject = Subject.get_subject_by_id(subject_id, call.message.chat.id)
            subject_name = subject.name if subject else "Unknown"

        if not grades:
            if bot:
                bot.edit_message_text(f"No grades found for {subject_name}.", call.message.chat.id, call.message.message_id)
            return

        text = f"📊 Grades for {subject_name}:\n\n"
        for grade in grades[:20]:  # Limit to 20 most recent
            if grade.subject_id is not None:
                subject = Subject.get_subject_by_id(grade.subject_id, call.message.chat.id)
                subject_name = subject.name if subject else "Unknown"
            else:
                subject_name = "Unknown"
            text += f"• {subject_name}: {grade.value} ({grade.grade_type}) - {grade.date}\n"

        if len(grades) > 20:
            text += f"\n... and {len(grades) - 20} more grades"

        if bot:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

    @bot.message_handler(commands=['average'])  # type: ignore[attr-defined]
    def handle_average(message: Message) -> None:
        if not hasattr(message, 'chat') or not hasattr(message.chat, 'id'):
            return
        subjects = Subject.get_subjects_by_user(message.chat.id)
        if not subjects:
            if bot:
                bot.reply_to(message, "You don't have any subjects yet.")
            return

        text = "📈 Average Grades:\n\n"
        for subject in subjects:
            grades = Grade.get_grades_by_user(message.chat.id, subject_id=subject.id)
            if grades:
                values = [grade.value for grade in grades if grade.value is not None]
                if values:
                    avg = sum(values) / len(values)
                    text += f"• {subject.name}: {avg:.2f} (from {len(values)} grades)\n"
                else:
                    text += f"• {subject.name}: No grades yet\n"
            else:
                text += f"• {subject.name}: No grades yet\n"

        if bot:
            bot.send_message(message.chat.id, text)

    @bot.message_handler(commands=['cancel'])  # type: ignore[attr-defined]
    def handle_cancel(message: Message) -> None:
        if not hasattr(message, 'chat') or not hasattr(message.chat, 'id'):
            return
        if message.chat.id in user_states:
            del user_states[message.chat.id]
        if bot:
            bot.reply_to(message, "Operation cancelled.")

    @bot.message_handler(func=lambda message: hasattr(message, 'chat') and hasattr(message.chat, 'id') and message.chat.id in user_states)  # type: ignore[attr-defined]
    def handle_user_input(message: Message) -> None:
        if not hasattr(message, 'chat') or not hasattr(message.chat, 'id'):
            return
        state = user_states[message.chat.id]['state']

        if state == 'waiting_subject_name':
            name = getattr(message, 'text', None)
            if not name:
                return
            subject = Subject(user_id=message.chat.id, name=name.strip())
            subject.save()
            del user_states[message.chat.id]
            if bot:
                bot.reply_to(message, f"Subject '{subject.name}' added successfully!")

        elif state == 'waiting_term_name':
            term_name = getattr(message, 'text', None)
            if not term_name:
                return
            user_states[message.chat.id]['term_name'] = term_name.strip()
            user_states[message.chat.id]['state'] = 'waiting_term_start'
            if bot:
                bot.reply_to(message, "Enter start date (YYYY-MM-DD):")

        elif state == 'waiting_term_start':
            text = getattr(message, 'text', None)
            if not text:
                return
            try:
                start_date = date.fromisoformat(text.strip())
                user_states[message.chat.id]['start_date'] = start_date
                user_states[message.chat.id]['state'] = 'waiting_term_end'
                if bot:
                    bot.reply_to(message, "Enter end date (YYYY-MM-DD):")
            except ValueError:
                if bot:
                    bot.reply_to(message, "Invalid date format. Please use YYYY-MM-DD:")

        elif state == 'waiting_term_end':
            text = getattr(message, 'text', None)
            if not text:
                return
            try:
                end_date = date.fromisoformat(text.strip())
                term = Term(
                    user_id=message.chat.id,
                    name=user_states[message.chat.id]['term_name'],
                    start_date=user_states[message.chat.id]['start_date'],
                    end_date=end_date
                )
                term.save()
                del user_states[message.chat.id]
                if bot:
                    bot.reply_to(message, f"Term '{term.name}' added successfully!")
            except ValueError:
                if bot:
                    bot.reply_to(message, "Invalid date format. Please use YYYY-MM-DD:")

        elif state == 'waiting_grade_value':
            text = getattr(message, 'text', None)
            if not text:
                return
            try:
                value = int(text.strip())
                if not 1 <= value <= 12:
                    raise ValueError
                subject_id = user_states[message.chat.id]['subject_id']
                grade = Grade(
                    user_id=message.chat.id,
                    subject_id=subject_id,
                    value=value,
                    grade_type="regular",
                    date_=date.today()
                )
                # Get current term
                current_term = Term.get_current_term(message.chat.id)
                if current_term:
                    grade.term_id = current_term.id
                grade.save()
                del user_states[message.chat.id]
                subject = Subject.get_subject_by_id(subject_id, message.chat.id)
                if bot:
                    bot.reply_to(message, f"Grade {value} added for {subject.name if subject else 'subject'}!")
            except ValueError:
                if bot:
                    bot.reply_to(message, "Please enter a valid grade (1-12):")

# Main bot polling
if __name__ == "__main__":
    if bot:
        log("Bot started")
        bot.polling(none_stop=True)
    else:
        print("Bot token not found. Set TELEGRAM_TOKEN environment variable.")
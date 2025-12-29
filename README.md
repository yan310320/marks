# Marks E-Daybook

A Telegram bot for managing school grades and marks. Built with Python, SQLite, and pyTelegramBotAPI.

## Features

- 📚 **Subject Management**: Add and manage school subjects
- 📊 **Grade Tracking**: Record and view grades for different subjects
- 📅 **Academic Terms**: Organize grades by academic terms
- 📈 **Statistics**: Calculate average grades per subject
- 🤖 **Telegram Bot**: Easy-to-use interface via Telegram

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Telegram Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow the instructions
3. Copy the bot token

### 3. Set Environment Variable

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` and add your bot token:

```
TELEGRAM_TOKEN=your_bot_token_here
```

Or set it directly in your shell:

```bash
# Linux/Mac
export TELEGRAM_TOKEN='your_bot_token_here'

# Windows
set TELEGRAM_TOKEN=your_bot_token_here
```

### 4. Run the Bot

```bash
python Marks.py
```

## Database Schema

The application uses SQLite with the following tables:

- `users`: User information
- `subjects`: School subjects
- `grades`: Individual grades/marks
- `terms`: Academic terms
- `schedule`: Weekly class schedule

## Usage

### Commands

- `/start` - Start using the bot
- `/help` - Show available commands
- `/add_subject` - Add a new subject
- `/list_subjects` - View all subjects
- `/add_grade` - Record a new grade
- `/view_grades` - View grades by subject
- `/average` - Calculate average grades
- `/add_term` - Add academic term
- `/list_terms` - View all terms
- `/cancel` - Cancel current operation

### Example Workflow

1. Start the bot with `/start`
2. Add subjects using `/add_subject`
3. Add academic terms using `/add_term`
4. Record grades using `/add_grade`
5. View statistics with `/average`

## Development

The code is organized as follows:

- `backend.py`: Core functionality, database operations, bot handlers
- `Marks.py`: Main entry point
- `db.db`: SQLite database file
- `requirements.txt`: Python dependencies

## Security Notes

- Bot token is read from environment variable for security
- Database operations use parameterized queries to prevent SQL injection
- User data is isolated by Telegram user ID

## License

This project is open source. Feel free to modify and distribute.
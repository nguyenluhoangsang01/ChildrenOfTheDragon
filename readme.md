# Albion Online Discord Bot - CTA Attendance Tracker

This bot helps Albion Online guilds manage CTA (Call to Arms) attendance using Discord commands and party list screenshots. It supports fuzzy name matching, slash commands, and attendance tracking.

## 🔧 Features

- `!check` — Upload one or more party screenshots to detect present members (message command).
- `/list` — Show full member list with attendance count, sorted by attendance.
- `/add` — Add a new member.
- `/remove` — Remove a member (Admin only).
- `/set` — Upload member list from `.txt` or `.json` file (Admin only).
- `/clear` — Clear all members (Admin only).
- `/filter <operator> <value>` — Show members filtered by attendance (e.g., `> 3`, `= 0`).
- `/today` — Show members who joined CTA today.
- `/yesterday` — Show members who joined CTA yesterday.

## 🧠 How It Works

- Uses **Tesseract OCR** to read names from uploaded images.
- Applies **fuzzy string matching** to detect similar names with tolerance for OCR errors.
- Tracks attendance counts in `attendance_count.json`.
- Logs daily CTA participation in `attendance_log.json`.
- Maintains the guild roster in `guild_members.json`.

## 🛠️ Requirements

- Python 3.9+
- **Tesseract OCR** installed (update the path in `main.py` if needed).
- Python libraries:
  ```bash
  pip install discord.py opencv-python pytesseract rapidfuzz python-dotenv flask

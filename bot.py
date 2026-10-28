import telebot
import sqlite3
import time
import datetime
import os
from dotenv import load_dotenv

# خوندن توکن از فایل مخفی .env
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    print("ERROR: Token not found! Please check your .env file.")
    exit()

bot = telebot.TeleBot(TOKEN)

# ۱. ساخت دیتابیس
def setup_db():
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS reminders
                      (id INTEGER PRIMARY KEY, chat_id TEXT, task TEXT, remind_time TEXT)''')
    conn.commit()
    conn.close()

# ۲. دستور استارت
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, 
                     "سلام! من ربات یادآور هستم. 🕒\n"
                     "برای تنظیم یادآور، دقیقاً با این فرمت پیام بده:\n"
                     "`ساعت:دقیقه متن یادآوری`\n"
                     "مثلاً: `14:30 رفتن به کلاس`", parse_mode='Markdown')

# ۳. دریافت و ذخیره یادآور
@bot.message_handler(func=lambda message: True)
def set_reminder(message):
    try:
        text = message.text
        time_part, task = text.split(" ", 1)
        hour, minute = map(int, time_part.split(":"))
        
        now = datetime.datetime.now()
        remind_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if remind_time < now:
            remind_time += datetime.timedelta(days=1)
            
        remind_time_str = remind_time.strftime("%Y-%m-%d %H:%M")
        
        conn = sqlite3.connect('reminders.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reminders (chat_id, task, remind_time) VALUES (?, ?, ?)", 
                       (str(message.chat.id), task, remind_time_str))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ ثبت شد! ساعت {time_part} بابت «{task}» بهت پیام میدم.")
    except Exception:
        bot.reply_to(message, "❌ فرمت اشتباهه! لطفاً دقیقاً مثل این بفرست:\n`14:30 رفتن به کلاس`", parse_mode='Markdown')

# ۴. حلقه پس‌زمینه
def check_reminders():
    while True:
        try:
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            conn = sqlite3.connect('reminders.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, chat_id, task FROM reminders WHERE remind_time = ?", (now_str,))
            due_reminders = cursor.fetchall()
            
            for r_id, chat_id, task in due_reminders:
                bot.send_message(chat_id, f"🔔 **یادآوری:** {task}", parse_mode='Markdown')
                cursor.execute("DELETE FROM reminders WHERE id = ?", (r_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error: {e}")
            
        time.sleep(30)

# ۵. اجرا
if __name__ == '__main__':
    setup_db()
    print("ربات یادآور روشن شد...")
    
    import threading
    t = threading.Thread(target=check_reminders)
    t.daemon = True
    t.start()
    
    bot.infinity_polling()
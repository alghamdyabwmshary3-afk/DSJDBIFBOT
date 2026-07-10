import os
import re
import json
import sqlite3
import requests
import telebot
import yt_dlp
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from urllib.parse import urlparse, quote
import time
from datetime import datetime, timedelta
import threading
import zipfile
import shutil
import hashlib
import random
import sys

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN environment variable is not set.")
    print("Please add your Telegram bot token as a secret named BOT_TOKEN.")
    sys.exit(1)

OWNER_ID = 8539408138
OWNER_USERNAME = "Mkdkdkd8484849"

bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = "bot_database.db"

CHANNEL_ID = -1003886889715

print(f"📢 تم تعيين القناة: {CHANNEL_ID}")

def init_database():
    """إنشاء قاعدة البيانات مع جميع الجداول"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        join_date TEXT,
        last_active TEXT,
        is_banned INTEGER DEFAULT 0,
        rank TEXT DEFAULT 'عضو',
        daily_reward_date TEXT,
        notifications INTEGER DEFAULT 1
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS channels (
        channel_id TEXT PRIMARY KEY,
        channel_title TEXT,
        added_date TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        media_type TEXT,
        platform TEXT,
        download_date TEXT,
        file_size INTEGER
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS banned_users (
        user_id INTEGER PRIMARY KEY,
        ban_reason TEXT,
        ban_date TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS daily_requests (
        user_id INTEGER,
        request_date TEXT,
        request_count INTEGER DEFAULT 1,
        PRIMARY KEY (user_id, request_date)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        feedback_text TEXT,
        feedback_date TEXT,
        status TEXT DEFAULT 'جديد'
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        notification_text TEXT,
        notification_date TEXT,
        is_read INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS channel_posts (
        post_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_hash TEXT,
        media_type TEXT,
        platform TEXT,
        query TEXT,
        file_size INTEGER,
        post_date TEXT,
        channel_message_id INTEGER,
        views INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_points (
        user_id INTEGER PRIMARY KEY,
        points INTEGER DEFAULT 0,
        total_downloads INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        last_reward_date TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS store_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT,
        item_description TEXT,
        points_cost INTEGER,
        item_type TEXT,
        is_active INTEGER DEFAULT 1
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS bot_settings (
        setting_key TEXT PRIMARY KEY,
        setting_value TEXT,
        updated_date TEXT
    )''')
    
    conn.commit()
    conn.close()

init_database()

def save_channel_setting(channel_id):
    """حفظ معرف القناة في قاعدة البيانات"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT OR REPLACE INTO bot_settings (setting_key, setting_value, updated_date)
                 VALUES ('channel_id', ?, ?)''', (str(channel_id), now))
    conn.commit()
    conn.close()
    print(f"✅ تم حفظ القناة في قاعدة البيانات: {channel_id}")

if CHANNEL_ID:
    save_channel_setting(CHANNEL_ID)

def generate_user_hash(user_id):
    """توليد معرف مشفر للمستخدم لإخفاء هويته"""
    salt = "EMPEROR_BOT_2026"
    hash_object = hashlib.sha256(f"{user_id}{salt}".encode())
    hash_hex = hash_object.hexdigest()
    random_suffix = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=4))
    return f"#{hash_hex[:6]}{random_suffix}"

def get_media_type_emoji(media_type):
    """الحصول على إيموجي مناسب لنوع الميديا"""
    emojis = {
        "image": "🖼️",
        "video": "🎬",
        "audio": "🎵",
        "document": "📄"
    }
    return emojis.get(media_type, "📁")

def get_platform_emoji(platform):
    """الحصول على إيموجي للمنصة"""
    emojis = {
        "youtube": "🔴",
        "instagram": "🟣",
        "facebook": "🔵",
        "tiktok": "⚫",
        "twitter": "🐦",
        "messenger": "💬",
        "pinterest": "📌",
        "soundcloud": "🎵",
        "dailymotion": "🎬",
        "vimeo": "🎥",
        "search": "🔍",
        "unknown": "🌐"
    }
    return emojis.get(platform.lower(), "🌐")

def post_to_channel(user_id, media_type, platform, query, file_size, file_path=None):
    """نشر المحتوى في القناة مع إخفاء الهوية"""
    global CHANNEL_ID
    
    if not CHANNEL_ID:
        print("❌ لا توجد قناة محددة للنشر!")
        return None
    
    try:
        user_hash = generate_user_hash(user_id)
        platform_name = platform.capitalize() if platform != "search" else "بحث"
        media_emoji = get_media_type_emoji(media_type)
        platform_emoji = get_platform_emoji(platform)
        file_size_mb = round(file_size / (1024 * 1024), 2) if file_size else 0
        
        post_text = f"""
{media_emoji} **طلب {media_type} جديد**
━━━━━━━━━━━━━━━━━━━━━━━
📌 **النوع:** {media_type}
{platform_emoji} **المنصة:** {platform_name}
📋 **المحتوى:** `{query[:100]}`

📊 **حجم الملف:** {file_size_mb} ميجابايت
👤 **طلب بواسطة:** {user_hash}
📅 **التاريخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

🔒 جميع الحقوق محفوظة للبوت
━━━━━━━━━━━━━━━━━━━━━━━
#تحميل #{media_type} #{platform if platform != 'search' else 'بحث'}
        """
        
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as file:
                if media_type == "image":
                    msg = bot.send_photo(CHANNEL_ID, file, caption=post_text, parse_mode="Markdown")
                elif media_type == "video":
                    msg = bot.send_video(CHANNEL_ID, file, caption=post_text, parse_mode="Markdown", supports_streaming=True)
                elif media_type == "audio":
                    msg = bot.send_audio(CHANNEL_ID, file, caption=post_text, parse_mode="Markdown")
                else:
                    msg = bot.send_document(CHANNEL_ID, file, caption=post_text, parse_mode="Markdown")
        else:
            msg = bot.send_message(CHANNEL_ID, post_text, parse_mode="Markdown")
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''INSERT INTO channel_posts 
                     (user_id, user_hash, media_type, platform, query, file_size, post_date, channel_message_id)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (user_id, user_hash, media_type, platform, query, file_size, now, msg.message_id))
        conn.commit()
        conn.close()
        
        try:
            bot.send_message(
                user_id,
                f"✅ **تم نشر طلبك في قناة البوت!**\n\n"
                f"🔗 معرفك المشفر: `{user_hash}`\n"
                f"📌 نوع المحتوى: {media_type}\n"
                f"🌐 المنصة: {platform_name}"
            )
        except:
            pass
        
        print(f"✅ تم النشر في القناة: {media_type} - {platform_name}")
        return msg.message_id
        
    except Exception as e:
        print(f"❌ خطأ في النشر للقناة: {e}")
        return None

def get_user_points(user_id):
    """الحصول على نقاط المستخدم"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT points FROM user_points WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    return 0

def add_points(user_id, points):
    """إضافة نقاط للمستخدم"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''INSERT INTO user_points (user_id, points, total_downloads, level)
                 VALUES (?, ?, 0, 1)
                 ON CONFLICT(user_id) DO UPDATE SET points = points + ?''',
              (user_id, points, points))
    conn.commit()
    conn.close()

def get_points_multiplier(media_type):
    """الحصول على مضاعف النقاط حسب نوع الميديا"""
    multipliers = {
        "image": 1,
        "audio": 2,
        "video": 3,
        "document": 1
    }
    return multipliers.get(media_type, 1)

def add_download_points(user_id, media_type):
    """إضافة نقاط عند التحميل"""
    points = get_points_multiplier(media_type)
    add_points(user_id, points)
    return points

def send_notification(user_id, title, message, notification_type="info"):
    """إرسال إشعار للمستخدم"""
    try:
        emojis = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "reward": "🎁",
            "achievement": "🏆"
        }
        emoji = emojis.get(notification_type, "ℹ️")
        
        notification_text = f"""
{emoji} **{title}**
━━━━━━━━━━━━━━━━━━━
{message}

📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        bot.send_message(user_id, notification_text, parse_mode="Markdown")
        return True
    except:
        return False

def get_library_posts(limit=10):
    """الحصول على أحدث المنشورات في المكتبة"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''SELECT user_hash, media_type, platform, query, file_size, post_date
                 FROM channel_posts
                 ORDER BY post_date DESC
                 LIMIT ?''', (limit,))
    results = c.fetchall()
    conn.close()
    return results

def get_leaderboard(limit=10):
    """الحصول على لوحة المتصدرين"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''SELECT user_hash, COUNT(*) as download_count, 
                 (SELECT points FROM user_points WHERE user_id = channel_posts.user_id) as points
                 FROM channel_posts
                 GROUP BY user_hash
                 ORDER BY download_count DESC
                 LIMIT ?''', (limit,))
    results = c.fetchall()
    conn.close()
    return results

def get_recommendations(user_id, limit=5):
    """الحصول على توصيات مخصصة للمستخدم"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''SELECT media_type, platform, query
                 FROM channel_posts
                 WHERE user_id = ?
                 ORDER BY post_date DESC
                 LIMIT 5''', (user_id,))
    user_history = c.fetchall()
    
    if not user_history:
        c.execute('''SELECT media_type, platform, COUNT(*) as count
                     FROM channel_posts
                     GROUP BY media_type, platform
                     ORDER BY count DESC
                     LIMIT 5''')
        recommendations = c.fetchall()
    else:
        media_types = [row[0] for row in user_history]
        platforms = [row[1] for row in user_history]
        
        c.execute('''SELECT media_type, platform, query
                     FROM channel_posts
                     WHERE media_type IN ({}) OR platform IN ({})
                     ORDER BY post_date DESC
                     LIMIT ?'''.format(
                         ','.join(['?']*len(media_types)),
                         ','.join(['?']*len(platforms))
                     ), (*media_types, *platforms, limit))
        recommendations = c.fetchall()
    
    conn.close()
    return recommendations

def save_user(user_id, username=None, first_name=None, last_name=None):
    """حفظ المستخدم في قاعدة البيانات"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        c.execute('''INSERT OR IGNORE INTO users 
                     (user_id, username, first_name, last_name, join_date, last_active, rank)
                     VALUES (?, ?, ?, ?, ?, ?, 'عضو')''',
                  (user_id, username, first_name, last_name, now, now))
        
        c.execute('''UPDATE users SET last_active = ? WHERE user_id = ?''', (now, user_id))
        conn.commit()
        conn.close()
    except:
        pass

def update_user_rank(user_id):
    """تحديث مستوى المستخدم حسب عدد التحميلات"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM stats WHERE user_id = ?', (user_id,))
        downloads = c.fetchone()[0]
        
        if downloads >= 1000:
            rank = '👑 إمبراطوري'
        elif downloads >= 500:
            rank = '💎 ذهبي'
        elif downloads >= 100:
            rank = '⭐ مميز'
        else:
            rank = '👤 عضو'
        
        c.execute('UPDATE users SET rank = ? WHERE user_id = ?', (rank, user_id))
        conn.commit()
        conn.close()
        return rank
    except:
        return '👤 عضو'

def is_user_banned(user_id):
    """التحقق إذا كان المستخدم محظوراً"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT user_id FROM banned_users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def ban_user(user_id, reason="لا يوجد سبب"):
    """حظر مستخدم"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT OR IGNORE INTO banned_users (user_id, ban_reason, ban_date) VALUES (?, ?, ?)',
              (user_id, reason, now))
    conn.commit()
    conn.close()

def unban_user(user_id):
    """إلغاء حظر مستخدم"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def check_rate_limit(user_id, max_requests=30):
    """التحقق من عدد الطلبات لتجنب السبام"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    c.execute('''INSERT OR IGNORE INTO daily_requests (user_id, request_date, request_count)
                 VALUES (?, ?, 0)''', (user_id, today))
    
    c.execute('''UPDATE daily_requests SET request_count = request_count + 1
                 WHERE user_id = ? AND request_date = ?''', (user_id, today))
    
    c.execute('SELECT request_count FROM daily_requests WHERE user_id = ? AND request_date = ?',
              (user_id, today))
    count = c.fetchone()[0]
    conn.commit()
    conn.close()
    
    return count <= max_requests

def get_remaining_requests(user_id):
    """الحصول على عدد الطلبات المتبقية"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute('SELECT request_count FROM daily_requests WHERE user_id = ? AND request_date = ?',
              (user_id, today))
    result = c.fetchone()
    conn.close()
    if result:
        return max(0, 30 - result[0])
    return 30

def get_users_count():
    """عدد المستخدمين الكلي"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    count = c.fetchone()[0]
    conn.close()
    return count

def get_active_users_today():
    """عدد المستخدمين النشطين اليوم"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute('SELECT COUNT(DISTINCT user_id) FROM stats WHERE download_date LIKE ?', (f"{today}%",))
    count = c.fetchone()[0]
    conn.close()
    return count

def get_total_downloads():
    """إجمالي التحميلات"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM stats')
    count = c.fetchone()[0]
    conn.close()
    return count

def increment_download_stats(user_id, media_type, platform="unknown", file_size=0):
    """تسجيل عملية تحميل"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO stats (user_id, media_type, platform, download_date, file_size)
                 VALUES (?, ?, ?, ?, ?)''',
              (user_id, media_type, platform, now, file_size))
    conn.commit()
    conn.close()
    update_user_rank(user_id)

def save_channel(channel_id, channel_title="غير معروف"):
    """حفظ قناة إجبارية مع إشعار جميع المستخدمين"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('INSERT OR IGNORE INTO channels (channel_id, channel_title, added_date) VALUES (?, ?, ?)',
              (channel_id, channel_title, now))
    conn.commit()
    conn.close()
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT user_id FROM users')
        users = c.fetchall()
        conn.close()
        
        for user_id in users:
            try:
                bot.send_message(
                    user_id[0],
                    f"📢 **تم إضافة قناة جديدة للاشتراك الإجباري!**\n\n"
                    f"🔹 القناة: `{channel_title}`\n"
                    f"🔹 يرجى الاشتراك فيها لمواصلة استخدام البوت.\n\n"
                    f"💡 أرسل أي كلمة أو رابط وسيظهر لك طلب الاشتراك."
                )
                time.sleep(0.05)
            except:
                pass
    except:
        pass

def get_channels():
    """الحصول على قائمة القنوات الإجبارية"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT channel_id FROM channels')
    channels = [row[0] for row in c.fetchall()]
    conn.close()
    return channels

def clear_channels():
    """تصفير القنوات الإجبارية"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM channels')
    conn.commit()
    conn.close()

def get_user_rank(user_id):
    """الحصول على مستوى المستخدم"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT rank FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else '👤 عضو'

def save_feedback(user_id, feedback_text):
    """حفظ ملاحظة"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''INSERT INTO feedback (user_id, feedback_text, feedback_date)
                 VALUES (?, ?, ?)''', (user_id, feedback_text, now))
    conn.commit()
    conn.close()

def get_feedback_list():
    """الحصول على قائمة الملاحظات"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''SELECT id, user_id, feedback_text, feedback_date, status 
                 FROM feedback WHERE status = 'جديد'
                 ORDER BY feedback_date DESC LIMIT 20''')
    results = c.fetchall()
    conn.close()
    return results

def get_daily_reward(user_id):
    """التحقق من المكافأة اليومية"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute('SELECT daily_reward_date FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    if result and result[0] == today:
        return False
    return True

def update_daily_reward(user_id):
    """تحديث تاريخ المكافأة اليومية"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute('UPDATE users SET daily_reward_date = ? WHERE user_id = ?', (today, user_id))
    conn.commit()
    conn.close()

user_sessions = {}
user_queues = {}
user_processing = {}

def check_all_subscriptions(chat_id):
    """التحقق من اشتراك المستخدم في جميع القنوات الإجبارية"""
    
    if chat_id == OWNER_ID:
        return []
    
    if is_user_banned(chat_id):
        return ["banned"]
    
    channels = get_channels()
    
    if not channels:
        return []
    
    unsubscribed_channels = []
    
    for ch_id in channels:
        try:
            member = bot.get_chat_member(ch_id, chat_id)
            
            if member.status not in ["member", "administrator", "creator"]:
                raise Exception("غير مشترك")
            
            if member.user.is_bot:
                raise Exception("بوت")
                
        except Exception as e:
            try:
                invite_link = bot.export_chat_invite_link(ch_id)
                chat_info = bot.get_chat(ch_id)
                unsubscribed_channels.append({
                    "title": chat_info.title,
                    "url": invite_link,
                    "id": ch_id
                })
            except Exception as invite_error:
                unsubscribed_channels.append({
                    "title": f"قناة {ch_id}",
                    "url": None,
                    "id": ch_id
                })
    
    return unsubscribed_channels

def send_dynamic_join_request(chat_id, unsub_list, message_id=None):
    """إرسال طلب الاشتراك بالقنوات مع أزرار"""
    
    if unsub_list == ["banned"]:
        bot.send_message(chat_id, "⛔ **أنت محظور من استخدام البوت!**\nللتواصل مع المطور: @Mkdkdkd8484849")
        return
    
    markup = InlineKeyboardMarkup(row_width=2)
    
    for ch in unsub_list:
        button_text = f"📢 اشترك في {ch['title']}"
        if ch.get('url'):
            markup.add(InlineKeyboardButton(button_text, url=ch['url']))
        else:
            markup.add(InlineKeyboardButton(button_text, callback_data=f"channel_info_{ch['id']}"))
    
    markup.add(InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub"))
    
    msg_text = (
        "🔒 **للاستمرار في استخدام البوت، يجب الاشتراك في القنوات التالية:**\n\n"
        "📌 اشترك في جميع القنوات المذكورة أدناه، ثم اضغط على زر التحقق.\n\n"
        f"📊 عدد القنوات: `{len(unsub_list)}`"
    )
    
    bot.send_message(chat_id, msg_text, parse_mode="Markdown", reply_markup=markup)

def show_main_menu(chat_id, user_id):
    """عرض القائمة الرئيسية المتطورة"""
    markup = InlineKeyboardMarkup(row_width=2)
    
    markup.add(
        InlineKeyboardButton("🔍 بحث", callback_data="menu_search"),
        InlineKeyboardButton("📥 تحميل رابط", callback_data="menu_download")
    )
    markup.add(
        InlineKeyboardButton("🏆 المتصدرين", callback_data="menu_leaderboard"),
        InlineKeyboardButton("🎁 مكافأة يومية", callback_data="menu_daily")
    )
    markup.add(
        InlineKeyboardButton("📊 إحصائياتي", callback_data="menu_my_stats"),
        InlineKeyboardButton("📚 المكتبة", callback_data="menu_library")
    )
    markup.add(
        InlineKeyboardButton("🎯 توصيات", callback_data="menu_recommend"),
        InlineKeyboardButton("❓ مساعدة", callback_data="menu_help")
    )
    
    if user_id == OWNER_ID:
        markup.add(
            InlineKeyboardButton("👑 لوحة التحكم", callback_data="menu_admin_panel"),
            InlineKeyboardButton("📢 إعدادات القناة", callback_data="menu_channel_settings")
        )
    
    points = get_user_points(user_id)
    rank = get_user_rank(user_id)
    
    welcome_text = f"""
👑 **مرحباً بك في البوت الإمبراطوري!**
━━━━━━━━━━━━━━━━━━━━━━━

📌 **مستواك:** {rank}
⭐ **نقاطك:** {points}

🎯 **اختر من القائمة أدناه:**
    """
    
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=markup)

def show_channel_settings(chat_id):
    """عرض إعدادات القناة"""
    global CHANNEL_ID
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📢 تعيين قناة نشر جديدة", callback_data="set_channel"),
        InlineKeyboardButton("📊 إحصائيات القناة", callback_data="channel_stats")
    )
    
    text = f"""
📢 **إعدادات قناة النشر**
━━━━━━━━━━━━━━━━━━━━━━━

🔹 **القناة الحالية:** `{CHANNEL_ID if CHANNEL_ID else 'لم يتم التعيين'}`
🔒 **الوضع:** نشر تلقائي مع إخفاء الهوية

📌 **كيف يعمل النظام:**
- عند كل تحميل، يتم نشر المحتوى في القناة
- سيتم إخفاء هويات المستخدمين تماماً
- يمكنك تعيين القناة بالضغط على الزر أدناه
    """
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

def process_search_download(chat_id, query_text, media_type, reply_to_id):
    """معالجة البحث وتحميل أول نتيجة"""
    
    unsub_list = check_all_subscriptions(chat_id)
    if unsub_list:
        send_dynamic_join_request(chat_id, unsub_list)
        return
    
    if not check_rate_limit(chat_id):
        remaining = get_remaining_requests(chat_id)
        bot.send_message(chat_id, f"⛔ **تم تجاوز حد الطلبات اليومي!**\nالطلبات المتبقية: {remaining}")
        return
    
    status_msg = bot.send_message(chat_id, f"🔍 **جاري البحث عن:** `{query_text}`", parse_mode="Markdown")
    
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    ydl_opts = {
        "outtmpl": f"downloads/{chat_id}_%(id)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "geo_bypass": True,
        "default_search": "ytsearch1",
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        },
        "socket_timeout": 30,
        "retries": 3,
        "ignoreerrors": True,
        "no_color": True,
    }
    
    if media_type == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }]
    elif media_type == "video":
        ydl_opts["format"] = "best[ext=mp4]/best"
    elif media_type == "image":
        ydl_opts["format"] = "best"
        ydl_opts["writethumbnail"] = True
        ydl_opts["skip_download"] = True
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if media_type == "image":
                info = ydl.extract_info(f"ytsearch1:{query_text}", download=True)
                if info and "entries" in info and info["entries"]:
                    entry = info["entries"][0]
                    thumbnail_url = entry.get("thumbnail", "")
                    if thumbnail_url:
                        bot.send_photo(chat_id, thumbnail_url,
                                       caption=f"🖼️ **{entry.get('title', query_text)}**",
                                       reply_to_message_id=reply_to_id)
                        
                        add_download_points(chat_id, "image")
                        increment_download_stats(chat_id, "image", "search", 0)
                        post_to_channel(chat_id, "image", "search", query_text, 0)
                        bot.delete_message(chat_id, status_msg.message_id)
                        return
                bot.edit_message_text("❌ **لم يتم العثور على صور!**", chat_id, status_msg.message_id)
                return
            
            info = ydl.extract_info(f"ytsearch1:{query_text}", download=True)
            
            if not info or "entries" not in info or not info["entries"]:
                bot.edit_message_text("❌ **لم يتم العثور على نتائج!**", chat_id, status_msg.message_id)
                return
            
            entry = info["entries"][0]
            filename = ydl.prepare_filename(entry)
            
            if media_type == "audio":
                base, _ = os.path.splitext(filename)
                for ext in [".mp3", ".m4a", ".ogg", ".webm"]:
                    if os.path.exists(base + ext):
                        filename = base + ext
                        break
            
            if not os.path.exists(filename):
                base, _ = os.path.splitext(filename)
                for ext in [".mp4", ".mp3", ".mkv", ".webm", ".m4a"]:
                    if os.path.exists(base + ext):
                        filename = base + ext
                        break
            
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                with open(filename, "rb") as file_to_send:
                    if media_type == "audio":
                        bot.send_audio(chat_id, file_to_send,
                                       caption=f"🎵 **{entry.get('title', query_text)}**",
                                       reply_to_message_id=reply_to_id,
                                       timeout=180)
                    else:
                        bot.send_video(chat_id, file_to_send,
                                       caption=f"🎬 **{entry.get('title', query_text)}**",
                                       reply_to_message_id=reply_to_id,
                                       timeout=180,
                                       supports_streaming=True)
                
                points = add_download_points(chat_id, media_type)
                increment_download_stats(chat_id, media_type, "search", file_size)
                post_to_channel(chat_id, media_type, "search", query_text, file_size, filename)
                
                try:
                    os.remove(filename)
                except:
                    pass
                
                bot.delete_message(chat_id, status_msg.message_id)
            else:
                bot.edit_message_text("❌ **فشل التحميل!**", chat_id, status_msg.message_id)
    
    except Exception as e:
        print(f"Search download error: {e}")
        try:
            bot.edit_message_text("❌ **حدث خطأ أثناء البحث والتحميل.**", chat_id, status_msg.message_id)
        except:
            pass

def clean_and_fix_url(url):
    """تنظيف الرابط وإصلاحه"""
    if "instagram.com" in url and "?" in url:
        url = url.split("?")[0]
    if "x.com" in url:
        url = url.replace("x.com", "twitter.com")
    for param in ["?utm_", "&utm_", "?fbclid", "&fbclid"]:
        if param in url:
            url = url.split(param)[0]
    return url

def download_media_processor(url, chat_id, reply_to_id, media_type, quality=None, platform="unknown"):
    """معالجة تحميل الوسائط"""
    
    try:
        unsub_list = check_all_subscriptions(chat_id)
        if unsub_list:
            send_dynamic_join_request(chat_id, unsub_list)
            return False
        
        if not check_rate_limit(chat_id):
            remaining = get_remaining_requests(chat_id)
            bot.send_message(chat_id, f"⛔ **تم تجاوز حد الطلبات اليومي!**\nالطلبات المتبقية: {remaining}")
            return False
        
        status_msg = bot.send_message(chat_id, "⏳ **جاري التحميل والتجهيز...**", parse_mode="Markdown")
        
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        
        ydl_opts = {
            "outtmpl": f"downloads/{chat_id}_%(id)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            },
            "socket_timeout": 30,
            "retries": 10,
            "fragment_retries": 10,
            "ignoreerrors": True,
            "no_color": True,
            "extract_flat": False
        }
        
        if media_type == "audio":
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        else:
            if quality == "1080p":
                ydl_opts["format"] = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best"
            elif quality == "720p":
                ydl_opts["format"] = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best"
            elif quality == "480p":
                ydl_opts["format"] = "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best"
            elif quality == "360p":
                ydl_opts["format"] = "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best"
            else:
                ydl_opts["format"] = "best[ext=mp4]/best"
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    url = clean_and_fix_url(url)
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    
                    if media_type == "audio":
                        base, _ = os.path.splitext(filename)
                        if os.path.exists(base + ".mp3"):
                            filename = base + ".mp3"
                    
                    if not os.path.exists(filename):
                        base, _ = os.path.splitext(filename)
                        for ext in [".mp4", ".mp3", ".mkv", ".webm", ".m4a", ".mp4a"]:
                            if os.path.exists(base + ext):
                                filename = base + ext
                                break
                    
                    if os.path.exists(filename):
                        file_size = os.path.getsize(filename)
                        with open(filename, "rb") as file_to_send:
                            if media_type == "audio":
                                bot.send_audio(chat_id, file_to_send,
                                             caption="🎵 **تم تحميل الصوت بنجاح** ✨",
                                             reply_to_message_id=reply_to_id,
                                             timeout=180)
                            else:
                                quality_text = f"بجودة {quality}" if quality else "تلقائية"
                                bot.send_video(chat_id, file_to_send,
                                             caption=f"🎬 **تم تحميل الفيديو {quality_text}** ✨",
                                             reply_to_message_id=reply_to_id,
                                             timeout=180,
                                             supports_streaming=True)
                        
                        query = url[:100]
                        post_to_channel(chat_id, media_type, platform, query, file_size, filename)
                        points = add_download_points(chat_id, media_type)
                        
                        send_notification(chat_id, "🌟 مكافأة تحميل!", f"لقد حصلت على **{points} نقطة** لتحميل {media_type}!\n📊 إجمالي نقاطك: {get_user_points(chat_id)}")
                        
                        os.remove(filename)
                        bot.delete_message(chat_id, status_msg.message_id)
                        increment_download_stats(chat_id, media_type, platform, file_size)
                        return True
                    else:
                        raise Exception("الملف غير موجود")
            
            except Exception as e:
                print(f"Download attempt {attempt + 1} failed: {e}")
                if attempt == max_attempts - 1:
                    bot.edit_message_text("❌ **فشل التحميل، تأكد من صلاحية الرابط.**",
                                        chat_id, status_msg.message_id)
                    return False
                else:
                    time.sleep(2)
                    continue
        
        return False
    
    except Exception as e:
        print(f"Download error: {e}")
        bot.send_message(chat_id, "❌ **حدث خطأ أثناء التحميل، حاول مرة أخرى.**")
        return False

def show_word_options(message, text_query):
    """عرض أزرار اختيار نوع الميديا"""
    markup = InlineKeyboardMarkup(row_width=2)
    session_id = str(message.message_id)
    user_sessions[f"word_{message.chat.id}_{session_id}"] = text_query
    
    markup.add(
        InlineKeyboardButton("🎵 صوت", callback_data=f"wtype_audio_{session_id}"),
        InlineKeyboardButton("🎬 فيديو", callback_data=f"wtype_video_{session_id}"),
        InlineKeyboardButton("🖼️ صورة", callback_data=f"wtype_image_{session_id}")
    )
    
    bot.reply_to(message, "📥 **اختر نوع المحتوى من الأزرار التالية:**", reply_markup=markup)

def show_link_platforms(message, url):
    """عرض أزرار المنصات"""
    markup = InlineKeyboardMarkup(row_width=2)
    session_id = str(message.message_id)
    user_sessions[f"link_{message.chat.id}_{session_id}"] = url
    
    markup.add(
        InlineKeyboardButton("🔵 فيسبوك", callback_data=f"plat_fb_{session_id}"),
        InlineKeyboardButton("⚫ تيك توك", callback_data=f"plat_tt_{session_id}")
    )
    markup.add(
        InlineKeyboardButton("🐦 تويتر", callback_data=f"plat_tw_{session_id}"),
        InlineKeyboardButton("💬 ماسنجر", callback_data=f"plat_ms_{session_id}")
    )
    markup.add(
        InlineKeyboardButton("🟣 انستغرام", callback_data=f"plat_ig_{session_id}"),
        InlineKeyboardButton("🔴 يوتيوب", callback_data=f"plat_yt_{session_id}")
    )
    markup.add(
        InlineKeyboardButton("📌 Pinterest", callback_data=f"plat_pin_{session_id}")
    )
    
    bot.reply_to(message, "📱 **اختر المنصة المطلوبة للتحميل:**", reply_markup=markup)

def show_service_type_options(chat_id, session_id, platform_name):
    """سؤال المستخدم: فيديو أم صوت"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎬 فيديو", callback_data=f"srv_video_{platform_name}_{session_id}"),
        InlineKeyboardButton("🎵 صوت", callback_data=f"srv_audio_{platform_name}_{session_id}")
    )
    bot.send_message(chat_id, "🎥 **اختر نوع التحميل:**", reply_markup=markup)

def show_quality_options(chat_id, session_id, platform_name):
    """عرض جودات الفيديو"""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("1080p 🔥", callback_data=f"qual_1080p_{platform_name}_{session_id}"),
        InlineKeyboardButton("720p ✨", callback_data=f"qual_720p_{platform_name}_{session_id}")
    )
    markup.add(
        InlineKeyboardButton("480p ⚡", callback_data=f"qual_480p_{platform_name}_{session_id}"),
        InlineKeyboardButton("360p 📉", callback_data=f"qual_360p_{platform_name}_{session_id}")
    )
    bot.send_message(chat_id, "⚙️ **اختر الجودة المناسبة:**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    user_id = call.from_user.id
    
    if is_user_banned(chat_id):
        bot.answer_callback_query(call.id, "⛔ أنت محظور!", show_alert=True)
        return
    
    if call.data.startswith("menu_"):
        action = call.data.replace("menu_", "")
        
        if action == "search":
            bot.answer_callback_query(call.id, "🔍 أرسل كلمة البحث الآن")
            bot.send_message(chat_id, "✍️ **أرسل الكلمة التي تريد البحث عنها:**")
        
        elif action == "download":
            bot.answer_callback_query(call.id, "📥 أرسل الرابط الآن")
            bot.send_message(chat_id, "🔗 **أرسل الرابط الذي تريد تحميله:**")
        
        elif action == "leaderboard":
            leaders = get_leaderboard(10)
            if not leaders:
                bot.send_message(chat_id, "📭 **لا يوجد متصدرين حتى الآن!**\nكن أول من يحمّل المحتوى.")
                return
            
            text = "🏆 **لوحة المتصدرين**\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            for i, (user_hash, downloads, points) in enumerate(leaders, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                text += f"{medal} {user_hash} - {downloads} تحميل - {points or 0} نقطة\n"
            
            bot.send_message(chat_id, text)
        
        elif action == "daily":
            daily_reward(call.message)
        
        elif action == "my_stats":
            points = get_user_points(user_id)
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM channel_posts WHERE user_id = ?', (user_id,))
            downloads = c.fetchone()[0]
            conn.close()
            
            text = f"""
📊 **إحصائياتك الشخصية**
━━━━━━━━━━━━━━━━━━━━━━━
👑 مستواك: {get_user_rank(user_id)}
⭐ نقاطك: {points}
📥 عدد التحميلات: {downloads}
📈 النقاط المتبقية للمستوى التالي: {100 - (downloads % 100)}
            """
            bot.send_message(chat_id, text, parse_mode="Markdown")
        
        elif action == "library":
            posts = get_library_posts(10)
            if not posts:
                bot.send_message(chat_id, "📚 **المكتبة فارغة حالياً!**\nقم بتحميل محتوى لبدء المكتبة.")
                return
            
            text = "📚 **أحدث المحتويات في المكتبة**\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            for post in posts[:5]:
                user_hash, media_type, platform, query, file_size, date = post
                text += f"{get_media_type_emoji(media_type)} {media_type} - {platform}\n   📝 {query[:30]}...\n   👤 {user_hash} | 📅 {date[:10]}\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            bot.send_message(chat_id, text)
        
        elif action == "recommend":
            recommendations = get_recommendations(user_id, 5)
            if not recommendations:
                bot.send_message(chat_id, "📭 **لا توجد توصيات حالياً!**\nحمّل بعض المحتوى للحصول على توصيات.")
                return
            
            text = "🎯 **توصيات مخصصة لك**\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            for media_type, platform, query in recommendations:
                text += f"{get_media_type_emoji(media_type)} **{media_type}** - {platform}\n   📝 {query[:50]}\n━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            bot.send_message(chat_id, text)
        
        elif action == "help":
            help_text = """
❓ **مساعدة - البوت الإمبراطوري**
━━━━━━━━━━━━━━━━━━━━━━━

📌 **طرق الاستخدام:**

1️⃣ **بحث سريع:**
   - أرسل كلمة → اختر نوع المحتوى

2️⃣ **تحميل من رابط:**
   - أرسل رابط → اختر المنصة → اختر النوع والجودة

3️⃣ **المكافآت اليومية:**
   - استخدم أمر `/daily` أو زر المكافآت

4️⃣ **النقاط والمستويات:**
   - كل تحميل يمنحك نقاط
   - النقاط تؤهلك لمستويات أعلى

5️⃣ **المكتبة:**
   - استعرض أحدث التحميلات من المستخدمين

6️⃣ **التوصيات:**
   - اقتراحات مخصصة بناءً على تاريخ تحميلاتك

🔗 **للتواصل مع المطور:** @Mkdkdkd8484849
            """
            bot.send_message(chat_id, help_text, parse_mode="Markdown")
        
        elif action == "admin_panel":
            if user_id != OWNER_ID:
                bot.answer_callback_query(call.id, "⛔ غير مصرح!", show_alert=True)
                return
            admin_panel(call.message)
        
        elif action == "channel_settings":
            if user_id != OWNER_ID:
                bot.answer_callback_query(call.id, "⛔ غير مصرح!", show_alert=True)
                return
            show_channel_settings(chat_id)
        
        bot.answer_callback_query(call.id)
        return
    
    if call.data.startswith("channel_info_"):
        channel_id = call.data.replace("channel_info_", "")
        bot.answer_callback_query(call.id, f"🔍 معرف القناة: {channel_id}\nابحث عن القناة يدوياً واشترك فيها.", show_alert=True)
        return
    
    if call.data.startswith("wtype_"):
        parts = call.data.split("_")
        media_type = parts[1]
        session_id = parts[2]
        session_key = f"word_{chat_id}_{session_id}"
        
        if session_key in user_sessions:
            query_text = user_sessions[session_key]
            try:
                bot.delete_message(chat_id, message_id)
            except:
                pass
            process_search_download(chat_id, query_text, media_type, int(session_id))
            del user_sessions[session_key]
        else:
            bot.answer_callback_query(call.id, "❌ انتهت صلاحية الجلسة.", show_alert=True)
        return
    
    if call.data.startswith("plat_"):
        parts = call.data.split("_")
        platform_name = parts[1]
        session_id = parts[2]
        
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        show_service_type_options(chat_id, session_id, platform_name)
        bot.answer_callback_query(call.id, "✅ تم اختيار المنصة")
        return
    
    if call.data.startswith("srv_"):
        parts = call.data.split("_")
        media_type = parts[1]
        platform_name = parts[2]
        session_id = parts[3]
        
        session_key = f"link_{chat_id}_{session_id}"
        if session_key not in user_sessions:
            bot.answer_callback_query(call.id, "❌ حدث خطأ في الجلسة.", show_alert=True)
            return
        
        url = user_sessions[session_key]
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass
        
        platform_names = {
            "fb": "Facebook", "tt": "TikTok", "tw": "Twitter",
            "ms": "Messenger", "ig": "Instagram", "yt": "YouTube", "pin": "Pinterest"
        }
        platform_full = platform_names.get(platform_name, "unknown")
        
        if media_type == "audio":
            download_media_processor(url, chat_id, int(session_id), "audio", platform=platform_full)
            del user_sessions[session_key]
        else:
            show_quality_options(chat_id, session_id, platform_name)
        return
    
    if call.data.startswith("qual_"):
        parts = call.data.split("_")
        quality_val = parts[1]
        platform_name = parts[2]
        session_id = parts[3]
        
        session_key = f"link_{chat_id}_{session_id}"
        if session_key in user_sessions:
            url = user_sessions[session_key]
            try:
                bot.delete_message(chat_id, message_id)
            except:
                pass
            
            platform_names = {
                "fb": "Facebook", "tt": "TikTok", "tw": "Twitter",
                "ms": "Messenger", "ig": "Instagram", "yt": "YouTube", "pin": "Pinterest"
            }
            platform_full = platform_names.get(platform_name, "unknown")
            
            download_media_processor(url, chat_id, int(session_id), "video", quality=quality_val, platform=platform_full)
            del user_sessions[session_key]
        else:
            bot.answer_callback_query(call.id, "❌ انتهت الجلسة.")
        return
    
    if call.data == "check_sub":
        bot.answer_callback_query(call.id, "🔍 جاري التحقق من اشتراكك...", show_alert=False)
        
        unsub_list = check_all_subscriptions(chat_id)
        
        if not unsub_list:
            try:
                bot.delete_message(chat_id, message_id)
            except:
                pass
            bot.send_message(
                chat_id, 
                "🎉 **تم التفعيل بنجاح! أهلاً بك في البوت.**\n\n"
                "✅ أنت الآن مشترك في جميع القنوات المطلوبة.\n\n"
                "💡 أرسل كلمة للبحث أو رابط للتحميل."
            )
        else:
            markup = InlineKeyboardMarkup(row_width=2)
            
            for ch in unsub_list:
                button_text = f"📢 اشترك في {ch['title']}"
                if ch.get('url'):
                    markup.add(InlineKeyboardButton(button_text, url=ch['url']))
                else:
                    markup.add(InlineKeyboardButton(button_text, callback_data=f"channel_info_{ch['id']}"))
            
            markup.add(InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_sub"))
            
            msg_text = (
                "⚠️ **لا زلت غير مشترك في جميع القنوات!**\n\n"
                "📌 اشترك في القنوات التالية، ثم اضغط على زر التحقق 👇\n"
                f"📊 عدد القنوات المتبقية: `{len(unsub_list)}`"
            )
            
            try:
                bot.edit_message_text(msg_text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
            except:
                bot.send_message(chat_id, msg_text, parse_mode="Markdown", reply_markup=markup)
            
            bot.answer_callback_query(call.id, f"❌ لم تشترك في {len(unsub_list)} قنوات بعد!", show_alert=True)
        return
    
    if call.data == "broadcast_msg":
        if chat_id != OWNER_ID:
            bot.answer_callback_query(call.id, "⛔ غير مصرح", show_alert=True)
            return
        msg = bot.send_message(OWNER_ID, "✍️ **أرسل رسالة الإذاعة:**\nلإلغاء الأمر أرسل `/cancel`")
        bot.register_next_step_handler(msg, start_broadcasting)
        bot.answer_callback_query(call.id, "✅ جاهز للإذاعة")
        return
    
    if call.data == "clear_ch":
        if chat_id != OWNER_ID:
            bot.answer_callback_query(call.id, "⛔ غير مصرح", show_alert=True)
            return
        clear_channels()
        bot.answer_callback_query(call.id, "✅ تم تصفير القنوات!", show_alert=True)
        admin_panel(call.message)
        return
    
    if call.data == "stats_advanced":
        if chat_id != OWNER_ID:
            bot.answer_callback_query(call.id, "⛔ غير مصرح", show_alert=True)
            return
        
        total_users = get_users_count()
        active_today = get_active_users_today()
        total_downloads = get_total_downloads()
        channels_count = len(get_channels())
        
        stats_text = (
            "📊 **الإحصائيات المتقدمة**\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"👥 إجمالي المستخدمين: `{total_users}`\n"
            f"🟢 النشاط اليومي: `{active_today}`\n"
            f"📥 إجمالي التحميلات: `{total_downloads}`\n"
            f"📈 متوسط التحميل: `{round(total_downloads/max(1,total_users), 1)}`\n"
            f"📢 القنوات الإجبارية: `{channels_count}`"
        )
        bot.edit_message_text(stats_text, chat_id, message_id, parse_mode="Markdown")
        return
    
    if call.data == "feedback_list":
        if chat_id != OWNER_ID:
            bot.answer_callback_query(call.id, "⛔ غير مصرح", show_alert=True)
            return
        
        feedbacks = get_feedback_list()
        if not feedbacks:
            bot.answer_callback_query(call.id, "📭 لا توجد ملاحظات جديدة!", show_alert=True)
            return
        
        text = "📋 **الملاحظات الجديدة**\n━━━━━━━━━━━━━━━━━━━\n"
        for fb in feedbacks[:5]:
            fb_id, fb_user_id, fb_text, fb_date, fb_status = fb
            text += f"🔹 المستخدم: `{fb_user_id}`\n📝 {fb_text[:100]}\n📅 {fb_date[:10]}\n━━━━━━━━━━━━━━━━━━━\n"
        
        bot.send_message(chat_id, text, parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        return
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "set_channel")
def handle_set_channel(call):
    """معالجة تعيين القناة"""
    if call.from_user.id != OWNER_ID:
        return
    
    bot.answer_callback_query(call.id, "✍️ أرسل معرف القناة الآن")
    msg = bot.send_message(call.message.chat.id, "📢 **أرسل معرف القناة:**\nمثال: `-1001234567890`\nلإلغاء الأمر أرسل `/cancel`")
    bot.register_next_step_handler(msg, process_set_channel)

def process_set_channel(message):
    """معالجة تعيين القناة"""
    global CHANNEL_ID
    
    if message.text == "/cancel":
        bot.reply_to(message, "❌ تم إلغاء التعيين.")
        return
    
    try:
        channel_id = int(message.text.strip())
        try:
            chat = bot.get_chat(channel_id)
            CHANNEL_ID = channel_id
            save_channel_setting(channel_id)
            bot.reply_to(
                message,
                f"✅ **تم تعيين القناة بنجاح!**\n"
                f"📢 اسم القناة: `{chat.title}`\n"
                f"🆔 المعرف: `{channel_id}`\n\n"
                f"🔒 سيتم نشر جميع طلبات المستخدمين هنا مع إخفاء هوياتهم."
            )
        except Exception as e:
            bot.reply_to(message, f"❌ **خطأ:** القناة غير موجودة أو البوت ليس عضواً فيها.\n{str(e)}")
    except:
        bot.reply_to(message, "❌ معرف القناة غير صالح، أرسل رقماً صحيحاً.")

@bot.callback_query_handler(func=lambda call: call.data == "channel_stats")
def handle_channel_stats(call):
    """عرض إحصائيات القناة"""
    if call.from_user.id != OWNER_ID:
        return
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM channel_posts')
    total_posts = c.fetchone()[0]
    
    c.execute('SELECT media_type, COUNT(*) FROM channel_posts GROUP BY media_type ORDER BY COUNT(*) DESC')
    media_stats = c.fetchall()
    
    c.execute('SELECT platform, COUNT(*) FROM channel_posts GROUP BY platform ORDER BY COUNT(*) DESC LIMIT 5')
    platform_stats = c.fetchall()
    conn.close()
    
    text = f"""
📊 **إحصائيات القناة**
━━━━━━━━━━━━━━━━━━━━━━━
📤 إجمالي المنشورات: `{total_posts}`

📂 **حسب النوع:**
"""
    for media_type, count in media_stats:
        text += f"   {get_media_type_emoji(media_type)} {media_type}: {count}\n"
    
    text += "\n🌐 **أكثر المنصات استخداماً:**\n"
    for platform, count in platform_stats:
        text += f"   {get_platform_emoji(platform)} {platform}: {count}\n"
    
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=["start"])
def send_welcome(message):
    user = message.from_user
    save_user(user.id, user.username, user.first_name, user.last_name)
    
    if is_user_banned(user.id):
        bot.send_message(user.id, "⛔ **أنت محظور من استخدام البوت!**")
        return
    
    unsub_list = check_all_subscriptions(user.id)
    if unsub_list:
        send_dynamic_join_request(user.id, unsub_list)
        return
    
    show_main_menu(message.chat.id, user.id)

@bot.message_handler(commands=["menu"])
def menu_command(message):
    """عرض القائمة الرئيسية"""
    if is_user_banned(message.from_user.id):
        return
    show_main_menu(message.chat.id, message.from_user.id)

@bot.message_handler(commands=["daily"])
def daily_reward(message):
    """المكافأة اليومية"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    if is_user_banned(user_id):
        return
    
    if get_daily_reward(user_id):
        update_daily_reward(user_id)
        reward_text = (
            "🎁 **تهانينا! حصلت على مكافأتك اليومية!**\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "✅ تم إضافة **5 طلبات إضافية** اليوم.\n"
            "🔹 أصبح حدك اليومي: 35 طلب.\n\n"
            "💡 عد غداً للحصول على مكافأة جديدة!"
        )
        bot.reply_to(message, reward_text, parse_mode="Markdown")
    else:
        remaining = get_remaining_requests(user_id)
        bot.reply_to(message, f"⏳ **لقد حصلت على مكافأتك اليومية بالفعل!**\n📊 الطلبات المتبقية: `{remaining}`")

@bot.message_handler(commands=["feedback"])
def feedback_command(message):
    """إرسال ملاحظة"""
    msg = bot.reply_to(message, "✍️ **أرسل ملاحظتك الآن:**\nلإلغاء الأمر أرسل `/cancel`")
    bot.register_next_step_handler(msg, process_feedback)

def process_feedback(message):
    if message.text == "/cancel":
        bot.reply_to(message, "❌ تم إلغاء الإرسال.")
        return
    
    save_feedback(message.from_user.id, message.text)
    bot.reply_to(message, "✅ **تم استلام ملاحظتك بنجاح!**\nشكراً لك. 🙏")

@bot.message_handler(commands=["rank"])
def rank_command(message):
    """عرض مستوى المستخدم"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    rank = get_user_rank(user_id)
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM stats WHERE user_id = ?', (user_id,))
    downloads = c.fetchone()[0]
    conn.close()
    
    if "إمبراطوري" in rank:
        next_rank = "👑 أنت في أعلى مستوى!"
        remaining = 0
    elif "ذهبي" in rank:
        next_rank = "👑 إمبراطوري"
        remaining = 1000 - downloads
    elif "مميز" in rank:
        next_rank = "💎 ذهبي"
        remaining = 500 - downloads
    else:
        next_rank = "⭐ مميز"
        remaining = 100 - downloads
    
    rank_text = (
        "👑 **مستواك في البوت**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"📌 المستوى الحالي: `{rank}`\n"
        f"📥 عدد التحميلات: `{downloads}`\n"
        f"🎯 المستوى التالي: `{next_rank}`\n"
        f"📊 التحميلات المتبقية: `{max(0, remaining)}`"
    )
    bot.reply_to(message, rank_text, parse_mode="Markdown")

@bot.message_handler(commands=["points"])
def points_command(message):
    """عرض نقاط المستخدم"""
    user_id = message.from_user.id
    points = get_user_points(user_id)
    bot.reply_to(
        message,
        f"⭐ **نقاطك الحالية: `{points}`**\n\n"
        f"📌 كل صورة: 1 نقطة\n"
        f"🎵 كل صوت: 2 نقطة\n"
        f"🎬 كل فيديو: 3 نقاط\n\n"
        f"🎯 استمر بالتحميل لترفع نقاطك!"
    )

@bot.message_handler(commands=["library"])
def library_command(message):
    """عرض المكتبة"""
    if is_user_banned(message.from_user.id):
        return
    posts = get_library_posts(10)
    if not posts:
        bot.reply_to(message, "📚 **المكتبة فارغة!**\nحمّل محتوى لتبدأ المكتبة.")
        return
    
    text = "📚 **أحدث المحتويات**\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    for post in posts[:5]:
        user_hash, media_type, platform, query, file_size, date = post
        text += f"{get_media_type_emoji(media_type)} **{media_type}** - {platform}\n   📝 {query[:30]}...\n   👤 {user_hash} | 📅 {date[:10]}\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    bot.reply_to(message, text)

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.chat.id != OWNER_ID:
        return
    
    total_users = get_users_count()
    active_today = get_active_users_today()
    total_downloads = get_total_downloads()
    channels_count = len(get_channels())
    remaining = get_remaining_requests(message.chat.id)
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📢 إذاعة جماعية", callback_data="broadcast_msg"),
        InlineKeyboardButton("🗑️ تعطيل القنوات", callback_data="clear_ch")
    )
    markup.add(
        InlineKeyboardButton("📊 إحصائيات", callback_data="stats_advanced"),
        InlineKeyboardButton("📋 الملاحظات", callback_data="feedback_list")
    )
    
    admin_text = (
        "👑 **لوحة التحكم الإمبراطورية**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"👥 المستخدمين: `{total_users}`\n"
        f"🟢 النشاط اليومي: `{active_today}`\n"
        f"📥 التحميلات: `{total_downloads}`\n"
        f"📢 القنوات: `{channels_count}`\n"
        f"📊 طلباتك المتبقية: `{remaining}`\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🔧 **أدوات التحكم:**"
    )
    
    bot.reply_to(message, admin_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=["ban"])
def ban_command(message):
    if message.chat.id != OWNER_ID:
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ استخدم: `/ban معرف_المستخدم`")
            return
        
        user_id = int(parts[1])
        reason = " ".join(parts[2:]) if len(parts) > 2 else "لا يوجد سبب"
        
        ban_user(user_id, reason)
        bot.reply_to(message, f"✅ تم حظر المستخدم `{user_id}`")
        try:
            bot.send_message(user_id, f"⛔ **تم حظرك من البوت!**\nالسبب: {reason}")
        except:
            pass
    except:
        bot.reply_to(message, "❌ معرف المستخدم غير صالح.")

@bot.message_handler(commands=["unban"])
def unban_command(message):
    if message.chat.id != OWNER_ID:
        return
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.reply_to(message, "❌ استخدم: `/unban معرف_المستخدم`")
            return
        
        user_id = int(parts[1])
        unban_user(user_id)
        bot.reply_to(message, f"✅ تم إلغاء حظر المستخدم `{user_id}`")
    except:
        bot.reply_to(message, "❌ معرف المستخدم غير صالح.")

@bot.message_handler(commands=["stats"])
def stats_command(message):
    if message.chat.id != OWNER_ID:
        return
    
    total_users = get_users_count()
    active_today = get_active_users_today()
    total_downloads = get_total_downloads()
    
    stats_text = (
        "📊 **إحصائيات البوت**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"👥 إجمالي المستخدمين: `{total_users}`\n"
        f"🟢 النشاط اليومي: `{active_today}`\n"
        f"📥 إجمالي التحميلات: `{total_downloads}`\n"
        f"📈 متوسط التحميل: `{round(total_downloads/max(1,total_users), 1)}`"
    )
    bot.reply_to(message, stats_text, parse_mode="Markdown")

@bot.message_handler(commands=["cancel"])
def cancel_command(message):
    if message.chat.id != OWNER_ID:
        return
    bot.reply_to(message, "❌ تم إلغاء العملية.")

def start_broadcasting(message):
    if message.text == "/cancel":
        bot.reply_to(message, "❌ تم إلغاء الإذاعة.")
        return
    
    users = []
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    users = [row[0] for row in c.fetchall()]
    conn.close()
    
    if not users:
        bot.reply_to(message, "❌ لا يوجد مستخدمين.")
        return
    
    progress = bot.send_message(OWNER_ID, f"⏳ جاري النشر لـ `{len(users)}` مستخدم...", parse_mode="Markdown")
    success = 0
    failed = 0
    
    for u_id in users:
        try:
            bot.copy_message(int(u_id), message.chat.id, message.message_id)
            success += 1
            time.sleep(0.05)
        except:
            failed += 1
    
    result_text = (
        f"✅ **تم النشر بنجاح!**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📤 تم الإرسال لـ: `{success}` مستخدم\n"
        f"❌ فشل الإرسال لـ: `{failed}` مستخدم"
    )
    bot.edit_message_text(result_text, OWNER_ID, progress.message_id, parse_mode="Markdown")

@bot.my_chat_member_handler()
def detect_channel_add(update):
    """اكتشاف إضافة البوت كادمن في قناة"""
    if update.chat.type == "channel" and update.new_chat_member.status in ["administrator", "creator"]:
        try:
            owner_status = bot.get_chat_member(update.chat.id, OWNER_ID).status
            if owner_status in ["creator", "administrator"]:
                chat_info = bot.get_chat(update.chat.id)
                save_channel(update.chat.id, chat_info.title)
                
                bot.send_message(
                    OWNER_ID,
                    f"✅ **تم تفعيل الاشتراك الإجباري لقناة جديدة!**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"📢 اسم القناة: `{chat_info.title}`\n"
                    f"🆔 معرف القناة: `{update.chat.id}`\n"
                    f"🔒 سيتم تفعيل الاشتراك الإجباري فوراً لجميع المستخدمين."
                )
                
                try:
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute('SELECT user_id FROM users WHERE last_active > datetime("now", "-1 day")')
                    active_users = c.fetchall()
                    conn.close()
                    
                    for user_id in active_users:
                        try:
                            bot.send_message(
                                user_id[0],
                                f"📢 **تم إضافة قناة جديدة للاشتراك الإجباري!**\n"
                                f"📌 يرجى الاشتراك في `{chat_info.title}` لمواصلة استخدام البوت.\n"
                                f"💡 أرسل أي كلمة أو رابط وسيظهر لك طلب الاشتراك."
                            )
                            time.sleep(0.1)
                        except:
                            pass
                except:
                    pass
        except Exception as e:
            print(f"Error detecting channel add: {e}")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user = message.from_user
    chat_id = message.chat.id
    
    if message.chat.type in ["group", "supergroup", "channel"]:
        return
    
    save_user(user.id, user.username, user.first_name, user.last_name)
    
    if is_user_banned(user.id):
        bot.send_message(chat_id, "⛔ **أنت محظور من استخدام البوت!**")
        return
    
    if not message.text:
        return
    
    text = message.text.strip()
    
    unsub_list = check_all_subscriptions(chat_id)
    if unsub_list:
        send_dynamic_join_request(chat_id, unsub_list, message.message_id)
        return
    
    if text.lower().startswith("vless://"):
        try:
            parsed = urlparse(text)
            result = (
                "🔑 **مفتاح VLESS المستخرج**\n"
                "━━━━━━━━━━━━━━━━━━━\n"
                f"🆔 UUID: `{parsed.username}`\n"
                f"🌐 Host: `{parsed.hostname}`\n"
                f"🔌 Port: `{parsed.port}`"
            )
            bot.reply_to(message, result, parse_mode="Markdown")
        except:
            bot.reply_to(message, "❌ بنية رابط vless غير مدعومة.")
        return
    
    if text.startswith("http://") or text.startswith("https://"):
        cleaned_url = clean_and_fix_url(text)
        show_link_platforms(message, cleaned_url)
    else:
        show_word_options(message, text)

def clean_temp_files():
    while True:
        try:
            if os.path.exists("downloads"):
                for file in os.listdir("downloads"):
                    file_path = os.path.join("downloads", file)
                    try:
                        if os.path.isfile(file_path):
                            file_age = time.time() - os.path.getctime(file_path)
                            if file_age > 3600:
                                os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path, ignore_errors=True)
                    except:
                        pass
        except:
            pass
        time.sleep(3600)

cleanup_thread = threading.Thread(target=clean_temp_files, daemon=True)
cleanup_thread.start()

print("=" * 60)
print("👑 تم إطلاق البوت الإمبراطوري المتطور بنجاح!")
print(f"📢 القناة المخصصة للنشر: {CHANNEL_ID}")
print("📊 نظام التشغيل: SQLite Database")
print("🛡️ نظام الحماية: Rate Limiting (30 طلب/يوم)")
print("=" * 60)

bot.infinity_polling(allowed_updates=["message", "callback_query", "my_chat_member", "channel_post"])

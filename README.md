#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                                                  ║
║                                         👑 LEGENDARY IMPERIUM PRO v15.0 👑                                                       ║
║                                                                                                                                  ║
║                     النسخة الأسطورية - تداول متعدد الأطراف الزمنية - إنذارات صوتية - إشعارات ذكية                              ║
║                                                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import json
import uuid
import sqlite3
import threading
import random
import re
import asyncio
import signal
import logging
import shutil
import subprocess
from datetime import datetime, timedelta
from io import BytesIO
from collections import deque, defaultdict
from decimal import Decimal, ROUND_HALF_UP
import warnings
warnings.filterwarnings('ignore')

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

import requests
import pandas as pd
import numpy as np
import ta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.patches import FancyBboxPatch
from matplotlib import rcParams

import edge_tts
import telebot
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)

# ============================================================
# 🔐 الإعدادات الرئيسية
# ============================================================
TELEGRAM_TOKEN = "8551852762:AAF1D_Qvg2TuCZ_d4nVFYo5lDvtPFQtDhGw"
BINANCE_API_KEY = "Z4cAj9XOSA2ahNL1VCNHsUY1yRbtMaqlA31L6TNPKSVQZsfjsTKcmbvm9tDWip1P"
BINANCE_SECRET_KEY = "3d37Pdun6FEUiajO6TinzY9jD97vL6YkPrjvZV9iqanefuDyAZV9ykScPF0G0kFO"
ADMIN_ID = 8539408138
SUPPORT_USERNAME = "@Mkdkdkd8484849bot"

BOT_NAME = "🏦 IMPERIUM PRO v15.0"
DEFAULT_TARGETS = 5
MIN_CONFIDENCE = 55
MAX_DAILY_POSTS = 10
RISK_PER_TRADE = 2.0
REWARD_RISK_RATIO = 3.0
DAILY_REPORT_HOUR = 20
LAST_COINS_MEMORY = 5
AUTO_RECO_INTERVAL_MINUTES = 20
LEARNING_MODE = True
SOUND_ENABLED = True
DEFAULT_VOICE = "ar-SA-HamedNeural"

BLACKLIST_COINS = ["UST", "LUNA", "FTT"]

# متغيرات التحكم
AUTO_SENDER_PAUSED = False
LAST_RESET_DATE = None
DAILY_SEND_COUNT = 0

# ============================================================
# 🎙️ الأصوات العربية
# ============================================================
VOICES = {
    "حامد": "ar-SA-HamedNeural",
    "زارية": "ar-SA-ZariyahNeural",
    "شاكر": "ar-EG-ShakirNeural",
    "مهند": "ar-SD-MohanadNeural",
    "سلمى": "ar-EG-SalmaNeural",
}

# ============================================================
# 📊 العملات الرئيسية (سيتم توسيعها ديناميكياً)
# ============================================================
MASTER_COINS = {
    "BTC": "BTCUSDT", "ETH": "ETHUSDT", "BNB": "BNBUSDT", "SOL": "SOLUSDT",
    "XRP": "XRPUSDT", "ADA": "ADAUSDT", "DOGE": "DOGEUSDT", "AVAX": "AVAXUSDT",
    "DOT": "DOTUSDT", "LINK": "LINKUSDT", "MATIC": "MATICUSDT", "LTC": "LTCUSDT",
    "ARB": "ARBUSDT", "OP": "OPUSDT", "NEAR": "NEARUSDT", "ATOM": "ATOMUSDT",
    "APT": "APTUSDT", "SUI": "SUIUSDT", "PEPE": "PEPEUSDT", "WIF": "WIFUSDT",
    "TRX": "TRXUSDT", "TON": "TONUSDT", "SHIB": "SHIBUSDT", "UNI": "UNIUSDT",
    "AAVE": "AAVEUSDT", "MKR": "MKRUSDT", "CRV": "CRVUSDT", "COMP": "COMPUSDT"
}

VIP_RANKS = {
    "bronze": {"signals_per_day": 5, "color": "🥉", "min_wallet": 0},
    "silver": {"signals_per_day": 10, "color": "🥈", "min_wallet": 500},
    "gold": {"signals_per_day": 20, "color": "🥇", "min_wallet": 2000},
    "platinum": {"signals_per_day": 50, "color": "💎", "min_wallet": 10000}
}

# ============================================================
# 🗄️ قاعدة البيانات المتطورة
# ============================================================
def get_db():
    return sqlite3.connect("imperium_v15.db", check_same_thread=False)

def init_database():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                chat_id INTEGER,
                join_date TEXT,
                is_banned INTEGER DEFAULT 0,
                default_targets INTEGER DEFAULT 5,
                notifications_enabled INTEGER DEFAULT 1,
                wallet_balance REAL DEFAULT 1000,
                vip_rank TEXT DEFAULT 'bronze',
                daily_signals_used INTEGER DEFAULT 0,
                last_signal_date TEXT,
                referral_code TEXT,
                referred_by INTEGER DEFAULT 0,
                total_referrals INTEGER DEFAULT 0,
                admin_level INTEGER DEFAULT 10
            );
            CREATE TABLE IF NOT EXISTS banned_channels (chat_id INTEGER PRIMARY KEY, banned_date TEXT, reason TEXT);
            CREATE TABLE IF NOT EXISTS banned_users (user_id INTEGER PRIMARY KEY, banned_date TEXT, reason TEXT);
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER, action TEXT, target_id TEXT,
                details TEXT, timestamp TEXT
            );
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY, user_id INTEGER, coin TEXT, entry_price REAL,
                position TEXT, targets TEXT, stop_loss REAL, current_target INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active', created_at TEXT, closed_at TEXT, profit_loss REAL,
                is_following INTEGER DEFAULT 0, message_id INTEGER DEFAULT 0, chat_id INTEGER DEFAULT 0,
                confidence INTEGER DEFAULT 0, signal_score INTEGER DEFAULT 0,
                entry_time TEXT, exit_time TEXT, timeframe_1h_score INTEGER DEFAULT 0,
                timeframe_4h_score INTEGER DEFAULT 0, timeframe_1d_score INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS user_follows (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, post_id INTEGER,
                coin TEXT, trade_id TEXT, follow_date TEXT, is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS analysis_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT,
                first_name TEXT, coin TEXT, request_date TEXT, status TEXT DEFAULT 'pending',
                chat_id INTEGER, message_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS channel_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, message_id INTEGER,
                coin TEXT, entry_price REAL, targets TEXT, stop_loss REAL, post_time TEXT,
                current_target INTEGER DEFAULT 0, targets_hit TEXT DEFAULT '[]',
                confidence INTEGER DEFAULT 0, is_completed INTEGER DEFAULT 0,
                trade_id TEXT, is_auto_follow INTEGER DEFAULT 1,
                entry_time TEXT, exit_time TEXT
            );
            CREATE TABLE IF NOT EXISTS active_channels (
                chat_id INTEGER PRIMARY KEY, chat_name TEXT, chat_link TEXT, added_date TEXT,
                last_post_time TEXT, last_coin TEXT, daily_posts INTEGER DEFAULT 0,
                last_post_date TEXT, is_active INTEGER DEFAULT 1, is_approved INTEGER DEFAULT 0,
                auto_send INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS bot_state (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS coin_performance (coin TEXT PRIMARY KEY, total_signals INTEGER DEFAULT 0, successful_signals INTEGER DEFAULT 0, total_profit REAL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS stats (
                user_id INTEGER PRIMARY KEY, total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0, losing_trades INTEGER DEFAULT 0,
                total_profit REAL DEFAULT 0, total_targets_hit INTEGER DEFAULT 0,
                weekly_hits INTEGER DEFAULT 0, monthly_hits INTEGER DEFAULT 0,
                last_week_update TEXT, last_month_update TEXT
            );
            CREATE TABLE IF NOT EXISTS leaderboard (
                user_id INTEGER PRIMARY KEY, username TEXT,
                weekly_hits INTEGER DEFAULT 0, monthly_hits INTEGER DEFAULT 0,
                total_hits INTEGER DEFAULT 0, last_updated TEXT
            );
            CREATE TABLE IF NOT EXISTS ai_learning (
                id INTEGER PRIMARY KEY AUTOINCREMENT, coin TEXT, indicator_name TEXT,
                weight REAL DEFAULT 1.0, total_tests INTEGER DEFAULT 0,
                successful_tests INTEGER DEFAULT 0, last_updated TEXT
            );
            CREATE TABLE IF NOT EXISTS favorite_coins (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, coin TEXT,
                added_date TEXT, UNIQUE(user_id, coin)
            );
            CREATE TABLE IF NOT EXISTS user_voice_settings (
                user_id INTEGER PRIMARY KEY, voice_name TEXT DEFAULT 'حامد',
                sound_enabled INTEGER DEFAULT 1, last_alert_time TEXT
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                title TEXT, message TEXT, created_at TEXT, is_read INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS broadcast_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER,
                message TEXT, sent_to INTEGER, sent_date TEXT
            );
            CREATE TABLE IF NOT EXISTS schedule_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER,
                time_slot TEXT, is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
                coin TEXT, target_price REAL, alert_type TEXT, created_at TEXT,
                is_triggered INTEGER DEFAULT 0
            );
        ''')
        conn.commit()
        
        indicators = ['RSI', 'MACD', 'EMA', 'ADX', 'Volume', 'Stochastic', 'Bollinger', 'CCI', 'Williams', 'MFI']
        for coin in MASTER_COINS.keys():
            for ind in indicators:
                conn.execute('INSERT OR IGNORE INTO ai_learning (coin, indicator_name, weight) VALUES (?, ?, ?)', (coin, ind, 1.0))
        
        conn.execute('INSERT OR IGNORE INTO bot_state (key, value) VALUES ("last_run", ?)', (datetime.now().isoformat(),))
        conn.execute('INSERT OR IGNORE INTO bot_state (key, value) VALUES ("total_posts", "0")')
        conn.execute('INSERT OR IGNORE INTO bot_state (key, value) VALUES ("learning_mode", "true")')
        conn.execute('INSERT OR IGNORE INTO bot_state (key, value) VALUES ("success_rate", "0")')
        conn.commit()

init_database()

# ============================================================
# 🛡️ نظام الحماية والذكاء الخارق
# ============================================================

class SecurityGuard:
    """نظام حماية متقدم لا يمكن اختراقه"""
    
    def __init__(self):
        self.suspicious_activities = defaultdict(list)
        self.request_limits = defaultdict(list)
        self.blacklisted_patterns = [
            "DROP TABLE", "DELETE FROM", "INSERT INTO", "UPDATE.*SET",
            "../", "etc/passwd", "__import__", "exec\\(", "eval\\(",
            "system\\(", "subprocess", "os\\.system", "__getattr__",
            "globals\\(\\)", "locals\\(\\)", "__builtins__"
        ]
    
    def detect_spam(self, user_id, action):
        now = datetime.now()
        self.suspicious_activities[user_id].append(now)
        self.suspicious_activities[user_id] = [
            t for t in self.suspicious_activities[user_id] 
            if (now - t).seconds < 60
        ]
        if len(self.suspicious_activities[user_id]) > 10:
            self.auto_ban(user_id, "تجاوز الحد المسموح من المحاولات")
            return True
        return False
    
    def validate_command(self, text):
        if not text:
            return True
        for pattern in self.blacklisted_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        return True
    
    def rate_limit(self, user_id, command, limit=5):
        key = f"{user_id}_{command}"
        now = datetime.now()
        self.request_limits[key] = [
            t for t in self.request_limits[key] 
            if (now - t).seconds < 60
        ]
        if len(self.request_limits[key]) >= limit:
            return False
        self.request_limits[key].append(now)
        return True
    
    def auto_ban(self, user_id, reason):
        with get_db() as conn:
            conn.execute('INSERT OR REPLACE INTO banned_users (user_id, banned_date, reason) VALUES (?, ?, ?)',
                        (user_id, datetime.now().isoformat(), f"[تلقائي] {reason}"))
            conn.commit()
        logger.warning(f"🚫 تم حظر المستخدم {user_id} تلقائياً - السبب: {reason}")

class PermissionManager:
    """نظام إدارة الصلاحيات المتقدم"""
    
    def __init__(self):
        self.roles = {
            'owner': 100,
            'super_admin': 90,
            'admin': 70,
            'moderator': 50,
            'vip_user': 20,
            'user': 10
        }
    
    def get_user_level(self, user_id):
        with get_db() as conn:
            result = conn.execute('SELECT admin_level FROM users WHERE user_id = ?', (user_id,)).fetchone()
        return result[0] if result else 10
    
    def check_permission(self, user_id, required_role):
        user_level = self.get_user_level(user_id)
        required_level = self.roles.get(required_role, 0)
        return user_level >= required_level
    
    def log_admin_action(self, admin_id, action, target_id, details):
        with get_db() as conn:
            conn.execute('''
                INSERT INTO admin_logs (admin_id, action, target_id, details, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (admin_id, action, target_id, json.dumps(details), datetime.now().isoformat()))
            conn.commit()

# ============================================================
# 🧠 نظام التحليل متعدد الأطراف الزمنية (MULTI-TIMEFRAME)
# ============================================================

class MultiTimeframeAnalyzer:
    """تحليل متقدم باستخدام 3 أطر زمنية: 1 ساعة، 4 ساعات، يومي"""
    
    def __init__(self):
        self.timeframes = {
            '1h': {'interval': '1h', 'limit': 100, 'weight': 0.3},
            '4h': {'interval': '4h', 'limit': 100, 'weight': 0.4},
            '1d': {'interval': '1d', 'limit': 100, 'weight': 0.3}
        }
    
    def analyze_all_timeframes(self, coin):
        """تحليل العملة على جميع الأطر الزمنية"""
        results = {}
        total_score = 0
        total_weight = 0
        
        for tf_name, tf_config in self.timeframes.items():
            df = binance.get_klines(coin, interval=tf_config['interval'], limit=tf_config['limit'])
            if df is not None and len(df) > 50:
                df = Analyzer.calc_indicators(df)
                price = binance.get_price(coin)
                signal = Analyzer.get_signal_score(df, price, coin)
                trend, _ = Analyzer.get_market_trend(df)
                
                results[tf_name] = {
                    'score': signal['score'],
                    'signal': signal['signal'],
                    'confidence': signal['confidence'],
                    'trend': trend,
                    'rsi': df['rsi'].iloc[-1] if 'rsi' in df.columns else 50,
                    'macd_bullish': signal['score'] > 0
                }
                
                total_score += signal['score'] * tf_config['weight']
                total_weight += tf_config['weight']
            else:
                results[tf_name] = {'score': 0, 'signal': '⚠️ بيانات غير كافية', 'confidence': 30}
        
        final_score = total_score / total_weight if total_weight > 0 else 0
        
        # تحديد التوصية النهائية بناءً على توافق الأطر الزمنية
        bullish_count = sum(1 for r in results.values() if r.get('score', 0) > 0)
        bearish_count = sum(1 for r in results.values() if r.get('score', 0) < 0)
        
        if bullish_count >= 2:
            final_signal = "🟢🔥 توصية قوية - توافق أكثر من إطار زمني 🔥🟢"
        elif bullish_count == 1:
            final_signal = "🟡📈 توصية متوسطة - توافق إطار زمني واحد 📈🟡"
        elif bearish_count >= 2:
            final_signal = "🔴⚠️ اتجاه هابط قوي - تجنب الشراء ⚠️🔴"
        else:
            final_signal = "🟡⏸ تضارب في الأطر الزمنية - انتظار وضوح ⏸🟡"
        
        return {
            'timeframes': results,
            'final_score': final_score,
            'final_signal': final_signal,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count
        }

# ============================================================
# 📢 نظام الإنذارات الصوتية والإشعارات عند الاقتراب من الأهداف
# ============================================================

class AlertSystem:
    """نظام متقدم للإنذارات الصوتية والإشعارات"""
    
    def __init__(self, bot):
        self.bot = bot
        self.last_alerts = defaultdict(dict)
        
    def check_price_proximity(self, trade_id, coin, current_price, targets, stop_loss):
        """التحقق من اقتراب السعر من الأهداف وإرسال إنذار"""
        alerts_sent = []
        
        for i, target in enumerate(targets):
            target_key = f"target_{i+1}"
            proximity_percent = abs((current_price - target) / target) * 100
            
            # إذا كان السعر على بعد أقل من 0.5% من الهدف
            if proximity_percent < 0.5:
                last_alert = self.last_alerts.get(trade_id, {}).get(target_key)
                if not last_alert or (datetime.now() - last_alert).seconds > 300:  # كل 5 دقائق
                    alerts_sent.append({
                        'type': 'proximity',
                        'target': i+1,
                        'target_price': target,
                        'distance_percent': proximity_percent
                    })
                    self.last_alerts[trade_id][target_key] = datetime.now()
        
        return alerts_sent
    
    def send_proximity_alert(self, user_id, coin, target_num, target_price, distance_percent):
        """إرسال إشعار الاقتراب من الهدف"""
        message = f"""⚠️ <b>تنبيه: اقتراب من الهدف!</b>
━━━━━━━━━━━━━━━━━━━━
💰 <b>العملة:</b> {coin}
🎯 <b>الهدف رقم:</b> {target_num}
💵 <b>سعر الهدف:</b> ${target_price:.8f}
📏 <b>المسافة المتبقية:</b> {distance_percent:.2f}%
━━━━━━━━━━━━━━━━━━━━
🚀 استعد لتحقيق الهدف قريباً!"""
        
        try:
            self.bot.send_message(user_id, message, parse_mode='HTML')
            if SOUND_ENABLED:
                voice_text = f"تنبيه مهم. عملة {coin} تقترب من الهدف رقم {target_num}"
                send_voice_message(self.bot, user_id, voice_text)
        except Exception as e:
            logger.error(f"خطأ في إرسال إنذار الاقتراب: {e}")
    
    def send_target_hit_alert(self, user_id, coin, target_num, current_price, profit_percent):
        """إرسال إنذار تحقيق الهدف مع صوت"""
        message = f"""🎉 <b>تهانينا! تم تحقيق الهدف!</b> 🎉
━━━━━━━━━━━━━━━━━━━━
💰 <b>العملة:</b> {coin}
🎯 <b>الهدف رقم:</b> {target_num}
💵 <b>السعر المحقق:</b> ${current_price:.8f}
📈 <b>الربح المحقق:</b> +{profit_percent:.2f}%
━━━━━━━━━━━━━━━━━━━━
🏆 استمر في المتابعة لتحقيق باقي الأهداف!"""
        
        try:
            self.bot.send_message(user_id, message, parse_mode='HTML')
            if SOUND_ENABLED:
                voice_text = f"تهانينا. تم تحقيق الهدف رقم {target_num} لعملة {coin} بربح {profit_percent:.1f} بالمئة"
                send_voice_message(self.bot, user_id, voice_text, get_user_voice(user_id))
        except Exception as e:
            logger.error(f"خطأ في إرسال إنذار تحقيق الهدف: {e}")

# ============================================================
# 🔌 Binance Client المطور
# ============================================================
class BinanceClient:
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        self.symbols_cache = {}
        self.load_all_symbols()
        logger.info("✅ تم الاتصال بـ Binance")

    def load_all_symbols(self):
        try:
            response = requests.get(f"{self.base_url}/exchangeInfo", timeout=10)
            data = response.json()
            all_symbols = [s['symbol'] for s in data['symbols'] if s['status'] == 'TRADING' and s['symbol'].endswith('USDT')]
            for s in all_symbols:
                self.symbols_cache[s.replace('USDT', '').upper()] = s
            logger.info(f"✅ تم تحميل {len(all_symbols)} عملة")
        except Exception as e:
            logger.error(f"خطأ في تحميل العملات: {e}")
            for coin, symbol in MASTER_COINS.items():
                self.symbols_cache[coin] = symbol

    def search_coin(self, query):
        """بحث متقدم لأي عملة في بينانس (أكثر من 1500 عملة)"""
        if not query:
            return None, None
        query = query.upper().strip().replace('USDT', '')
        
        if query in self.symbols_cache:
            return self.symbols_cache[query], query
        
        for coin, symbol in self.symbols_cache.items():
            if query in coin or coin in query:
                return symbol, coin
        
        try:
            response = requests.get(f"{self.base_url}/exchangeInfo", timeout=10)
            data = response.json()
            all_symbols = [s['symbol'] for s in data['symbols'] 
                          if s['status'] == 'TRADING' and s['symbol'].endswith('USDT')]
            for symbol in all_symbols:
                coin_name = symbol.replace('USDT', '')
                self.symbols_cache[coin_name] = symbol
                if query in coin_name or coin_name in query:
                    return symbol, coin_name
        except Exception as e:
            logger.error(f"خطأ في تحديث الكاش: {e}")
        
        return None, None

    def get_klines(self, coin, interval="1h", limit=200):
        try:
            symbol = self.search_coin(coin)[0]
            if not symbol:
                return None
            params = {'symbol': symbol, 'interval': interval, 'limit': limit}
            response = requests.get(f"{self.base_url}/klines", params=params, timeout=10)
            data = response.json()
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                              'close_time', 'qav', 'trades', 'tb_base', 'tb_quote', 'ignore'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            return df
        except Exception as e:
            logger.error(f"خطأ في جلب البيانات: {e}")
            return None

    def get_price(self, coin):
        try:
            symbol = self.search_coin(coin)[0]
            if symbol:
                response = requests.get(f"{self.base_url}/ticker/price", params={'symbol': symbol}, timeout=5)
                return float(response.json()['price'])
        except Exception:
            pass
        return 0.0

    def get_24hr_change(self, coin):
        try:
            symbol = self.search_coin(coin)[0]
            if symbol:
                response = requests.get(f"{self.base_url}/ticker/24hr", params={'symbol': symbol}, timeout=5)
                return float(response.json()['priceChangePercent'])
        except Exception:
            pass
        return 0.0

binance = BinanceClient()

# ============================================================
# 📈 التحليل الفني المتقدم
# ============================================================
class Analyzer:
    @staticmethod
    def calc_indicators(df):
        if df is None or len(df) < 50:
            return df
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_hist'] = macd.macd_diff()
        df['ema9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
        df['ema21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
        df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
        df['ema200'] = ta.trend.EMAIndicator(df['close'], window=200).ema_indicator()
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
        df['atr_percent'] = (df['atr'] / df['close']) * 100
        adx_ind = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
        df['adx'] = adx_ind.adx()
        df['plus_di'] = adx_ind.adx_pos()
        df['minus_di'] = adx_ind.adx_neg()
        bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
        df['bb_high'] = bb.bollinger_hband()
        df['bb_mid'] = bb.bollinger_mavg()
        df['bb_low'] = bb.bollinger_lband()
        df['bb_width'] = (df['bb_high'] - df['bb_low']) / df['bb_mid'] * 100
        df['bb_position'] = (df['close'] - df['bb_low']) / (df['bb_high'] - df['bb_low'])
        stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()
        df['volume_sma'] = ta.trend.SMAIndicator(df['volume'], window=20).sma_indicator()
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        df['williams_r'] = ta.momentum.WilliamsRIndicator(df['high'], df['low'], df['close'], lbp=14).williams_r()
        df['cci'] = ta.trend.CCIIndicator(df['high'], df['low'], df['close'], window=20).cci()
        df['mfi'] = ta.volume.MFIIndicator(df['high'], df['low'], df['close'], df['volume'], window=14).money_flow_index()
        return df

    @staticmethod
    def get_signal_score(df, price, coin=None):
        if df is None or len(df) < 50:
            return {'score': 0, 'signal': '⏸ مراقبة', 'confidence': 50, 'details': {}}
        last = df.iloc[-1]
        score = 0
        details = {}
        
        rsi = last['rsi'] if not pd.isna(last['rsi']) else 50
        if rsi < 25:
            score += 20
        elif rsi < 30:
            score += 15
        elif rsi < 35:
            score += 8
        elif rsi > 75:
            score -= 20
        elif rsi > 70:
            score -= 15
        elif rsi > 65:
            score -= 8
        
        if not pd.isna(last['macd']) and not pd.isna(last['macd_signal']):
            if last['macd'] > last['macd_signal'] and last['macd_hist'] > 0:
                score += 25
            elif last['macd'] > last['macd_signal']:
                score += 15
            elif last['macd'] < last['macd_signal'] and last['macd_hist'] < 0:
                score -= 25
            elif last['macd'] < last['macd_signal']:
                score -= 15
        
        if last['ema9'] > last['ema21']:
            score += 6
        if last['ema21'] > last['ema50']:
            score += 6
        if last['ema50'] > last['ema200']:
            score += 8
        else:
            score -= 6
        
        adx = last['adx'] if not pd.isna(last['adx']) else 0
        if adx > 40:
            score += 15 if last['plus_di'] > last['minus_di'] else -15
        elif adx > 25:
            score += 10 if last['plus_di'] > last['minus_di'] else -10
        
        if not pd.isna(last['bb_position']):
            if last['bb_position'] < 0.1:
                score += 10
            elif last['bb_position'] < 0.2:
                score += 6
            elif last['bb_position'] > 0.9:
                score -= 10
            elif last['bb_position'] > 0.8:
                score -= 6
        
        if not pd.isna(last['stoch_k']):
            if last['stoch_k'] < 20:
                score += 10
            elif last['stoch_k'] < 30:
                score += 5
            elif last['stoch_k'] > 80:
                score -= 10
            elif last['stoch_k'] > 70:
                score -= 5
        
        if not pd.isna(last['volume_ratio']):
            if last['volume_ratio'] > 2:
                score += 10 if score > 0 else -10
            elif last['volume_ratio'] > 1.5:
                score += 7 if score > 0 else -7
        
        if not pd.isna(last['mfi']):
            if last['mfi'] < 20:
                score += 8
            elif last['mfi'] > 80:
                score -= 8
        
        if score >= 50:
            signal = '🟢🔥 صاروخ صاعد - شراء قوي 🔥🟢'
        elif score >= 30:
            signal = '🟢✅ شراء ذكي ✅🟢'
        elif score >= 15:
            signal = '🟡📈 احتمالية صعود 📈🟡'
        elif score <= -50:
            signal = '🔴⚠️ قنابل هابطة - بيع قوي ⚠️🔴'
        elif score <= -30:
            signal = '🔴🔻 بيع وقائي 🔻🔴'
        elif score <= -15:
            signal = '🔴📉 احتمالية هبوط 📉🔴'
        else:
            signal = '🟡⏸ انتظار ومراقبة ⏸🟡'
        
        confidence = min(98, 50 + abs(score) // 2)
        return {'score': score, 'signal': signal, 'confidence': confidence, 'details': details}

    @staticmethod
    def calculate_dynamic_targets(price, score, num_targets):
        targets = []
        if price < 0.001:
            base_step = price * 0.15
        elif price < 0.01:
            base_step = price * 0.10
        elif price < 0.1:
            base_step = price * 0.08
        else:
            base_step = price * 0.02
        multipliers = [1.0, 1.8, 2.5, 3.2, 4.0, 4.8, 5.5]
        for i in range(min(num_targets, len(multipliers))):
            targets.append(round(price + (base_step * multipliers[i]), 8))
        return targets[:num_targets]

    @staticmethod
    def calculate_smart_stop_loss(price, score, atr_percent, trend):
        if score >= 50:
            stop_percent = 0.025
        elif score >= 30:
            stop_percent = 0.035
        else:
            stop_percent = 0.045
        if "هابط" in trend:
            stop_percent *= 1.2
        if atr_percent > 5:
            stop_percent *= 1.3
        if price < 0.001:
            stop_percent = 0.12
        elif price < 0.01:
            stop_percent = 0.08
        return round(price * (1 - stop_percent), 8)

    @staticmethod
    def get_market_trend(df):
        if df is None or len(df) < 50:
            return "عرضي", 50
        last = df.iloc[-1]
        if last['ema9'] > last['ema21'] > last['ema50'] > last['ema200']:
            return "🟢 صاعد قوي 🟢", 85
        elif last['ema9'] > last['ema21'] > last['ema50']:
            return "🟢 صاعد 🟢", 70
        elif last['ema9'] < last['ema21'] < last['ema50'] < last['ema200']:
            return "🔴 هابط قوي 🔴", 15
        elif last['ema9'] < last['ema21'] < last['ema50']:
            return "🔴 هابط 🔴", 30
        return "🟡 عرضي 🟡", 50

    @staticmethod
    def get_best_coin(exclude_coins=[]):
        best_score = -999
        best_coin = None
        best_data = None
        for coin in MASTER_COINS.keys():
            if coin in exclude_coins or coin in BLACKLIST_COINS:
                continue
            df = binance.get_klines(coin, interval="1h", limit=100)
            if df is None:
                continue
            df = Analyzer.calc_indicators(df)
            price = binance.get_price(coin)
            if price == 0:
                continue
            signal = Analyzer.get_signal_score(df, price, coin)
            score = signal['score']
            if score > best_score:
                best_score = score
                best_coin = coin
                best_data = {'df': df, 'price': price, 'signal': signal}
        return best_coin, best_data

# ============================================================
# 🧠 نظام الثقة المتقدم (Advanced Confidence)
# ============================================================

class AdvancedConfidence:
    """نظام الثقة المتقدم - يجمع بين المؤشرات والتاريخ والتحليل"""
    
    @staticmethod
    def calculate_real_confidence(df, price, coin):
        """حساب الثقة الحقيقية بنسبة مئوية دقيقة"""
        if df is None or len(df) < 50:
            return {'confidence': 50, 'risk_score': 50, 'details': {}, 'is_safe': True}
        
        last = df.iloc[-1]
        weights = {
            'rsi': 15,
            'macd': 20,
            'ema': 15,
            'adx': 15,
            'volume': 10,
            'stochastic': 10,
            'bollinger': 10,
            'mfi': 5
        }
        
        score = 0
        max_score = sum(weights.values())
        details = {}
        
        # RSI
        rsi = last.get('rsi', 50)
        if not pd.isna(rsi):
            if 30 <= rsi <= 70:
                rsi_score = 10
            elif 20 <= rsi < 30 or 70 < rsi <= 80:
                rsi_score = 5
            else:
                rsi_score = 0
            score += (rsi_score / 10) * weights['rsi']
            details['RSI'] = f"{rsi:.1f}"
        
        # MACD
        macd = last.get('macd', 0)
        macd_signal = last.get('macd_signal', 0)
        if not pd.isna(macd) and not pd.isna(macd_signal):
            if macd > macd_signal and last.get('macd_hist', 0) > 0:
                macd_score = 10
            elif macd > macd_signal:
                macd_score = 7
            elif macd < macd_signal:
                macd_score = 3
            else:
                macd_score = 5
            score += (macd_score / 10) * weights['macd']
            details['MACD'] = "صاعد" if macd > macd_signal else "هابط"
        
        # EMA Trend
        ema9 = last.get('ema9', price)
        ema21 = last.get('ema21', price)
        ema50 = last.get('ema50', price)
        if ema9 > ema21 > ema50:
            ema_score = 10
        elif ema9 > ema21:
            ema_score = 7
        elif ema9 < ema21 < ema50:
            ema_score = 2
        elif ema9 < ema21:
            ema_score = 4
        else:
            ema_score = 5
        score += (ema_score / 10) * weights['ema']
        details['الاتجاه'] = "صاعد" if ema9 > ema21 else "هابط"
        
        # ADX
        adx = last.get('adx', 20)
        if not pd.isna(adx):
            if adx > 40:
                adx_score = 10
            elif adx > 25:
                adx_score = 7
            elif adx > 20:
                adx_score = 5
            else:
                adx_score = 3
            score += (adx_score / 10) * weights['adx']
            details['ADX'] = f"{adx:.1f}"
        
        # Volume
        volume_ratio = last.get('volume_ratio', 1)
        if not pd.isna(volume_ratio):
            if volume_ratio > 2:
                vol_score = 10
            elif volume_ratio > 1.5:
                vol_score = 8
            elif volume_ratio > 1:
                vol_score = 6
            elif volume_ratio > 0.5:
                vol_score = 4
            else:
                vol_score = 2
            score += (vol_score / 10) * weights['volume']
            details['الحجم'] = f"{volume_ratio:.1f}x"
        
        # Stochastic
        stoch_k = last.get('stoch_k', 50)
        if not pd.isna(stoch_k):
            if stoch_k < 20:
                stoch_score = 9
            elif stoch_k < 30:
                stoch_score = 7
            elif stoch_k > 80:
                stoch_score = 3
            else:
                stoch_score = 5
            score += (stoch_score / 10) * weights['stochastic']
        
        # Bollinger Bands
        bb_position = last.get('bb_position', 0.5)
        if not pd.isna(bb_position):
            if bb_position < 0.2:
                bb_score = 9
            elif bb_position < 0.3:
                bb_score = 7
            elif bb_position > 0.8:
                bb_score = 3
            else:
                bb_score = 5
            score += (bb_score / 10) * weights['bollinger']
        
        # MFI
        mfi = last.get('mfi', 50)
        if not pd.isna(mfi):
            if mfi < 20:
                mfi_score = 9
            elif mfi > 80:
                mfi_score = 2
            else:
                mfi_score = 5
            score += (mfi_score / 10) * weights['mfi']
        
        # حساب النسبة المئوية النهائية
        final_confidence = (score / max_score) * 100
        final_confidence = max(30, min(98, final_confidence))
        
        # حساب درجة المخاطرة
        risk_score = 100 - final_confidence
        atr_percent = last.get('atr_percent', 2)
        if atr_percent > 5:
            risk_score += 15
        if volume_ratio < 0.5:
            risk_score += 10
        risk_score = min(100, risk_score)
        
        is_safe = risk_score < 60 and final_confidence >= 60
        
        return {
            'confidence': round(final_confidence, 1),
            'risk_score': round(risk_score, 1),
            'details': details,
            'is_safe': is_safe,
            'recommendation': '🟢 آمن للتداول' if is_safe else '⚠️高风险 أو ثقة منخفضة'
        }

# ============================================================
# 🎙️ دوال الأصوات ونطق الأرقام
# ============================================================
def format_number_for_speech(num):
    if num is None:
        return "صفر"
    try:
        num = float(num)
    except Exception:
        return str(num)
    
    integer_part = int(num)
    decimal_part = int(round((num - integer_part) * 100, 0))
    
    if integer_part == 0 and decimal_part == 0:
        return "صفر"
    
    ones = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"]
    tens = ["", "عشرة", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"]
    hundreds = ["", "مئة", "مئتان", "ثلاثمئة", "أربعمئة", "خمسمئة", "ستمئة", "سبعمئة", "ثمانمئة", "تسعمئة"]
    units = ["", "ألف", "مليون", "مليار", "تريليون"]
    
    def convert_three(n):
        if n == 0:
            return ""
        result = ""
        if n >= 100:
            result += hundreds[n // 100] + " "
            n %= 100
        if n >= 20:
            result += tens[n // 10] + " "
            n %= 10
        if n > 0:
            result += ones[n] + " "
        return result.strip()
    
    result = ""
    if integer_part > 0:
        temp = integer_part
        i = 0
        while temp > 0:
            seg = temp % 1000
            if seg > 0:
                seg_text = convert_three(seg)
                if i > 0:
                    seg_text += " " + units[i]
                result = seg_text + " " + result
            temp //= 1000
            i += 1
        result = result.strip()
    else:
        result = "صفر"
    
    if decimal_part > 0:
        if decimal_part < 10:
            result += " فاصلة " + ones[decimal_part]
        else:
            d1 = decimal_part // 10
            d2 = decimal_part % 10
            if d1 == 1:
                result += " فاصلة " + (ones[d2] + " عشرة" if d2 > 0 else "عشرة")
            else:
                result += " فاصلة " + (tens[d1] if d1 > 0 else "") + " " + ones[d2]
    
    return result.strip()

def format_price_for_speech(price):
    if price < 1:
        cents = int(price * 100)
        return f"{format_number_for_speech(cents)} سنت"
    elif price < 1000:
        dollars = int(price)
        cents = int((price - dollars) * 100)
        if cents > 0:
            return f"{format_number_for_speech(dollars)} دولار و {format_number_for_speech(cents)} سنت"
        else:
            return f"{format_number_for_speech(dollars)} دولار"
    elif price < 1000000:
        thousands = int(price / 1000)
        remaining = int(price % 1000)
        if remaining > 0:
            return f"{format_number_for_speech(thousands)} ألف و {format_number_for_speech(remaining)} دولار"
        else:
            return f"{format_number_for_speech(thousands)} ألف دولار"
    else:
        millions = int(price / 1000000)
        return f"{format_number_for_speech(millions)} مليون دولار"

def format_percent_for_speech(percent):
    abs_percent = abs(percent)
    if abs_percent >= 100:
        return f"{format_number_for_speech(int(percent))} بالمئة"
    elif abs_percent >= 1:
        return f"{format_number_for_speech(int(percent))} فاصلة {int((abs_percent - int(abs_percent)) * 10)} بالمئة"
    else:
        return f"{format_number_for_speech(int(percent * 100))} فاصلة {int((percent * 100 - int(percent * 100)) * 10)} بالمئة"

async def text_to_speech(text, voice=DEFAULT_VOICE, output_file="output.mp3"):
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        return output_file
    except Exception as e:
        logger.error(f"خطأ في تحويل النص إلى صوت: {e}")
        return None

def send_voice_message(bot, chat_id, text, voice_name=None):
    if not SOUND_ENABLED:
        return None
    try:
        voice = VOICES.get(voice_name, DEFAULT_VOICE) if voice_name else DEFAULT_VOICE
        output_file = f"voice_{uuid.uuid4().hex[:8]}.mp3"
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(text_to_speech(text, voice, output_file))
        loop.close()
        if result and os.path.exists(output_file):
            with open(output_file, 'rb') as audio:
                bot.send_voice(chat_id, audio)
            os.remove(output_file)
            return True
    except Exception as e:
        logger.error(f"خطأ في إرسال الصوت: {e}")
    return False

# ============================================================
# 🎨 الرسم البياني المتقدم
# ============================================================
class ChartMaker:
    @staticmethod
    def create(coin, df, price, signal, targets, sl, score, trend, entry_time=None, exit_time=None):
        try:
            fig = plt.figure(figsize=(16, 12), facecolor='#0a0e1a')
            ax1 = fig.add_axes([0.05, 0.35, 0.9, 0.55])
            ax1.set_facecolor('#0a0e1a')
            recent = df.tail(100)
            for i, (idx, row) in enumerate(recent.iterrows()):
                color = '#00ff88' if row['close'] >= row['open'] else '#ff4444'
                body_h = abs(row['close'] - row['open'])
                body_b = min(row['close'], row['open'])
                ax1.add_patch(Rectangle((i - 0.35, body_b), 0.7, body_h, facecolor=color, edgecolor=color, linewidth=1))
                ax1.plot([i, i], [row['high'], max(row['close'], row['open'])], color=color, linewidth=1)
                ax1.plot([i, i], [min(row['close'], row['open']), row['low']], color=color, linewidth=1)
            if 'ema9' in recent.columns:
                ax1.plot(range(len(recent)), recent['ema9'].values, '--', color='#ffb347', lw=1.5, label='EMA 9', alpha=0.8)
            if 'ema21' in recent.columns:
                ax1.plot(range(len(recent)), recent['ema21'].values, '--', color='#ff6b6b', lw=1.5, label='EMA 21', alpha=0.8)
            if 'ema50' in recent.columns:
                ax1.plot(range(len(recent)), recent['ema50'].values, '--', color='#4ecdc4', lw=1.5, label='EMA 50', alpha=0.8)
            
            tcolor = '#00ff88' if 'شراء' in signal else '#ff4444'
            for i, t in enumerate(targets):
                ax1.axhline(y=t, color=tcolor, ls='--', alpha=0.5, lw=1)
                ax1.text(len(recent)-5, t, f'Target {i+1}', color=tcolor, fontsize=9)
            ax1.axhline(y=sl, color='#ff4444', ls='--', lw=2, alpha=0.8)
            ax1.text(len(recent)-5, sl, 'STOP LOSS', color='#ff4444', fontsize=10, weight='bold')
            ax1.axhline(y=price, color='white', ls='-', lw=1, alpha=0.3)
            
            # إضافة وقت الدخول والخروج على الرسم البياني
            if entry_time:
                ax1.text(2, price * 0.98, f"⏰ دخول: {entry_time}", color='#00ff88', fontsize=10, weight='bold')
            if exit_time:
                ax1.text(2, price * 0.95, f"⏰ خروج: {exit_time}", color='#ff4444', fontsize=10, weight='bold')
            
            ax1.set_title(f'{coin}/USDT | {signal} | Score: {score} | {trend}', color='white', fontsize=14, weight='bold')
            ax1.legend(loc='upper left', facecolor='#0a0e1a', labelcolor='white')
            ax1.grid(True, alpha=0.15)
            ax1.set_xticks([])
            ax1.tick_params(colors='white')
            
            ax2 = fig.add_axes([0.05, 0.20, 0.9, 0.12])
            ax2.set_facecolor('#0a0e1a')
            if 'rsi' in recent.columns:
                ax2.plot(range(len(recent)), recent['rsi'].values, color='#ffb347', lw=1.5)
                ax2.axhline(y=70, color='#ff4444', ls='--', alpha=0.5)
                ax2.axhline(y=30, color='#00ff88', ls='--', alpha=0.5)
                ax2.fill_between(range(len(recent)), 30, 70, alpha=0.1, color='white')
            ax2.set_title('RSI (14)', color='white', fontsize=9)
            ax2.set_ylim(0, 100)
            ax2.tick_params(colors='white')
            ax2.grid(True, alpha=0.15)
            
            ax3 = fig.add_axes([0.05, 0.10, 0.9, 0.08])
            ax3.set_facecolor('#0a0e1a')
            if 'macd' in recent.columns:
                ax3.plot(range(len(recent)), recent['macd'].values, color='#00ff88', lw=1, label='MACD')
                ax3.plot(range(len(recent)), recent['macd_signal'].values, color='#ff4444', lw=1, label='Signal')
                ax3.bar(range(len(recent)), recent['macd_hist'].values, color='#ffb347', alpha=0.5, width=0.8)
            ax3.set_title('MACD', color='white', fontsize=9)
            ax3.tick_params(colors='white')
            ax3.legend(loc='upper left', facecolor='#0a0e1a', labelcolor='white')
            ax3.grid(True, alpha=0.15)
            
            ax4 = fig.add_axes([0.05, 0.03, 0.9, 0.05])
            ax4.set_facecolor('#0a0e1a')
            vols = recent['volume'].values
            vcolors = ['#00ff88' if recent['close'].iloc[i] >= recent['open'].iloc[i] else '#ff4444' for i in range(len(vols))]
            ax4.bar(range(len(vols)), vols, color=vcolors, alpha=0.7, width=0.8)
            ax4.set_title('Volume', color='white', fontsize=9)
            ax4.tick_params(colors='white')
            ax4.grid(True, alpha=0.15)
            
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=100, facecolor='#0a0e1a', bbox_inches='tight')
            buf.seek(0)
            plt.close()
            return buf
        except Exception as e:
            logger.error(f"Chart error: {e}")
            return None

# ============================================================
# 📊 إدارة الصفقات المتقدمة مع الإنذارات
# ============================================================
class TradeManager:
    @staticmethod
    def create(user_id, coin, price, action, targets, sl, chat_id=0, message_id=0, score=0):
        trade_id = str(uuid.uuid4())[:8]
        entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_db() as conn:
            conn.execute('''INSERT INTO trades 
                (trade_id, user_id, coin, entry_price, position, targets, stop_loss, current_target, status, created_at, message_id, chat_id, confidence, signal_score, entry_time) 
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, "active", ?, ?, ?, ?, ?, ?)''', 
                (trade_id, user_id, coin, price, action, json.dumps(targets), sl, datetime.now().isoformat(), message_id, chat_id, score, score, entry_time))
            conn.execute('INSERT OR IGNORE INTO stats (user_id) VALUES (?)', (user_id,))
            conn.execute('UPDATE stats SET total_trades = total_trades + 1 WHERE user_id = ?', (user_id,))
            conn.commit()
        return trade_id

    @staticmethod
    def monitor(bot):
        alert_system = AlertSystem(bot)
        while True:
            try:
                with get_db() as conn:
                    trades = conn.execute('''SELECT trade_id, user_id, coin, entry_price, position, targets, current_target, stop_loss, chat_id, message_id, entry_time
                                            FROM trades WHERE status = "active"''').fetchall()
                    for trade_id, user_id, coin, entry, pos, targets_json, curr_t, sl, chat_id, msg_id, entry_time in trades:
                        targets = json.loads(targets_json)
                        current_price = binance.get_price(coin)
                        if current_price == 0:
                            continue
                        total_targets = len(targets)
                        
                        # التحقق من الاقتراب من الأهداف
                        proximity_alerts = alert_system.check_price_proximity(trade_id, coin, current_price, targets, sl)
                        for alert in proximity_alerts:
                            if user_id != 0:
                                alert_system.send_proximity_alert(user_id, coin, alert['target'], alert['target_price'], alert['distance_percent'])
                        
                        if pos in ['buy', 'strong_buy', 'weak_buy', 'STRONG_BUY', 'BUY']:
                            if current_price <= sl:
                                loss = entry - current_price
                                exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                conn.execute('UPDATE trades SET status = "closed", closed_at = ?, profit_loss = ?, exit_time = ? WHERE trade_id = ?', 
                                            (datetime.now().isoformat(), -loss, exit_time, trade_id))
                                conn.execute('UPDATE stats SET losing_trades = losing_trades + 1 WHERE user_id = ?', (user_id,))
                                if chat_id:
                                    bot.send_message(chat_id, f"🔴 تم تفعيل وقف الخسارة!\n💰 {coin}\n📉 السعر: ${current_price:.6f}\n⏰ وقت الخروج: {exit_time}")
                                continue
                            
                            for i, t in enumerate(targets, 1):
                                if current_price >= t and curr_t < i:
                                    profit_percent = ((current_price - entry) / entry) * 100
                                    exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    conn.execute('UPDATE trades SET current_target = ?, exit_time = ? WHERE trade_id = ?', (i, exit_time, trade_id))
                                    conn.commit()
                                    
                                    # إرسال إنذار تحقيق الهدف
                                    if user_id != 0:
                                        alert_system.send_target_hit_alert(user_id, coin, i, current_price, profit_percent)
                                    
                                    followers = conn.execute('SELECT user_id FROM user_follows WHERE trade_id = ? AND is_active = 1', (trade_id,)).fetchall()
                                    for follower in followers:
                                        try:
                                            bot.send_message(follower[0], f"🎯 تم تحقيق الهدف {i}!\n💰 العملة: {coin}\n🎯 السعر: ${t:.8f}\n💵 السعر الحالي: ${current_price:.8f}\n📊 الأهداف المتبقية: {total_targets - i}\n⏰ وقت الخروج: {exit_time}")
                                            if SOUND_ENABLED:
                                                send_voice_message(bot, follower[0], f"تهانينا. تم تحقيق الهدف {i} لعملة {coin}")
                                        except Exception:
                                            pass
                                    
                                    if chat_id:
                                        bot.send_message(chat_id, f"✅ تم تحقيق الهدف {i}!\n💰 {coin}\n🎯 السعر: ${t:.6f}\n⏰ الوقت: {exit_time}")
                                    
                                    with get_db() as conn2:
                                        conn2.execute('UPDATE stats SET total_targets_hit = total_targets_hit + 1, weekly_hits = weekly_hits + 1 WHERE user_id = ?', (user_id,))
                                        conn2.execute('UPDATE leaderboard SET weekly_hits = weekly_hits + 1, total_hits = total_hits + 1 WHERE user_id = ?', (user_id,))
                                        conn2.commit()
                                    
                                    if i == total_targets:
                                        profit = current_price - entry
                                        conn.execute('UPDATE trades SET status = "closed", closed_at = ?, profit_loss = ? WHERE trade_id = ?', 
                                                    (datetime.now().isoformat(), profit, trade_id))
                                        conn.execute('UPDATE stats SET winning_trades = winning_trades + 1, total_profit = total_profit + ? WHERE user_id = ?', (profit, user_id))
                                        if chat_id:
                                            bot.send_message(chat_id, f"🏆 تم تحقيق جميع الأهداف!\n💰 {coin}\n📈 الربح: ${profit:.6f}\n⏰ وقت الإغلاق: {exit_time}")
                                    break
                time.sleep(30)
            except Exception as e:
                logger.error(f"خطأ في مراقبة الصفقات: {e}")
                time.sleep(30)

# ============================================================
# 🤖 البوت الرئيسي - النسخة الأسطورية
# ============================================================
bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode='HTML')
recent_coins = deque(maxlen=LAST_COINS_MEMORY)
channel_threads = {}

# تفعيل أنظمة الحماية والذكاء
security = SecurityGuard()
permissions = PermissionManager()
multi_tf_analyzer = MultiTimeframeAnalyzer()
alert_system = AlertSystem(bot)
backup_system = None  # سيتم تفعيله لاحقاً
scheduler = None  # سيتم تفعيله لاحقاً

# ============================================================
# الدوال المساعدة
# ============================================================
def is_channel_banned(chat_id):
    with get_db() as conn:
        return conn.execute('SELECT 1 FROM banned_channels WHERE chat_id = ?', (chat_id,)).fetchone() is not None

def is_user_banned(user_id):
    with get_db() as conn:
        return conn.execute('SELECT 1 FROM banned_users WHERE user_id = ?', (user_id,)).fetchone() is not None

def get_user_voice(user_id):
    with get_db() as conn:
        result = conn.execute('SELECT voice_name FROM user_voice_settings WHERE user_id = ?', (user_id,)).fetchone()
        return result[0] if result else "حامد"

def add_notification(user_id, title, message):
    with get_db() as conn:
        conn.execute('INSERT INTO notifications (user_id, title, message, created_at) VALUES (?, ?, ?, ?)',
                    (user_id, title, message, datetime.now().isoformat()))
        conn.commit()

def get_user_stats_text(user_id):
    with get_db() as conn:
        stats = conn.execute('''SELECT total_trades, winning_trades, losing_trades, total_profit, total_targets_hit 
                                FROM stats WHERE user_id = ?''', (user_id,)).fetchone()
        if stats and stats[0] > 0:
            total, wins, losses, profit, targets = stats
            rate = (wins / total * 100) if total > 0 else 0
            return f"""📊 <b>إحصائياتك الشخصية</b>
━━━━━━━━━━━━━━━━━━━━
📈 <b>عدد الصفقات:</b> {total}
✅ <b>الرابحة:</b> {wins}
❌ <b>الخاسرة:</b> {losses}
🎯 <b>نسبة النجاح:</b> {rate:.1f}%
💰 <b>الربح الإجمالي:</b> ${profit:.4f}
🏆 <b>الأهداف المحققة:</b> {targets}
━━━━━━━━━━━━━━━━━━━━"""
        return "📭 <b>لا توجد إحصائيات بعد</b>\nقم بمتابعة الإشارات لتبدأ"

def send_recommendation_to_channel(chat_id):
    try:
        if is_channel_banned(chat_id):
            return False
        
        coin, data = Analyzer.get_best_coin(list(recent_coins))
        if not coin or not data:
            return False
        
        df = data['df']
        price = data['price']
        signal = data['signal']
        score = signal['score']
        
        if signal['confidence'] < MIN_CONFIDENCE:
            return False
        
        # التحليل متعدد الأطراف الزمنية
        mtf_analysis = multi_tf_analyzer.analyze_all_timeframes(coin)
        
        atr = df['atr'].iloc[-1] if 'atr' in df.columns else price * 0.01
        atr_percent = (atr / price) * 100
        trend, _ = Analyzer.get_market_trend(df)
        targets = Analyzer.calculate_dynamic_targets(price, score, DEFAULT_TARGETS)
        sl = Analyzer.calculate_smart_stop_loss(price, score, atr_percent, trend)
        
        # حساب أوقات الدخول والخروج المقترحة
        entry_time = datetime.now()
        entry_time_str = entry_time.strftime("%Y-%m-%d %H:%M:%S")
        # وقت الخروج المقترح بناءً على الأطراف الزمنية
        if mtf_analysis['bullish_count'] >= 2:
            estimated_exit = entry_time + timedelta(hours=24)
        else:
            estimated_exit = entry_time + timedelta(hours=12)
        exit_time_str = estimated_exit.strftime("%Y-%m-%d %H:%M:%S")
        
        chart = ChartMaker.create(coin, df, price, signal['signal'], targets, sl, score, trend, entry_time_str, exit_time_str)
        
        # عرض تحليل الأطراف الزمنية
        tf_text = ""
        for tf, result in mtf_analysis['timeframes'].items():
            emoji = "🟢" if result.get('score', 0) > 0 else "🔴" if result.get('score', 0) < 0 else "🟡"
            tf_text += f"{emoji} {tf}: {result.get('signal', 'مراقبة')[:20]}\n"
        
        targets_text = "\n".join([f"🎯 الهدف {i+1}: <code>${t:.8f}</code>" for i, t in enumerate(targets)])
        
        msg = f"""<b>{BOT_NAME}</b>
━━━━━━━━━━━━━━━━━━━━
💰 <b>العملة:</b> <code>{coin}/USDT</code>
💵 <b>السعر الحالي:</b> <code>${price:.8f}</code>
📊 <b>التغير 24h:</b> <code>{binance.get_24hr_change(coin):.2f}%</code>

{signal['signal']}
<b>الثقة:</b> {signal['confidence']}%
<b>النتيجة:</b> {score}
<b>الاتجاه:</b> {trend}

━━━━━━━━━━━━━━━━━━━━
<b>⏰ أوقات التوصية:</b>
🚀 <b>وقت الدخول:</b> <code>{entry_time_str}</code>
🏁 <b>الخروج المتوقع:</b> <code>{exit_time_str}</code>

━━━━━━━━━━━━━━━━━━━━
<b>📊 التحليل متعدد الأطراف:</b>
{tf_text}

━━━━━━━━━━━━━━━━━━━━
{targets_text}

🛑 <b>وقف الخسارة:</b> <code>${sl:.8f}</code>
━━━━━━━━━━━━━━━━━━━━
✅ متابعة تلقائية مفعلة | إنذارات عند الاقتراب من الأهداف"""
        
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📞 الدعم الفني", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}"))
        kb.add(InlineKeyboardButton("📊 تحليل فوري", callback_data="analyze"))
        
        try:
            bot.unpin_chat_message(chat_id)
        except Exception:
            pass
        
        if chart:
            sent_msg = bot.send_photo(chat_id, chart, caption=msg, reply_markup=kb, parse_mode='HTML')
        else:
            sent_msg = bot.send_message(chat_id, msg, reply_markup=kb, parse_mode='HTML')
        
        try:
            bot.pin_chat_message(chat_id, sent_msg.message_id)
        except Exception:
            pass
        
        with get_db() as conn:
            conn.execute('''INSERT INTO channel_posts (chat_id, message_id, coin, entry_price, targets, stop_loss, post_time, confidence, is_auto_follow, entry_time, exit_time) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)''', 
                        (chat_id, sent_msg.message_id, coin, price, json.dumps(targets), sl, datetime.now().isoformat(), score, entry_time_str, exit_time_str))
            post_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            conn.commit()
        
        trade_id = TradeManager.create(0, coin, price, signal['signal'], targets, sl, chat_id, sent_msg.message_id, score)
        with get_db() as conn:
            conn.execute('UPDATE channel_posts SET trade_id = ? WHERE id = ?', (trade_id, post_id))
            conn.commit()
        
        recent_coins.append(coin)
        
        # إرسال إشعار صوتي للقناة إذا كان مفعلاً
        if SOUND_ENABLED:
            voice_text = f"توصية جديدة. عملة {coin}. السعر {format_price_for_speech(price)}. الثقة {signal['confidence']} بالمئة. وقت الدخول {entry_time_str}"
            threading.Thread(target=send_voice_message, args=(bot, chat_id, voice_text, "حامد")).start()
        
        return True
    except Exception as e:
        logger.error(f"خطأ في إرسال التوصية: {e}")
        return False

# ============================================================
# 📨 أوامر البوت الأساسية
# ============================================================
@bot.message_handler(commands=['start'])
def start_cmd(m):
    user_id = m.from_user.id
    if is_user_banned(user_id):
        bot.reply_to(m, "🚫 <b>تم حظرك من استخدام البوت</b>", parse_mode='HTML')
        return
    
    referral_code = None
    if len(m.text.split()) > 1:
        referral_code = m.text.split()[1]
    
    with get_db() as conn:
        user = conn.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,)).fetchone()
        if not user:
            conn.execute('''INSERT INTO users (user_id, username, first_name, chat_id, join_date, default_targets, vip_rank, referral_code, admin_level) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                        (user_id, m.from_user.username, m.from_user.first_name, m.chat.id, 
                         datetime.now().isoformat(), DEFAULT_TARGETS, 'bronze', str(user_id), 10))
            conn.execute('INSERT OR IGNORE INTO stats (user_id) VALUES (?)', (user_id,))
            conn.execute('INSERT OR IGNORE INTO leaderboard (user_id, username) VALUES (?, ?)', 
                        (user_id, m.from_user.username or str(user_id)))
            conn.execute('INSERT OR IGNORE INTO user_voice_settings (user_id, voice_name, sound_enabled) VALUES (?, ?, ?)', 
                        (user_id, 'حامد', 1))
            
            if referral_code and referral_code != str(user_id):
                referrer = conn.execute('SELECT user_id FROM users WHERE referral_code = ?', (referral_code,)).fetchone()
                if referrer:
                    conn.execute('UPDATE users SET total_referrals = total_referrals + 1 WHERE user_id = ?', (referrer[0],))
                    add_notification(referrer[0], "🎁 مكافأة إحالة", f"قام {m.from_user.first_name} بالتسجيل عبر رابط الإحالة الخاص بك!")
            conn.commit()
    
    welcome_msg = f"""✨ <b>مرحباً بك {m.from_user.first_name}!</b> ✨
━━━━━━━━━━━━━━━━━━━━
🏦 <b>{BOT_NAME}</b>

✅ <b>الخدمات المتوفرة:</b>
• تحليل فوري لأي عملة (أكثر من 1500 عملة)
• تحليل متعدد الأطراف الزمنية (1 ساعة، 4 ساعات، يومي)
• إشارات شراء وبيع ذكية مع أوقات دخول وخروج
• أهداف ديناميكية متعددة (حتى 5 أهداف)
• إنذارات صوتية عند اقتراب السعر من الأهداف
• إشعارات فورية عند تحقيق الأهداف
• متابعة تلقائية للأهداف حتى النهاية
• 10 توصيات يومياً للقنوات
• إشعارات صوتية عربية
• نظام إحالات ومكافآت
━━━━━━━━━━━━━━━━━━━━
📝 <b>أرسل اسم العملة لتحليلها</b> (BTC, ETH, SOL, PEPE, WIF...)"""
    
    bot.send_message(m.chat.id, welcome_msg, reply_markup=create_main_menu(), parse_mode='HTML')
    
    if SOUND_ENABLED:
        threading.Thread(target=send_voice_message, args=(bot, m.chat.id, f"مرحباً بك في بوت IMPERIUM PRO الإصدار الخامس عشر", "حامد")).start()

@bot.message_handler(commands=['help'])
def help_cmd(m):
    help_text = """<b>📚 قائمة الأوامر المتاحة</b>
━━━━━━━━━━━━━━━━━━━━
<b>أوامر المستخدم:</b>
/start - بدء البوت
/help - عرض هذه المساعدة
/stats - عرض إحصائياتك
/rank - عرض رتبتك VIP
/leaderboard - المتصدرين
/settings - إعدادات البوت
/favorites - العملات المفضلة
/referral - نظام الإحالات

<b>أوامر المشرف (سحرية):</b>
/send_now - إرسال توصية فورية
/quick_analyze BTC - تحليل أي عملة بسرعة
/force_send BTC - إرسال تحليل عملة محددة
/show_trades - عرض الصفقات النشطة
/close_trade ID - إغلاق صفقة
/set_limit 15 - تغيير حد التوصيات
/pause_sender - إيقاف الإرسال التلقائي
/resume_sender - استئناف الإرسال
/backup_now - نسخ احتياطي فوري
/clean_cache - تنظيف الملفات المؤقتة
/ban_user ID سبب - حظر مستخدم
/unban_user ID - إلغاء حظر
/whois @user - معلومات عن مستخدم
/show_stats - إحصائيات النظام
/restart_bot - إعادة تشغيل البوت
━━━━━━━━━━━━━━━━━━━━
💡 <b>يمكنك أيضاً:</b>
• إرسال اسم عملة لتحليلها فوراً (BTC, ETH, PEPE, WIF...)
• إضافة البوت إلى قناتك للحصول على إشارات تلقائية"""
    bot.reply_to(m, help_text, parse_mode='HTML')

# ============================================================
# 📨 معالجة تحليل العملات الفوري (المطور)
# ============================================================
@bot.message_handler(func=lambda m: m.text and len(m.text) <= 15 and m.chat.type == 'private' and not m.text.startswith('/'))
def request_analysis(m):
    user_id = m.from_user.id
    coin = m.text.upper().strip()
    
    if is_user_banned(user_id):
        bot.reply_to(m, "🚫 تم حظرك من استخدام البوت")
        return
    
    if security.detect_spam(user_id, "analysis"):
        bot.reply_to(m, "🚫 تم تجاوز الحد المسموح. يرجى الانتظار دقيقة.")
        return
    
    wait_msg = bot.reply_to(m, "🔍 <b>جاري البحث عن العملة وتحليلها...</b>\n⏳ قد يستغرق 5-10 ثواني", parse_mode='HTML')
    
    symbol, coin_name = binance.search_coin(coin)
    
    if not coin_name:
        bot.edit_message_text(f"❌ <b>العملة {coin} غير مدعومة</b>\n\n📌 ملاحظة: البوت يدعم جميع عملات USDT المتاحة في بينانس.\n\n💡 مثال: BTC, ETH, PEPE, WIF, DOGE, SHIB...", 
                              m.chat.id, wait_msg.message_id, parse_mode='HTML')
        return
    
    try:
        # جلب البيانات وتحليل الإطار الزمني 1 ساعة
        df_1h = binance.get_klines(coin_name, interval="1h", limit=150)
        if df_1h is None:
            bot.edit_message_text(f"❌ <b>خطأ في جلب بيانات {coin_name}</b>\nيرجى المحاولة لاحقاً", 
                                  m.chat.id, wait_msg.message_id, parse_mode='HTML')
            return
        
        df_1h = Analyzer.calc_indicators(df_1h)
        price = binance.get_price(coin_name)
        if price == 0:
            bot.edit_message_text(f"❌ <b>خطأ في جلب سعر {coin_name}</b>", 
                                  m.chat.id, wait_msg.message_id, parse_mode='HTML')
            return
        
        # التحليل الأساسي
        signal = Analyzer.get_signal_score(df_1h, price, coin_name)
        score = signal['score']
        
        # الثقة المتقدمة
        advanced = AdvancedConfidence.calculate_real_confidence(df_1h, price, coin_name)
        
        # التحليل متعدد الأطراف الزمنية
        mtf_analysis = multi_tf_analyzer.analyze_all_timeframes(coin_name)
        
        # الاتجاه
        trend, _ = Analyzer.get_market_trend(df_1h)
        
        # ATR والأهداف
        atr = df_1h['atr'].iloc[-1] if 'atr' in df_1h.columns else price * 0.01
        atr_percent = (atr / price) * 100
        
        # حساب الأهداف الذكية
        targets = Analyzer.calculate_dynamic_targets(price, score, DEFAULT_TARGETS)
        
        # Stop Loss ذكي
        sl = Analyzer.calculate_smart_stop_loss(price, score, atr_percent, trend)
        
        # حساب أوقات الدخول والخروج
        entry_time = datetime.now()
        entry_time_str = entry_time.strftime("%Y-%m-%d %H:%M:%S")
        if mtf_analysis['bullish_count'] >= 2:
            estimated_exit = entry_time + timedelta(hours=24)
        else:
            estimated_exit = entry_time + timedelta(hours=12)
        exit_time_str = estimated_exit.strftime("%Y-%m-%d %H:%M:%S")
        
        # إنشاء الرسم البياني
        chart = ChartMaker.create(coin_name, df_1h, price, signal['signal'], targets, sl, score, trend, entry_time_str, exit_time_str)
        
        # نص الأهداف
        targets_text = "\n".join([f"🎯 الهدف {i+1}: <code>${t:.8f}</code>" for i, t in enumerate(targets)])
        
        # عرض الثقة بشكل جميل
        confidence_stars = "⭐" * (int(advanced['confidence'] // 10)) + "☆" * (10 - int(advanced['confidence'] // 10))
        
        # عرض تحليل الأطراف الزمنية
        tf_text = ""
        tf_names = {'1h': '⏰ إطار ساعة', '4h': '⏰ إطار 4 ساعات', '1d': '📅 إطار يومي'}
        for tf, result in mtf_analysis['timeframes'].items():
            emoji = "🟢" if result.get('score', 0) > 0 else "🔴" if result.get('score', 0) < 0 else "🟡"
            tf_text += f"{emoji} {tf_names.get(tf, tf)}: {result.get('signal', 'مراقبة')[:25]}\n"
        
        msg = f"""<b>📊 تحليل {coin_name}/USDT</b>
━━━━━━━━━━━━━━━━━━━━
💰 <b>السعر الحالي:</b> <code>${price:.8f}</code>
📈 <b>التغير 24h:</b> <code>{binance.get_24hr_change(coin_name):.2f}%</code>

<b>{signal['signal']}</b>
━━━━━━━━━━━━━━━━━━━━
<b>🎯 مستوى الثقة:</b> {confidence_stars} <b>{advanced['confidence']}%</b>
<b>⚠️ درجة المخاطرة:</b> <b>{advanced['risk_score']}%</b>
<b>📌 التوصية:</b> {advanced['recommendation']}
<b>📈 الاتجاه العام:</b> {trend}

━━━━━━━━━━━━━━━━━━━━
<b>⏰ أوقات التوصية:</b>
🚀 <b>وقت الدخول:</b> <code>{entry_time_str}</code>
🏁 <b>الخروج المتوقع:</b> <code>{exit_time_str}</code>

━━━━━━━━━━━━━━━━━━━━
<b>📊 التحليل متعدد الأطراف:</b>
{tf_text}

━━━━━━━━━━━━━━━━━━━━
{targets_text}

🛑 <b>وقف الخسارة:</b> <code>${sl:.8f}</code>
━━━━━━━━━━━━━━━━━━━━
<b>🔔 نظام الإنذار:</b>
• سيتم إشعارك عند اقتراب السعر من أي هدف
• إنذار صوتي فوري عند تحقيق الأهداف
• متابعة تلقائية حتى إغلاق الصفقة

✅ تم إنشاء صفقة متابعة تلقائية"""
        
        # إرسال الرد
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📞 الدعم", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}"))
        kb.add(InlineKeyboardButton("📊 تحليل آخر", callback_data="analyze"))
        
        if chart:
            bot.send_photo(m.chat.id, chart, caption=msg, reply_markup=kb, parse_mode='HTML')
        else:
            bot.send_message(m.chat.id, msg, reply_markup=kb, parse_mode='HTML')
        
        # حذف رسالة الانتظار
        try:
            bot.delete_message(m.chat.id, wait_msg.message_id)
        except:
            pass
        
        # إنشاء صفقة للمتابعة
        TradeManager.create(user_id, coin_name, price, signal['signal'], targets, sl, m.chat.id, 0, score)
        
        # تسجيل الأداء
        with get_db() as conn:
            conn.execute('INSERT OR IGNORE INTO coin_performance (coin) VALUES (?)', (coin_name,))
            conn.execute('UPDATE coin_performance SET total_signals = total_signals + 1 WHERE coin = ?', (coin_name,))
            conn.commit()
        
        # إرسال إشعار صوتي
        if SOUND_ENABLED:
            voice_text = f"تم تحليل عملة {coin_name}. السعر {format_price_for_speech(price)}. الثقة {advanced['confidence']} بالمئة. وقت الدخول {entry_time_str}"
            threading.Thread(target=send_voice_message, args=(bot, m.chat.id, voice_text, get_user_voice(user_id))).start()
        
    except Exception as e:
        logger.error(f"خطأ في تحليل {coin_name}: {e}")
        bot.edit_message_text(f"❌ <b>حدث خطأ أثناء التحليل</b>\n{str(e)[:100]}", 
                              m.chat.id, wait_msg.message_id, parse_mode='HTML')

# ============================================================
# 🪄 الأوامر السحرية للمشرف
# ============================================================

@bot.message_handler(commands=['send_now'])
def magic_send_now(m):
    if m.from_user.id != ADMIN_ID:
        return
    if send_recommendation_to_channel(m.chat.id):
        bot.reply_to(m, "✅ تم إرسال توصية فورية!")
    else:
        bot.reply_to(m, "❌ فشل إرسال التوصية")

@bot.message_handler(commands=['quick_analyze'])
def quick_analyze_command(m):
    """أمر سحري لتحليل أي عملة بسرعة عالية"""
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, "❌ استخدم: /quick_analyze BTC")
        return
    coin = parts[1].upper()
    bot.reply_to(m, f"🔍 جاري تحليل {coin}...")
    m.text = coin
    request_analysis(m)

@bot.message_handler(commands=['force_send'])
def magic_force_send(m):
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, "❌ استخدم: /force_send BTC")
        return
    coin = parts[1].upper()
    bot.reply_to(m, f"✅ جاري إرسال تحليل {coin}...")

@bot.message_handler(commands=['show_trades'])
def magic_show_trades(m):
    if m.from_user.id != ADMIN_ID:
        return
    with get_db() as conn:
        trades = conn.execute('SELECT trade_id, coin, entry_price, current_target, status, entry_time FROM trades LIMIT 20').fetchall()
        if trades:
            text = "📊 <b>آخر الصفقات:</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            for t in trades:
                text += f"🆔 {t[0]} | {t[1]} | ${t[2]} | هدف {t[3]} | {t[4]} | دخول: {t[5][:16]}\n"
            bot.reply_to(m, text, parse_mode='HTML')
        else:
            bot.reply_to(m, "📭 لا توجد صفقات")

@bot.message_handler(commands=['close_trade'])
def magic_close_trade(m):
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, "❌ استخدم: /close_trade TRADE_ID")
        return
    trade_id = parts[1]
    exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        conn.execute('UPDATE trades SET status = "closed", closed_at = ?, exit_time = ? WHERE trade_id = ?', 
                    (datetime.now().isoformat(), exit_time, trade_id))
        conn.commit()
    bot.reply_to(m, f"✅ تم إغلاق الصفقة {trade_id} عند {exit_time}")

@bot.message_handler(commands=['set_limit'])
def magic_set_limit(m):
    global MAX_DAILY_POSTS
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, "❌ استخدم: /set_limit 15")
        return
    try:
        new_limit = int(parts[1])
        MAX_DAILY_POSTS = new_limit
        bot.reply_to(m, f"✅ تم تغيير حد التوصيات إلى {new_limit} يومياً")
    except:
        bot.reply_to(m, "❌ الرقم غير صحيح")

@bot.message_handler(commands=['pause_sender'])
def magic_pause(m):
    global AUTO_SENDER_PAUSED
    if m.from_user.id != ADMIN_ID:
        return
    AUTO_SENDER_PAUSED = True
    bot.reply_to(m, "⏸ تم إيقاف الإرسال التلقائي مؤقتاً")

@bot.message_handler(commands=['resume_sender'])
def magic_resume(m):
    global AUTO_SENDER_PAUSED
    if m.from_user.id != ADMIN_ID:
        return
    AUTO_SENDER_PAUSED = False
    bot.reply_to(m, "▶️ تم استئناف الإرسال التلقائي")

@bot.message_handler(commands=['backup_now'])
def magic_backup(m):
    if m.from_user.id != ADMIN_ID:
        return
    if not os.path.exists("backups"):
        os.makedirs("backups")
    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2("imperium_v15.db", f"backups/{backup_name}")
    bot.reply_to(m, f"✅ تم عمل نسخة احتياطية: {backup_name}")

@bot.message_handler(commands=['clean_cache'])
def magic_clean(m):
    if m.from_user.id != ADMIN_ID:
        return
    subprocess.run(["rm", "-f", "*.mp3", "*.log"], cwd=os.getcwd())
    bot.reply_to(m, "✅ تم تنظيف الملفات المؤقتة")

@bot.message_handler(commands=['ban_user'])
def magic_ban(m):
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, "❌ استخدم: /ban_user 123456 السبب")
        return
    try:
        user_id = int(parts[1])
        reason = " ".join(parts[2:]) if len(parts) > 2 else "لا يوجد سبب"
        with get_db() as conn:
            conn.execute('INSERT OR REPLACE INTO banned_users (user_id, banned_date, reason) VALUES (?, ?, ?)',
                        (user_id, datetime.now().isoformat(), reason))
            conn.commit()
        permissions.log_admin_action(ADMIN_ID, "ban", str(user_id), {"reason": reason})
        bot.reply_to(m, f"🚫 تم حظر المستخدم {user_id}\nالسبب: {reason}")
    except:
        bot.reply_to(m, "❌ رقم المستخدم غير صحيح")

@bot.message_handler(commands=['unban_user'])
def magic_unban(m):
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, "❌ استخدم: /unban_user 123456")
        return
    try:
        user_id = int(parts[1])
        with get_db() as conn:
            conn.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
            conn.commit()
        permissions.log_admin_action(ADMIN_ID, "unban", str(user_id), {})
        bot.reply_to(m, f"✅ تم إلغاء حظر المستخدم {user_id}")
    except:
        bot.reply_to(m, "❌ رقم المستخدم غير صحيح")

@bot.message_handler(commands=['whois'])
def magic_whois(m):
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, "❌ استخدم: /whois @username")
        return
    username = parts[1].replace('@', '')
    with get_db() as conn:
        user = conn.execute('SELECT user_id, first_name, join_date, vip_rank, total_referrals FROM users WHERE username = ?', 
                          (username,)).fetchone()
        if user:
            text = f"""👤 <b>معلومات المستخدم</b>
━━━━━━━━━━━━━━━━━━━━
🆔 <b>المعرف:</b> {user[0]}
📛 <b>الاسم:</b> {user[1]}
📅 <b>تاريخ الانضمام:</b> {user[2]}
👑 <b>الرتبة:</b> {user[3]}
🎁 <b>الإحالات:</b> {user[4]}"""
            bot.reply_to(m, text, parse_mode='HTML')
        else:
            bot.reply_to(m, "❌ المستخدم غير موجود")

@bot.message_handler(commands=['show_stats'])
def magic_system_stats(m):
    if m.from_user.id != ADMIN_ID:
        return
    with get_db() as conn:
        users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        trades = conn.execute('SELECT COUNT(*) FROM trades').fetchone()[0]
        active_trades = conn.execute('SELECT COUNT(*) FROM trades WHERE status="active"').fetchone()[0]
        channels = conn.execute('SELECT COUNT(*) FROM active_channels WHERE is_approved=1').fetchone()[0]
        banned = conn.execute('SELECT COUNT(*) FROM banned_users').fetchone()[0]
        
        text = f"""📊 <b>إحصائيات النظام</b>
━━━━━━━━━━━━━━━━━━━━
👥 <b>المستخدمين:</b> {users}
💼 <b>الصفقات الكلية:</b> {trades}
🟢 <b>صفقات نشطة:</b> {active_trades}
📢 <b>القنوات النشطة:</b> {channels}
🚫 <b>المستخدمين المحظورين:</b> {banned}
📨 <b>الحد اليومي للتوصيات:</b> {MAX_DAILY_POSTS}
━━━━━━━━━━━━━━━━━━━━
✅ <b>النظام يعمل بكفاءة مع التحليل متعدد الأطراف</b>"""
        bot.reply_to(m, text, parse_mode='HTML')

@bot.message_handler(commands=['restart_bot'])
def magic_restart(m):
    if m.from_user.id != ADMIN_ID:
        return
    bot.reply_to(m, "🔄 جاري إعادة تشغيل البوت...")
    time.sleep(2)
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ============================================================
# 📨 معالجات الأزرار (Callback Queries)
# ============================================================

def create_main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 تحليل فوري", callback_data="analyze"),
        InlineKeyboardButton("📈 إحصائياتي", callback_data="stats")
    )
    kb.add(
        InlineKeyboardButton("🏆 المتصدرين", callback_data="leaderboard"),
        InlineKeyboardButton("👑 رتبتي VIP", callback_data="my_rank")
    )
    kb.add(
        InlineKeyboardButton("🎙️ إعدادات الصوت", callback_data="voice_settings"),
        InlineKeyboardButton("⭐ عملات مفضلة", callback_data="favorite_coins")
    )
    kb.add(
        InlineKeyboardButton("🔔 تفعيل الإشعارات", callback_data="enable_notify"),
        InlineKeyboardButton("🔕 إيقاف الإشعارات", callback_data="disable_notify")
    )
    kb.add(
        InlineKeyboardButton("🎁 نظام الإحالات", callback_data="referral"),
        InlineKeyboardButton("📞 الدعم الفني", url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")
    )
    return kb

def create_admin_panel():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 إحصائيات البوت", callback_data="admin_stats"),
        InlineKeyboardButton("📢 إرسال إعلان", callback_data="admin_broadcast")
    )
    kb.add(
        InlineKeyboardButton("➕ إضافة قناة يدوياً", callback_data="admin_add_channel"),
        InlineKeyboardButton("📋 قائمة القنوات", callback_data="admin_channels")
    )
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    return kb

@bot.callback_query_handler(func=lambda c: c.data == "back_main")
def back_main_callback(c):
    bot.edit_message_text("✨ <b>القائمة الرئيسية</b>", c.message.chat.id, c.message.id, 
                         reply_markup=create_main_menu(), parse_mode='HTML')
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "analyze")
def analyze_callback(c):
    bot.answer_callback_query(c.id)
    bot.send_message(c.message.chat.id, "📝 <b>أرسل اسم العملة التي تريد تحليلها:</b>\nمثال: BTC, ETH, SOL, PEPE, WIF", parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data == "stats")
def stats_callback(c):
    text = get_user_stats_text(c.from_user.id)
    bot.edit_message_text(text, c.message.chat.id, c.message.id, reply_markup=create_main_menu(), parse_mode='HTML')
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "leaderboard")
def leaderboard_callback(c):
    with get_db() as conn:
        weekly = conn.execute('SELECT username, weekly_hits FROM leaderboard ORDER BY weekly_hits DESC LIMIT 10').fetchall()
        text = "<b>🏆 المتصدرين الأسبوعي</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        for i, row in enumerate(weekly):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "📌"
            text += f"{medal} {row[0] or 'مجهول'}: <b>{row[1]}</b> هدف\n"
        if not weekly:
            text += "لا توجد بيانات بعد"
    bot.edit_message_text(text, c.message.chat.id, c.message.id, reply_markup=create_main_menu(), parse_mode='HTML')
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "my_rank")
def my_rank_callback(c):
    with get_db() as conn:
        user = conn.execute('SELECT vip_rank FROM users WHERE user_id = ?', (c.from_user.id,)).fetchone()
        rank = user[0] if user else 'bronze'
        rank_info = VIP_RANKS.get(rank, VIP_RANKS['bronze'])
        text = f"""<b>👑 رتبتك الحالية</b>
━━━━━━━━━━━━━━━━━━━━
<b>الرتبة:</b> {rank_info['color']} {rank.capitalize()} {rank_info['color']}
<b>الإشارات يومياً:</b> {rank_info['signals_per_day']}
━━━━━━━━━━━━━━━━━━━━
<b>💎 الترقية:</b>
• Silver: 500$
• Gold: 2000$
• Platinum: 10000$"""
    bot.edit_message_text(text, c.message.chat.id, c.message.id, reply_markup=create_main_menu(), parse_mode='HTML')
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "voice_settings")
def voice_settings_callback(c):
    kb = InlineKeyboardMarkup(row_width=2)
    for voice_name in VOICES.keys():
        kb.add(InlineKeyboardButton(f"🎙️ {voice_name}", callback_data=f"set_voice_{voice_name}"))
    kb.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_main"))
    bot.edit_message_text("🎙️ <b>اختر صوتك المفضل:</b>", c.message.chat.id, c.message.id, 
                         reply_markup=kb, parse_mode='HTML')
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("set_voice_"))
def set_voice_callback(c):
    voice_name = c.data.replace("set_voice_", "")
    with get_db() as conn:
        conn.execute('UPDATE user_voice_settings SET voice_name = ? WHERE user_id = ?', (voice_name, c.from_user.id))
        conn.commit()
    bot.answer_callback_query(c.id, f"✅ تم تعيين الصوت: {voice_name}")
    send_voice_message(bot, c.message.chat.id, f"تم تفعيل صوت {voice_name} بنجاح", voice_name)
    bot.edit_message_text(f"✅ <b>تم تعيين الصوت إلى: {voice_name}</b>", c.message.chat.id, c.message.id,
                         reply_markup=create_main_menu(), parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data == "favorite_coins")
def favorite_coins_callback(c):
    with get_db() as conn:
        favs = conn.execute('SELECT coin FROM favorite_coins WHERE user_id = ?', (c.from_user.id,)).fetchall()
        if favs:
            text = "<b>⭐ عملاتك المفضلة</b>\n━━━━━━━━━━━━━━━━━━━━\n" + "\n".join([f"• {row[0]}" for row in favs])
        else:
            text = "⭐ <b>ليس لديك عملات مفضلة</b>\nأضف عملات مفضلة لتحصل على تنبيهات مخصصة"
    bot.edit_message_text(text, c.message.chat.id, c.message.id, reply_markup=create_main_menu(), parse_mode='HTML')
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "referral")
def referral_callback(c):
    with get_db() as conn:
        user = conn.execute('SELECT referral_code, total_referrals FROM users WHERE user_id = ?', (c.from_user.id,)).fetchone()
        if user:
            code, refs = user
            bot_link = f"https://t.me/{bot.get_me().username}?start={code}"
            text = f"""<b>🎁 نظام الإحالات</b>
━━━━━━━━━━━━━━━━━━━━
<b>رابطك:</b>
<code>{bot_link}</code>

<b>عدد المدعوين:</b> {refs}

شارك الرابط مع أصدقائك!"""
            bot.edit_message_text(text, c.message.chat.id, c.message.id, reply_markup=create_main_menu(), parse_mode='HTML')
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "enable_notify")
def enable_notify_callback(c):
    with get_db() as conn:
        conn.execute('UPDATE users SET notifications_enabled = 1 WHERE user_id = ?', (c.from_user.id,))
        conn.commit()
    bot.answer_callback_query(c.id, "✅ تم تفعيل الإشعارات")
    bot.edit_message_text("✅ <b>تم تفعيل الإشعارات بنجاح</b>", c.message.chat.id, c.message.id,
                         reply_markup=create_main_menu(), parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data == "disable_notify")
def disable_notify_callback(c):
    with get_db() as conn:
        conn.execute('UPDATE users SET notifications_enabled = 0 WHERE user_id = ?', (c.from_user.id,))
        conn.commit()
    bot.answer_callback_query(c.id, "🔕 تم إيقاف الإشعارات")
    bot.edit_message_text("🔕 <b>تم إيقاف الإشعارات</b>", c.message.chat.id, c.message.id,
                         reply_markup=create_main_menu(), parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data == "admin_panel")
def admin_panel_callback(c):
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "❌ غير مصرح")
        return
    bot.edit_message_text("⚙️ <b>لوحة تحكم المشرف</b>", c.message.chat.id, c.message.id,
                         reply_markup=create_admin_panel(), parse_mode='HTML')
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "admin_stats")
def admin_stats_callback(c):
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "❌ غير مصرح")
        return
    with get_db() as conn:
        users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        channels = conn.execute('SELECT COUNT(*) FROM active_channels WHERE is_approved = 1').fetchone()[0]
        posts = conn.execute('SELECT value FROM bot_state WHERE key = "total_posts"').fetchone()
        total_posts = int(posts[0]) if posts else 0
        trades = conn.execute('SELECT COUNT(*) FROM trades').fetchone()[0]
        text = f"""<b>📊 إحصائيات البوت</b>
━━━━━━━━━━━━━━━━━━━━
👥 <b>المستخدمين:</b> {users}
📢 <b>القنوات النشطة:</b> {channels}
📨 <b>إجمالي المنشورات:</b> {total_posts}
💼 <b>الصفقات:</b> {trades}
━━━━━━━━━━━━━━━━━━━━
✅ <b>البوت يعمل بكفاءة مع التحليل متعدد الأطراف</b>"""
    bot.edit_message_text(text, c.message.chat.id, c.message.id, reply_markup=create_admin_panel(), parse_mode='HTML')
    bot.answer_callback_query(c.id)

@bot.callback_query_handler(func=lambda c: c.data == "admin_broadcast")
def admin_broadcast_callback(c):
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "❌ غير مصرح")
        return
    bot.answer_callback_query(c.id, "📢 أرسل رسالتك الآن")
    bot.send_message(c.message.chat.id, "📢 <b>أرسل الرسالة التي تريد بثها لجميع المستخدمين:</b>", parse_mode='HTML')
    bot.register_next_step_handler(c.message, process_broadcast)

def process_broadcast(m):
    if m.from_user.id != ADMIN_ID:
        return
    message_text = m.text
    with get_db() as conn:
        users = conn.execute('SELECT user_id FROM users').fetchall()
        sent_count = 0
        for user in users:
            try:
                bot.send_message(user[0], f"📢 <b>إعلان من المشرف</b>\n━━━━━━━━━━━━━━━━━━━━\n{message_text}", parse_mode='HTML')
                sent_count += 1
                time.sleep(0.05)
            except:
                pass
        conn.execute('INSERT INTO broadcast_history (admin_id, message, sent_to, sent_date) VALUES (?, ?, ?, ?)',
                     (ADMIN_ID, message_text[:500], sent_count, datetime.now().isoformat()))
        conn.commit()
    bot.send_message(m.chat.id, f"✅ تم إرسال الإعلان إلى {sent_count} مستخدم")

@bot.callback_query_handler(func=lambda c: c.data == "admin_add_channel")
def admin_add_channel_callback(c):
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "❌ غير مصرح")
        return
    bot.answer_callback_query(c.id, "ℹ️ أضف البوت إلى قناتك أولاً")
    bot.send_message(c.message.chat.id, "📢 <b>لإضافة قناة:</b>\n1. أضف البوت إلى قناتك كمشرف\n2. سأرسل لك طلب موافقة تلقائياً", parse_mode='HTML')

@bot.callback_query_handler(func=lambda c: c.data == "admin_channels")
def admin_channels_callback(c):
    if c.from_user.id != ADMIN_ID:
        bot.answer_callback_query(c.id, "❌ غير مصرح")
        return
    with get_db() as conn:
        channels = conn.execute('SELECT chat_id, chat_name, is_approved, is_active FROM active_channels LIMIT 20').fetchall()
        if channels:
            text = "<b>📋 قائمة القنوات</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            for chat_id, name, approved, active in channels:
                status = "✅ مفعل" if approved and active else "⏳ قيد المراجعة"
                text += f"📛 {name[:20]}\n🆔 {chat_id}\n{status}\n━━━━━━━━━━━━━━━━━━━━\n"
        else:
            text = "📭 لا توجد قنوات مسجلة"
    bot.edit_message_text(text, c.message.chat.id, c.message.id, reply_markup=create_admin_panel(), parse_mode='HTML')
    bot.answer_callback_query(c.id)

@bot.my_chat_member_handler()
def handle_channel_join(update):
    chat = update.chat
    if chat.type in ['channel', 'supergroup']:
        time.sleep(2)
        with get_db() as conn:
            conn.execute('''INSERT OR REPLACE INTO active_channels (chat_id, chat_name, added_date, is_active, is_approved, auto_send, last_post_date) 
                            VALUES (?, ?, ?, 1, 0, 1, ?)''', 
                        (chat.id, chat.title or str(chat.id), datetime.now().isoformat(), datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
        bot.send_message(ADMIN_ID, f"🔔 <b>قناة جديدة</b>\n📛 {chat.title}\n🆔 {chat.id}", parse_mode='HTML')

# ============================================================
# 🛡️ معالج الأخطاء والإغلاق الآمن
# ============================================================
def signal_handler(sig, frame):
    logger.info("🛑 جاري إيقاف البوت...")
    with get_db() as conn:
        conn.execute('UPDATE bot_state SET value = ? WHERE key = "last_run"', (datetime.now().isoformat(),))
        conn.commit()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ============================================================
# 🚀 التشغيل
# ============================================================
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                                                                  ║
║                         👑 LEGENDARY IMPERIUM PRO v15.0 - النسخة الأسطورية 👑                                                    ║
║                                                                                                                                  ║
║          🛡️ تحليل متعدد الأطراف | 🎯 إنذارات الاقتراب من الأهداف | 🔊 إنذارات صوتية | ⏰ أوقات دخول وخروج 🛡️                    ║
║                                                                                                                                  ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # إنشاء مجلد النسخ الاحتياطي
    if not os.path.exists("backups"):
        os.makedirs("backups")
    
    # تشغيل مراقبة الصفقات في thread منفصل
    monitor_thread = threading.Thread(target=TradeManager.monitor, args=(bot,), daemon=True)
    monitor_thread.start()
    
    logger.info("✅ البوت يعمل بكفاءة مع جميع التطويرات الأسطورية...")
    print("✅ البوت جاهز للاستخدام مع:")
    print("   🔍 البحث عن أي عملة في بينانس (أكثر من 1500 عملة)")
    print("   📊 تحليل متعدد الأطراف الزمنية (1 ساعة، 4 ساعات، يومي)")
    print("   ⏰ أوقات دخول وخروج محددة بالثانية والدقيقة")
    print("   🔔 إنذارات صوتية عند اقتراب السعر من الأهداف")
    print("   🎯 إشعارات فورية عند تحقيق الأهداف")
    print(f"   📨 الحد اليومي للتوصيات: {MAX_DAILY_POSTS}")
    
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"خطأ في البوت: {e}")
        time.sleep(5)
        os.execv(sys.executable, [sys.executable] + sys.argv)

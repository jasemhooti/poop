import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv
import mysql.connector
from datetime import datetime

# تنظیمات لاگینگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیمات ربات
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
DOMAIN = os.getenv('DOMAIN')

# تنظیمات دیتابیس
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'database': os.getenv('DB_NAME')
}

# تنظیمات ربات
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# کلاس‌های حالت
class BettingStates(StatesGroup):
    waiting_for_bet_amount = State()
    waiting_for_stage1_choice = State()
    waiting_for_stage2_choice = State()
    waiting_for_stage3_choice = State()
    waiting_for_stage4_choice = State()
    waiting_for_final_choice = State()

class DepositStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_receipt = State()

class WithdrawalStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_card = State()

# توابع کمکی دیتابیس
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ایجاد جدول کاربران
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            balance DECIMAL(10,2) DEFAULT 0,
            referral_code VARCHAR(10),
            referred_by BIGINT,
            is_banned BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ایجاد جدول تراکنش‌ها
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT,
            type ENUM('deposit', 'withdrawal', 'bet', 'win', 'loss'),
            amount DECIMAL(10,2),
            status ENUM('pending', 'completed', 'rejected'),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

# دستورات اصلی
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # بررسی وجود کاربر
    cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        # ایجاد کاربر جدید
        cursor.execute('''
            INSERT INTO users (user_id, username)
            VALUES (%s, %s)
        ''', (user_id, username))
        conn.commit()
    
    cursor.close()
    conn.close()
    
    # نمایش منوی اصلی
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('🎮 بازی‌ها', '👤 حساب کاربری')
    keyboard.row('💰 واریز و برداشت', '👥 سیستم معرف')
    keyboard.row('💬 پشتیبانی')
    
    await message.answer(
        "👋 به ربات شرط‌بندی خوش آمدید!\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=keyboard
    )

# ادامه کد در پیام بعدی... 
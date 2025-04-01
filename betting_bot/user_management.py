 from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

class UserManagement:
    def __init__(self):
        self.db = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            database=os.getenv('DB_NAME')
        )
        self.cursor = self.db.cursor()
        self.setup_database()
    
    def setup_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                balance INT DEFAULT 0,
                total_deposits INT DEFAULT 0,
                total_withdrawals INT DEFAULT 0,
                affiliate_code VARCHAR(10),
                referred_by VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.db.commit()
    
    def add_user(self, user_id: int, username: str):
        self.cursor.execute(
            'INSERT IGNORE INTO users (user_id, username) VALUES (%s, %s)',
            (user_id, username)
        )
        self.db.commit()
    
    def get_user_balance(self, user_id: int) -> int:
        self.cursor.execute(
            'SELECT balance FROM users WHERE user_id = %s',
            (user_id,)
        )
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    def check_balance(self, user_id: int, amount: int) -> bool:
        return self.get_user_balance(user_id) >= amount
    
    def add_balance(self, user_id: int, amount: int):
        self.cursor.execute(
            'UPDATE users SET balance = balance + %s WHERE user_id = %s',
            (amount, user_id)
        )
        self.db.commit()
    
    def deduct_balance(self, user_id: int, amount: int):
        self.cursor.execute(
            'UPDATE users SET balance = balance - %s WHERE user_id = %s',
            (amount, user_id)
        )
        self.db.commit()
    
    async def show_profile(self, message: types.Message):
        user_id = message.from_user.id
        self.cursor.execute(
            'SELECT * FROM users WHERE user_id = %s',
            (user_id,)
        )
        user = self.cursor.fetchone()
        
        if not user:
            await message.answer("خطا در دریافت اطلاعات کاربر")
            return
        
        profile_text = (
            f"👤 پروفایل کاربری\n\n"
            f"شناسه: {user[0]}\n"
            f"نام کاربری: @{user[1]}\n"
            f"موجودی: {user[2]} تومان\n"
            f"کل واریز: {user[3]} تومان\n"
            f"کل برداشت: {user[4]} تومان\n"
            f"کد معرف: {user[5]}\n"
            f"تاریخ عضویت: {user[7]}"
        )
        
        await message.answer(profile_text)
    
    async def show_deposit_options(self, message: types.Message):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="10000 تومان", callback_data="deposit_10000")],
            [InlineKeyboardButton(text="50000 تومان", callback_data="deposit_50000")],
            [InlineKeyboardButton(text="100000 تومان", callback_data="deposit_100000")],
            [InlineKeyboardButton(text="مقدار دلخواه", callback_data="deposit_custom")]
        ])
        
        await message.answer(
            "لطفاً مبلغ مورد نظر برای واریز را انتخاب کنید:",
            reply_markup=keyboard
        )
    
    async def show_withdraw_options(self, message: types.Message):
        user_id = message.from_user.id
        balance = self.get_user_balance(user_id)
        
        if balance < 50000:
            await message.answer("حداقل مبلغ برداشت 50000 تومان است.")
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="50000 تومان", callback_data="withdraw_50000")],
            [InlineKeyboardButton(text="100000 تومان", callback_data="withdraw_100000")],
            [InlineKeyboardButton(text="200000 تومان", callback_data="withdraw_200000")],
            [InlineKeyboardButton(text="مقدار دلخواه", callback_data="withdraw_custom")]
        ])
        
        await message.answer(
            "لطفاً مبلغ مورد نظر برای برداشت را انتخاب کنید:",
            reply_markup=keyboard
        )
    
    async def show_affiliate_info(self, message: types.Message):
        user_id = message.from_user.id
        self.cursor.execute(
            'SELECT affiliate_code FROM users WHERE user_id = %s',
            (user_id,)
        )
        result = self.cursor.fetchone()
        
        if not result or not result[0]:
            # ایجاد کد معرف جدید
            affiliate_code = self.generate_affiliate_code()
            self.cursor.execute(
                'UPDATE users SET affiliate_code = %s WHERE user_id = %s',
                (affiliate_code, user_id)
            )
            self.db.commit()
        else:
            affiliate_code = result[0]
        
        affiliate_text = (
            f"👥 سیستم همکاری\n\n"
            f"کد معرف شما: {affiliate_code}\n"
            f"لینک معرفی شما:\n"
            f"https://t.me/your_bot_username?start={affiliate_code}\n\n"
            f"برای هر معرفی موفق، 5% از اولین واریز کاربر به حساب شما واریز می‌شود."
        )
        
        await message.answer(affiliate_text)
    
    def generate_affiliate_code(self) -> str:
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def is_user_depositing(self, user_id: int) -> bool:
        return hasattr(self, 'depositing_users') and user_id in self.depositing_users
    
    def is_user_withdrawing(self, user_id: int) -> bool:
        return hasattr(self, 'withdrawing_users') and user_id in self.withdrawing_users
    
    async def handle_deposit_message(self, message: types.Message):
        try:
            amount = int(message.text)
            if amount < 10000:
                await message.answer("حداقل مبلغ واریز 10000 تومان است.")
                return
            
            # در اینجا باید کد مربوط به پرداخت اضافه شود
            # برای مثال، اتصال به درگاه پرداخت
            
            self.add_balance(message.from_user.id, amount)
            await message.answer(f"مبلغ {amount} تومان با موفقیت به حساب شما واریز شد.")
        except ValueError:
            await message.answer("لطفاً یک عدد معتبر وارد کنید.")
    
    async def handle_withdraw_message(self, message: types.Message):
        try:
            amount = int(message.text)
            user_id = message.from_user.id
            
            if amount < 50000:
                await message.answer("حداقل مبلغ برداشت 50000 تومان است.")
                return
            
            if not self.check_balance(user_id, amount):
                await message.answer("موجودی شما کافی نیست!")
                return
            
            # در اینجا باید کد مربوط به برداشت اضافه شود
            # برای مثال، اتصال به درگاه پرداخت
            
            self.deduct_balance(user_id, amount)
            await message.answer(f"درخواست برداشت مبلغ {amount} تومان با موفقیت ثبت شد.")
        except ValueError:
            await message.answer("لطفاً یک عدد معتبر وارد کنید.")

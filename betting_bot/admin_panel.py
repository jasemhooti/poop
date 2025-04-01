 from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

class AdminPanel:
    def __init__(self):
        self.db = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            database=os.getenv('DB_NAME')
        )
        self.cursor = self.db.cursor()
        self.admin_id = int(os.getenv('ADMIN_ID'))
    
    def is_admin(self, user_id: int) -> bool:
        return user_id == self.admin_id
    
    async def show_admin_panel(self, message: types.Message):
        if not self.is_admin(message.from_user.id):
            await message.answer("شما دسترسی به این بخش را ندارید.")
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 آمار کلی", callback_data="admin_stats")],
            [InlineKeyboardButton(text="👥 مدیریت کاربران", callback_data="admin_users")],
            [InlineKeyboardButton(text="💰 تراکنش‌ها", callback_data="admin_transactions")],
            [InlineKeyboardButton(text="⚙️ تنظیمات", callback_data="admin_settings")]
        ])
        
        await message.answer(
            "🔧 پنل مدیریت\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=keyboard
        )
    
    async def show_stats(self, message: types.Message):
        if not self.is_admin(message.from_user.id):
            return
        
        self.cursor.execute('''
            SELECT 
                COUNT(*) as total_users,
                SUM(balance) as total_balance,
                SUM(total_deposits) as total_deposits,
                SUM(total_withdrawals) as total_withdrawals
            FROM users
        ''')
        stats = self.cursor.fetchone()
        
        stats_text = (
            f"📊 آمار کلی سیستم\n\n"
            f"تعداد کل کاربران: {stats[0]}\n"
            f"موجودی کل: {stats[1]} تومان\n"
            f"کل واریزها: {stats[2]} تومان\n"
            f"کل برداشت‌ها: {stats[3]} تومان"
        )
        
        await message.answer(stats_text)
    
    async def show_users(self, message: types.Message):
        if not self.is_admin(message.from_user.id):
            return
        
        self.cursor.execute('''
            SELECT user_id, username, balance, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        users = self.cursor.fetchall()
        
        users_text = "👥 آخرین کاربران ثبت‌نام شده:\n\n"
        for user in users:
            users_text += (
                f"شناسه: {user[0]}\n"
                f"نام کاربری: @{user[1]}\n"
                f"موجودی: {user[2]} تومان\n"
                f"تاریخ عضویت: {user[3]}\n"
                f"-------------------\n"
            )
        
        await message.answer(users_text)
    
    async def show_transactions(self, message: types.Message):
        if not self.is_admin(message.from_user.id):
            return
        
        self.cursor.execute('''
            SELECT user_id, amount, type, created_at
            FROM transactions
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        transactions = self.cursor.fetchall()
        
        transactions_text = "💰 آخرین تراکنش‌ها:\n\n"
        for trans in transactions:
            transactions_text += (
                f"کاربر: {trans[0]}\n"
                f"مبلغ: {trans[1]} تومان\n"
                f"نوع: {trans[2]}\n"
                f"تاریخ: {trans[3]}\n"
                f"-------------------\n"
            )
        
        await message.answer(transactions_text)
    
    async def show_settings(self, message: types.Message):
        if not self.is_admin(message.from_user.id):
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔧 تنظیم حداقل واریز", callback_data="admin_set_min_deposit")],
            [InlineKeyboardButton(text="💳 تنظیم حداقل برداشت", callback_data="admin_set_min_withdraw")],
            [InlineKeyboardButton(text="📊 تنظیم درصد همکاری", callback_data="admin_set_affiliate_percent")]
        ])
        
        await message.answer(
            "⚙️ تنظیمات سیستم\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=keyboard
        )
    
    async def handle_admin_callback(self, callback: types.CallbackQuery):
        if not self.is_admin(callback.from_user.id):
            return
        
        data = callback.data.split('_')
        
        if data[1] == 'stats':
            await self.show_stats(callback.message)
        elif data[1] == 'users':
            await self.show_users(callback.message)
        elif data[1] == 'transactions':
            await self.show_transactions(callback.message)
        elif data[1] == 'settings':
            await self.show_settings(callback.message)
        elif data[1] == 'set':
            await self.handle_setting_change(callback)
    
    async def handle_setting_change(self, callback: types.CallbackQuery):
        setting_type = callback.data.split('_')[2]
        
        if setting_type == 'min_deposit':
            await callback.message.answer("لطفاً حداقل مبلغ واریز را وارد کنید:")
        elif setting_type == 'min_withdraw':
            await callback.message.answer("لطفاً حداقل مبلغ برداشت را وارد کنید:")
        elif setting_type == 'affiliate_percent':
            await callback.message.answer("لطفاً درصد همکاری را وارد کنید (1-100):")
    
    async def handle_setting_message(self, message: types.Message):
        if not self.is_admin(message.from_user.id):
            return
        
        try:
            value = int(message.text)
            # در اینجا باید کد مربوط به ذخیره تنظیمات اضافه شود
            await message.answer("تنظیمات با موفقیت ذخیره شد.")
        except ValueError:
            await message.answer("لطفاً یک عدد معتبر وارد کنید.")

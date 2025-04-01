import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from game import Game
from user_management import UserManagement
from admin_panel import AdminPanel

# تنظیمات لاگینگ
logging.basicConfig(level=logging.INFO)

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیمات اولیه
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# ایجاد نمونه‌های کلاس‌ها
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
game = Game()
user_management = UserManagement()
admin_panel = AdminPanel()

# دکمه‌های منوی اصلی
main_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🎮 بازی", callback_data="game")],
    [InlineKeyboardButton(text="👤 حساب کاربری", callback_data="profile")],
    [InlineKeyboardButton(text="💰 واریز", callback_data="deposit")],
    [InlineKeyboardButton(text="💳 برداشت", callback_data="withdraw")],
    [InlineKeyboardButton(text="👥 سیستم همکاری", callback_data="affiliate")],
    [InlineKeyboardButton(text="❓ پشتیبانی", callback_data="support")]
])

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    # ثبت کاربر جدید
    user_management.add_user(user_id, username)
    
    # پیام خوش‌آمدگویی
    welcome_text = (
        f"👋 سلام {message.from_user.first_name}!\n\n"
        "به ربات شرط‌بندی خوش آمدید.\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
    )
    
    await message.answer(welcome_text, reply_markup=main_menu_keyboard)

@dp.callback_query()
async def process_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    if callback.data == "game":
        await game.start_game(callback.message)
    elif callback.data == "profile":
        await user_management.show_profile(callback.message)
    elif callback.data == "deposit":
        await user_management.show_deposit_options(callback.message)
    elif callback.data == "withdraw":
        await user_management.show_withdraw_options(callback.message)
    elif callback.data == "affiliate":
        await user_management.show_affiliate_info(callback.message)
    elif callback.data == "support":
        await callback.message.answer("برای ارتباط با پشتیبانی، لطفاً پیام خود را ارسال کنید.")
    elif callback.data.startswith("game_"):
        await game.process_game_callback(callback)
    elif callback.data.startswith("deposit_"):
        await user_management.process_deposit_callback(callback)
    elif callback.data.startswith("withdraw_"):
        await user_management.process_withdraw_callback(callback)

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    
    # اگر کاربر در حال بازی است
    if game.is_user_playing(user_id):
        await game.handle_game_message(message)
    # اگر کاربر در حال واریز است
    elif user_management.is_user_depositing(user_id):
        await user_management.handle_deposit_message(message)
    # اگر کاربر در حال برداشت است
    elif user_management.is_user_withdrawing(user_id):
        await user_management.handle_withdraw_message(message)
    # اگر پیام برای پشتیبانی است
    elif message.text and not message.text.startswith('/'):
        await message.answer("پیام شما برای پشتیبانی ارسال شد. در اسرع وقت با شما تماس خواهیم گرفت.")

async def main():
    # راه‌اندازی ربات
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())

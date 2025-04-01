from aiogram import types
from aiogram.dispatcher import FSMContext
from datetime import datetime, timedelta

class AdminStates(StatesGroup):
    waiting_for_bank_account = State()
    waiting_for_bet_limits = State()
    waiting_for_commission_rate = State()
    waiting_for_support_channel = State()

async def is_admin(user_id: int) -> bool:
    """بررسی ادمین بودن کاربر"""
    return user_id == int(os.getenv('ADMIN_ID'))

async def admin_command(message: types.Message):
    """دستور ادمین"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ شما دسترسی به این بخش را ندارید.")
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("📊 آمار کلی", callback_data="admin_stats"),
        types.InlineKeyboardButton("💳 تنظیم حساب بانکی", callback_data="admin_bank"),
        types.InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users"),
        types.InlineKeyboardButton("⚙️ تنظیمات شرط‌بندی", callback_data="admin_bettings"),
        types.InlineKeyboardButton("👥 سیستم معرف", callback_data="admin_referral"),
        types.InlineKeyboardButton("💬 تنظیمات پشتیبانی", callback_data="admin_support"),
        types.InlineKeyboardButton("🔄 وضعیت بازی", callback_data="admin_game_status")
    )
    
    await message.answer(
        "🔧 پنل مدیریت\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=keyboard
    )

async def get_admin_stats() -> dict:
    """دریافت آمار کلی سیستم"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # تعداد کل کاربران
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    
    # تعداد کاربران امروز
    today = datetime.now().date()
    cursor.execute('''
        SELECT COUNT(*) 
        FROM users 
        WHERE DATE(created_at) = %s
    ''', (today,))
    new_users_today = cursor.fetchone()[0]
    
    # آمار تراکنش‌ها
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN type = 'deposit' THEN amount ELSE 0 END) as total_deposits,
            SUM(CASE WHEN type = 'withdrawal' THEN amount ELSE 0 END) as total_withdrawals,
            SUM(CASE WHEN type = 'bet' THEN amount ELSE 0 END) as total_bets,
            SUM(CASE WHEN type = 'win' THEN amount ELSE 0 END) as total_wins
        FROM transactions
    ''')
    
    transactions = cursor.fetchone()
    
    # آمار روزانه
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN type = 'deposit' THEN amount ELSE 0 END) as daily_deposits,
            SUM(CASE WHEN type = 'withdrawal' THEN amount ELSE 0 END) as daily_withdrawals,
            SUM(CASE WHEN type = 'bet' THEN amount ELSE 0 END) as daily_bets,
            SUM(CASE WHEN type = 'win' THEN amount ELSE 0 END) as daily_wins
        FROM transactions
        WHERE DATE(created_at) = %s
    ''', (today,))
    
    daily_transactions = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return {
        'total_users': total_users,
        'new_users_today': new_users_today,
        'total_deposits': float(transactions[0] or 0),
        'total_withdrawals': float(transactions[1] or 0),
        'total_bets': float(transactions[2] or 0),
        'total_wins': float(transactions[3] or 0),
        'daily_deposits': float(daily_transactions[0] or 0),
        'daily_withdrawals': float(daily_transactions[1] or 0),
        'daily_bets': float(daily_transactions[2] or 0),
        'daily_wins': float(daily_transactions[3] or 0)
    }

async def handle_admin_stats(callback_query: types.CallbackQuery):
    """نمایش آمار کلی"""
    if not await is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ شما دسترسی به این بخش را ندارید.")
        return
    
    stats = await get_admin_stats()
    
    message = (
        "📊 آمار کلی سیستم\n\n"
        f"👥 تعداد کل کاربران: {stats['total_users']}\n"
        f"📈 کاربران جدید امروز: {stats['new_users_today']}\n\n"
        "💰 تراکنش‌های کلی:\n"
        f"واریز: {stats['total_deposits']:,.0f} تومان\n"
        f"برداشت: {stats['total_withdrawals']:,.0f} تومان\n"
        f"شرط‌ها: {stats['total_bets']:,.0f} تومان\n"
        f"بردها: {stats['total_wins']:,.0f} تومان\n\n"
        "📅 تراکنش‌های امروز:\n"
        f"واریز: {stats['daily_deposits']:,.0f} تومان\n"
        f"برداشت: {stats['daily_withdrawals']:,.0f} تومان\n"
        f"شرط‌ها: {stats['daily_bets']:,.0f} تومان\n"
        f"بردها: {stats['daily_wins']:,.0f} تومان"
    )
    
    await callback_query.message.edit_text(message)

async def handle_user_management(callback_query: types.CallbackQuery):
    """مدیریت کاربران"""
    if not await is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ شما دسترسی به این بخش را ندارید.")
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🔍 جستجوی کاربر", callback_data="admin_search_user"),
        types.InlineKeyboardButton("📊 لیست کاربران", callback_data="admin_list_users"),
        types.InlineKeyboardButton("🚫 کاربران مسدود شده", callback_data="admin_banned_users")
    )
    
    await callback_query.message.edit_text(
        "👥 مدیریت کاربران\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=keyboard
    )

async def handle_betting_settings(callback_query: types.CallbackQuery):
    """تنظیمات شرط‌بندی"""
    if not await is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ شما دسترسی به این بخش را ندارید.")
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("💰 حداقل و حداکثر شرط", callback_data="admin_bet_limits"),
        types.InlineKeyboardButton("🎯 ضریب‌های مراحل", callback_data="admin_stage_multipliers"),
        types.InlineKeyboardButton("⏰ زمان پاسخگویی", callback_data="admin_response_time")
    )
    
    await callback_query.message.edit_text(
        "⚙️ تنظیمات شرط‌بندی\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=keyboard
    ) 
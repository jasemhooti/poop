from aiogram import types
from aiogram.dispatcher import FSMContext
import random
import string
from datetime import datetime, timedelta

def generate_referral_code(length: int = 8) -> str:
    """تولید کد معرف تصادفی"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

async def get_user_balance(user_id: int) -> float:
    """دریافت موجودی کاربر"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT balance FROM users WHERE user_id = %s', (user_id,))
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return float(result[0]) if result else 0.0

async def update_user_balance(user_id: int, amount: float, transaction_type: str):
    """بروزرسانی موجودی کاربر و ثبت تراکنش"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # بروزرسانی موجودی
    if transaction_type in ['deposit', 'win']:
        cursor.execute('''
            UPDATE users 
            SET balance = balance + %s 
            WHERE user_id = %s
        ''', (amount, user_id))
    else:
        cursor.execute('''
            UPDATE users 
            SET balance = balance - %s 
            WHERE user_id = %s
        ''', (amount, user_id))
    
    # ثبت تراکنش
    cursor.execute('''
        INSERT INTO transactions (user_id, type, amount, status)
        VALUES (%s, %s, %s, 'completed')
    ''', (user_id, transaction_type, amount))
    
    conn.commit()
    cursor.close()
    conn.close()

async def handle_deposit(message: types.Message, state: FSMContext):
    """پردازش درخواست واریز"""
    try:
        amount = float(message.text)
        if amount < 10000:
            await message.answer("❌ حداقل مبلغ واریز 10,000 تومان است.")
            return
        
        await state.update_data(deposit_amount=amount)
        
        # نمایش اطلاعات حساب ادمین
        admin_account = "6037XXXXXXXXXXXX"  # شماره حساب ادمین
        await message.answer(
            f"💰 مبلغ {amount:,.0f} تومان را به شماره حساب زیر واریز کنید:\n"
            f"شماره حساب: {admin_account}\n"
            "پس از واریز، تصویر رسید را ارسال کنید.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        await state.set_state(DepositStates.waiting_for_receipt)
    except ValueError:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کنید.")

async def handle_withdrawal(message: types.Message, state: FSMContext):
    """پردازش درخواست برداشت"""
    try:
        amount = float(message.text)
        if amount < 50000:
            await message.answer("❌ حداقل مبلغ برداشت 50,000 تومان است.")
            return
        
        user_balance = await get_user_balance(message.from_user.id)
        if amount > user_balance:
            await message.answer("❌ موجودی شما کافی نیست.")
            return
        
        await state.update_data(withdrawal_amount=amount)
        
        await message.answer(
            "💳 لطفاً تصویر کارت بانکی خود را ارسال کنید.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        
        await state.set_state(WithdrawalStates.waiting_for_card)
    except ValueError:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کنید.")

async def get_user_stats(user_id: int) -> dict:
    """دریافت آمار کاربر"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # آمار کلی
    cursor.execute('''
        SELECT 
            COUNT(*) as total_bets,
            SUM(CASE WHEN type = 'win' THEN amount ELSE 0 END) as total_wins,
            SUM(CASE WHEN type = 'loss' THEN amount ELSE 0 END) as total_losses
        FROM transactions
        WHERE user_id = %s
    ''', (user_id,))
    
    stats = cursor.fetchone()
    
    # آمار روزانه
    today = datetime.now().date()
    cursor.execute('''
        SELECT 
            COUNT(*) as daily_bets,
            SUM(CASE WHEN type = 'win' THEN amount ELSE 0 END) as daily_wins
        FROM transactions
        WHERE user_id = %s AND DATE(created_at) = %s
    ''', (user_id, today))
    
    daily_stats = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return {
        'total_bets': stats[0] or 0,
        'total_wins': float(stats[1] or 0),
        'total_losses': float(stats[2] or 0),
        'daily_bets': daily_stats[0] or 0,
        'daily_wins': float(daily_stats[1] or 0)
    }

async def get_referral_stats(user_id: int) -> dict:
    """دریافت آمار سیستم معرف"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # تعداد کاربران معرفی شده
    cursor.execute('''
        SELECT COUNT(*) 
        FROM users 
        WHERE referred_by = %s
    ''', (user_id,))
    
    total_referrals = cursor.fetchone()[0]
    
    # مجموع کمیسیون دریافتی
    cursor.execute('''
        SELECT SUM(amount * 0.1) as commission
        FROM transactions
        WHERE user_id IN (
            SELECT user_id 
            FROM users 
            WHERE referred_by = %s
        )
        AND type = 'bet'
    ''', (user_id,))
    
    total_commission = float(cursor.fetchone()[0] or 0)
    
    cursor.close()
    conn.close()
    
    return {
        'total_referrals': total_referrals,
        'total_commission': total_commission
    } 
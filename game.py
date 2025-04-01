from aiogram import types
from aiogram.dispatcher import FSMContext
import random

# تنظیمات مراحل بازی
STAGES = {
    1: {'goals': 3, 'empty': 1, 'multiplier': 1.25},
    2: {'goals': 3, 'empty': 1, 'multiplier': 1.40},
    3: {'goals': 2, 'empty': 2, 'multiplier': 1.85},
    4: {'goals': 2, 'empty': 2, 'multiplier': 2.00},
    5: {'goals': 1, 'empty': 3, 'multiplier': 3.50}
}

async def create_game_keyboard(stage: int, bet_amount: float) -> types.InlineKeyboardMarkup:
    """ایجاد کیبورد شیشه‌ای برای مرحله بازی"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    # ایجاد آرایه‌ای از دکمه‌ها
    buttons = []
    stage_config = STAGES[stage]
    
    # اضافه کردن دکمه‌های هدف
    for i in range(stage_config['goals']):
        buttons.append(types.InlineKeyboardButton(
            text="🎯",
            callback_data=f"stage{stage}_goal_{i}"
        ))
    
    # اضافه کردن دکمه‌های خالی
    for i in range(stage_config['empty']):
        buttons.append(types.InlineKeyboardButton(
            text="⚪️",
            callback_data=f"stage{stage}_empty_{i}"
        ))
    
    # مخلوط کردن دکمه‌ها
    random.shuffle(buttons)
    
    # اضافه کردن دکمه‌ها به کیبورد
    keyboard.add(*buttons)
    
    # اضافه کردن دکمه برداشت در مراحل بعد از اول
    if stage > 1:
        keyboard.add(types.InlineKeyboardButton(
            text=f"💰 برداشت ({bet_amount * STAGES[stage-1]['multiplier']:.0f} تومان)",
            callback_data=f"cashout_{stage}"
        ))
    
    return keyboard

async def handle_stage_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """پردازش انتخاب کاربر در هر مرحله"""
    data = callback_query.data.split('_')
    stage = int(data[0].replace('stage', ''))
    choice_type = data[1]
    
    if choice_type == 'goal':
        # کاربر برنده شده است
        current_data = await state.get_data()
        bet_amount = current_data['bet_amount']
        new_amount = bet_amount * STAGES[stage]['multiplier']
        
        if stage == 5:
            # مرحله نهایی - برداشت خودکار
            await callback_query.message.edit_text(
                f"🎉 تبریک! شما برنده شدید!\n"
                f"مبلغ برنده شده: {new_amount:.0f} تومان",
                reply_markup=None
            )
            await state.finish()
            return new_amount
        else:
            # رفتن به مرحله بعدی
            await callback_query.message.edit_text(
                f"🎯 عالی! شما برنده شدید!\n"
                f"مبلغ فعلی: {new_amount:.0f} تومان\n"
                f"آیا می‌خواهید به مرحله {stage + 1} بروید؟",
                reply_markup=await create_game_keyboard(stage + 1, new_amount)
            )
            await state.update_data(bet_amount=new_amount)
            await state.set_state(f"waiting_for_stage{stage + 1}_choice")
            return None
    else:
        # کاربر باخته است
        await callback_query.message.edit_text(
            "😢 متأسفانه شما باختید!\n"
            "می‌توانید دوباره تلاش کنید.",
            reply_markup=None
        )
        await state.finish()
        return 0

async def handle_cashout(callback_query: types.CallbackQuery, state: FSMContext):
    """پردازش درخواست برداشت کاربر"""
    data = callback_query.data.split('_')
    stage = int(data[1])
    
    current_data = await state.get_data()
    bet_amount = current_data['bet_amount']
    cashout_amount = bet_amount * STAGES[stage-1]['multiplier']
    
    await callback_query.message.edit_text(
        f"💰 برداشت موفق!\n"
        f"مبلغ برداشت شده: {cashout_amount:.0f} تومان",
        reply_markup=None
    )
    await state.finish()
    return cashout_amount 
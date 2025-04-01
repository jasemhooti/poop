from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import asyncio
from user_management import UserManagement

class Game:
    def __init__(self):
        self.active_games = {}
        self.multipliers = {
            1: 1.2,
            2: 1.5,
            3: 2.0,
            4: 3.0,
            5: 5.0
        }
        self.user_management = UserManagement()
    
    def is_user_playing(self, user_id):
        return user_id in self.active_games
    
    async def start_game(self, message: types.Message):
        user_id = message.from_user.id
        user_balance = self.user_management.get_user_balance(user_id)
        
        if user_balance < 1000:
            await message.answer("موجودی شما برای شروع بازی کافی نیست. حداقل موجودی 1000 تومان است.")
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1000 تومان", callback_data="game_bet_1000")],
            [InlineKeyboardButton(text="5000 تومان", callback_data="game_bet_5000")],
            [InlineKeyboardButton(text="10000 تومان", callback_data="game_bet_10000")],
            [InlineKeyboardButton(text="مقدار دلخواه", callback_data="game_bet_custom")]
        ])
        
        await message.answer(
            "لطفاً مبلغ شرط خود را انتخاب کنید:",
            reply_markup=keyboard
        )
    
    async def process_game_callback(self, callback: types.CallbackQuery):
        user_id = callback.from_user.id
        data = callback.data.split('_')
        
        if data[1] == 'bet':
            await self.handle_bet_selection(callback)
        elif data[1] == 'stage':
            await self.handle_stage_selection(callback)
        elif data[1] == 'cashout':
            await self.handle_cashout(callback)
    
    async def handle_bet_selection(self, callback: types.CallbackQuery):
        user_id = callback.from_user.id
        data = callback.data.split('_')
        bet_amount = int(data[2]) if data[2] != 'custom' else None
        
        if bet_amount is None:
            await callback.message.answer("لطفاً مبلغ شرط خود را وارد کنید (حداقل 1000 تومان):")
            self.active_games[user_id] = {'state': 'waiting_bet_amount'}
            return
        
        if not self.user_management.check_balance(user_id, bet_amount):
            await callback.message.answer("موجودی شما کافی نیست!")
            return
        
        self.active_games[user_id] = {
            'bet_amount': bet_amount,
            'current_stage': 0,
            'current_multiplier': 1.0
        }
        
        await self.show_stage_selection(callback.message)
    
    async def show_stage_selection(self, message: types.Message):
        user_id = message.from_user.id
        game_data = self.active_games[user_id]
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎲 ادامه", callback_data="game_stage_continue")],
            [InlineKeyboardButton(text="💰 برداشت", callback_data="game_cashout")]
        ])
        
        await message.answer(
            f"مرحله {game_data['current_stage'] + 1} از 5\n"
            f"ضریب فعلی: {game_data['current_multiplier']}x\n"
            f"مبلغ احتمالی برداشت: {int(game_data['bet_amount'] * game_data['current_multiplier'])} تومان",
            reply_markup=keyboard
        )
    
    async def handle_stage_selection(self, callback: types.CallbackQuery):
        user_id = callback.from_user.id
        game_data = self.active_games[user_id]
        
        if random.random() < 0.7:  # 70% شانس موفقیت
            game_data['current_stage'] += 1
            game_data['current_multiplier'] = self.multipliers[game_data['current_stage']]
            
            if game_data['current_stage'] == 5:
                await self.handle_win(callback.message)
            else:
                await self.show_stage_selection(callback.message)
        else:
            await self.handle_loss(callback.message)
    
    async def handle_win(self, message: types.Message):
        user_id = message.from_user.id
        game_data = self.active_games[user_id]
        win_amount = int(game_data['bet_amount'] * game_data['current_multiplier'])
        
        self.user_management.add_balance(user_id, win_amount)
        del self.active_games[user_id]
        
        await message.answer(
            f"🎉 تبریک! شما برنده شدید!\n"
            f"مبلغ برداشت: {win_amount} تومان"
        )
    
    async def handle_loss(self, message: types.Message):
        user_id = message.from_user.id
        game_data = self.active_games[user_id]
        
        self.user_management.deduct_balance(user_id, game_data['bet_amount'])
        del self.active_games[user_id]
        
        await message.answer(
            "😢 متأسفانه باختید!\n"
            "می‌توانید دوباره تلاش کنید."
        )
    
    async def handle_cashout(self, callback: types.CallbackQuery):
        user_id = callback.from_user.id
        game_data = self.active_games[user_id]
        win_amount = int(game_data['bet_amount'] * game_data['current_multiplier'])
        
        self.user_management.add_balance(user_id, win_amount)
        del self.active_games[user_id]
        
        await callback.message.answer(
            f"💰 برداشت موفق!\n"
            f"مبلغ برداشت: {win_amount} تومان"
        )

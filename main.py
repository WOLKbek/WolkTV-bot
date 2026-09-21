import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from database import Database

TOKEN = "8613565014:AAEiV18aLpag0bW-8iheiJVHt1r-1RSzCoY"
ADMIN_ID = 6328059183  # Shu yerga o'zingizning Telegram ID'ingizni yozing

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Database("cinema_bot.db")

# Admin kino qo'shishi uchun FSM holatlari
class AddMovie(StatesGroup):
    waiting_for_video = State()
    waiting_for_code = State()
    waiting_for_title = State()
    waiting_for_desc = State()

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    await db.add_user(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username
    )
    
    text = (
        f"Assalomu alaykum, {message.from_user.full_name}!\n\n"
        f"🍿 **Kino botimizga xush kelibsiz!**\n"
        f"Kino ko'rish uchun uning **kodini** yuboring (Masalan: `101`):"
    )
    if message.from_user.id == ADMIN_ID:
        text += "\n\n⚙️ **Admin buyruqlari:**\n/addmovie — Yangi kino qo'shish"
        
    await message.answer(text, parse_mode="Markdown")

# ================= ADMIN PANEL =================
@dp.message(Command("addmovie"))
async def add_movie_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Bu buyruq faqat admin uchun!")
        return

    await state.set_state(AddMovie.waiting_for_video)
    await message.answer("🎥 Iltimos, kino **videosini** yuboring:")

@dp.message(AddMovie.waiting_for_video, F.video)
async def process_video(message: types.Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AddMovie.waiting_for_code)
    await message.answer("🔑 Endi kino uchun **unikal kod** kiriting (masalan: `101`):")

@dp.message(AddMovie.waiting_for_code)
async def process_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text)
    await state.set_state(AddMovie.waiting_for_title)
    await message.answer("🎬 Kino **nomini** kiriting:")

@dp.message(AddMovie.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddMovie.waiting_for_desc)
    await message.answer("📝 Kino haqida **qisqacha tavsif** (yoki janri) yozing:")

@dp.message(AddMovie.waiting_for_desc)
async def process_desc(message: types.Message, state: FSMContext):
    data = await state.get_data()
    success = await db.add_movie(
        code=data['code'],
        title=data['title'],
        description=message.text,
        file_id=data['file_id']
    )
    
    if success:
        await message.answer(f"✅ **Kino muvaffaqiyatli saqlandi!**\n\n🔑 Kodi: `{data['code']}`\n🎬 Nomi: {data['title']}", parse_mode="Markdown")
    else:
        await message.answer("❌ Xatolik! Bu kod allaqachon boshqa kinoga berilgan.")
    
    await state.clear()

# ================= KINO QIDIRISH =================
@dp.message(F.text.isdigit())
async def get_movie(message: types.Message):
    code = message.text
    movie = await db.get_movie_by_code(code)

    if movie:
        caption_text = (
            f"🎬 **{movie['title']}**\n\n"
            f"📝 {movie['description']}\n\n"
            f"🔑 Kino kodi: `{movie['code']}`\n"
            f"👁 Ko'rishlar: {movie['views']} marta"
        )
        await message.answer_video(
            video=movie['file_id'],
            caption=caption_text,
            parse_mode="Markdown"
        )
    else:
        await message.answer("❌ Ushbu kod bo'yicha hech qanday kino topilmadi.")

from aiohttp import web

# Render port talab qilgani uchun soxta veb-server
async def handle(request):
    return web.Response(text="Bot ishlamoqda!")

async def main():
    await db.init_db()
    
    # Render beradigan portni olish
    port = int(os.getenv("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    
    # Veb-server va botni birga ishga tushirish
    await asyncio.gather(
        site.start(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())

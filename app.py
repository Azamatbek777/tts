import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
import uuid
from f5_tts import F5TTS

# ================= SOZLAMALAR =================
TOKEN = "8034346294:AAE53a_P73UK_oXP15gnBH1hlXiB5hKUZ74"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# F5-TTS ni yuklash
print("F5-TTS yuklanmoqda... (birinchi marta biroz vaqt oladi)")
tts = F5TTS()

USER_VOICES = {}
os.makedirs("voices", exist_ok=True)
os.makedirs("output", exist_ok=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 F5-TTS Voice Clone botga xush kelibsiz!\n\n"
        "1. Ovoz yuboring (5-15 soniya)\n"
        "2. Matn yozing\n"
        "Bot sizning ovozingiz bilan o‘qiydi.\n"
        "Yengil va sifatli!"
    )

@dp.message(types.ContentType.VOICE)
async def handle_voice(message: types.Message):
    user_id = message.from_user.id
    file = await bot.get_file(message.voice.file_id)
    
    path = f"voices/{user_id}_{uuid.uuid4()}.ogg"
    await bot.download_file(file.file_path, path)
    
    wav_path = path.replace(".ogg", ".wav")
    os.system(f"ffmpeg -i {path} -ar 22050 -ac 1 {wav_path} -y")
    
    USER_VOICES[user_id] = wav_path
    await message.answer("✅ Ovozingiz qabul qilindi! Endi matn yozing.")

@dp.message()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    if user_id not in USER_VOICES:
        await message.answer("❌ Avval ovoz yuboring!")
        return
    
    text = message.text.strip()
    if len(text) < 5:
        await message.answer("Matn juda qisqa.")
        return
    
    await message.answer("⏳ Audio yaratilmoqda...")
    
    try:
        output_path = f"output/{user_id}_{uuid.uuid4()}.wav"
        
        # F5-TTS bilan generatsiya
        tts.infer(
            text=text,
            ref_audio=USER_VOICES[user_id],
            output_path=output_path
        )
        
        audio = FSInputFile(output_path)
        await message.answer_voice(voice=audio)
        
    except Exception as e:
        await message.answer(f"Xatolik: {str(e)}")

async def main():
    print("✅ Bot ishga tushdi (F5-TTS)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

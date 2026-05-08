import os
import logging
import asyncio
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from TTS.api import TTS
from pydub import AudioSegment

# ---------- Sozlash ----------
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = os.getenv("BOT_TOKEN")          # Space'ning Settings → Secrets’da
# WEBHOOK_URL endi kerak emas!

VOICE_STORAGE = Path("voice_samples")
VOICE_STORAGE.mkdir(exist_ok=True)
user_voice: dict[int, Path] = {}

# ---------- FastAPI hayotiy sikli (polling bilan) ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """TTS modelini yuklaymiz va botni polling rejimida ishga tushiramiz."""
    print("🔄 TTS model yuklanmoqda...")
    app.state.tts = TTS(
        model_name="tts_models/multilingual/multi-dataset/your_tts",
        gpu=False,
    )
    print("✅ Model tayyor!")

    # Telegram botni yaratish
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.AUDIO | filters.VOICE, handle_voice_sample)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    # Botni ishga tushirish (polling)
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    app.state.application = application

    print("🤖 Bot polling rejimida ishlayapti...")
    yield

    # To‘xtatish
    await application.updater.stop()
    await application.stop()
    await application.shutdown()

app = FastAPI(lifespan=lifespan)

# ---------- Handlerlar (o‘zgarishsiz) ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum!\n"
        "1️⃣ Avval ovozingiz yozilgan MP3 yoki ovozli xabar yuboring.\n"
        "2️⃣ Keyin men sizga qanday matn o‘qishimni so‘rang."
    )

async def handle_voice_sample(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Foydalanuvchi yuborgan audio/ovozli xabarni qabul qilib,
    uni wav formatga o‘tkazamiz va saqlaymiz."""
    user_id = update.effective_user.id

    if update.message.voice:
        file = await update.message.voice.get_file()
    elif update.message.audio:
        file = await update.message.audio.get_file()
    else:
        return

    download_path = VOICE_STORAGE / f"{user_id}_original{Path(file.file_path).suffix}"
    wav_path = VOICE_STORAGE / f"{user_id}_reference.wav"

    await file.download_to_drive(download_path)

    # ffmpeg bilan 16kHz mono wav ga o‘girish
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", str(download_path),
                "-ar", "16000",
                "-ac", "1",
                "-sample_fmt", "s16",
                str(wav_path),
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        await update.message.reply_text("Faylni qayta ishlashda xatolik yuz berdi.")
        logging.error(f"ffmpeg error: {e.stderr.decode()}")
        return
    finally:
        download_path.unlink(missing_ok=True)

    # Davomiylikni tekshirish (kamida 2 soniya)
    try:
        audio = AudioSegment.from_wav(wav_path)
        if len(audio) < 2000:
            await update.message.reply_text(
                "Ovoz namunasi juda qisqa (kamida 2 soniya). Iltimos, uzunroq ovoz yuboring."
            )
            return
    except Exception as e:
        logging.error(f"AudioSegment error: {e}")
        await update.message.reply_text("Audio faylni tahlil qilib bo‘lmadi.")
        return

    user_voice[user_id] = wav_path
    await update.message.reply_text(
        "✅ Ovoz namunasi saqlandi. Endi menga o‘qishim kerak bo‘lgan matnni yuboring."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Matnni saqlangan ovoz namunasi asosida o‘qiydi."""
    user_id = update.effective_user.id
    text = update.message.text
    if not text or len(text) > 500:
        await update.message.reply_text("Matn juda uzun yoki bo‘sh.")
        return

    if user_id not in user_voice:
        await update.message.reply_text(
            "Iltimos, avval ovoz namunangizni MP3 yoki ovozli xabar ko‘rinishida yuboring."
        )
        return

    tts = app.state.tts
    output_path = VOICE_STORAGE / f"{user_id}_output.wav"

    tts.tts_to_file(
        text=text,
        speaker_wav=str(user_voice[user_id]),
        file_path=str(output_path),
    )

    with open(output_path, "rb") as voice:
        await update.message.reply_voice(voice=voice)

    output_path.unlink(missing_ok=True)


# Uvicorn ishga tushirish (oddiy)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

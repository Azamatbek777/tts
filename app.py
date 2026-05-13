import os
import telebot
from TTS.api import TTS

# 1. Telegram bot tokenni kiriting
BOT_TOKEN = "8034346294:AAE53a_P73UK_oXP15gnBH1hlXiB5hKUZ74"
bot = telebot.TeleBot(BOT_TOKEN)

# 2. Coqui TTS modelini yuklash (XTTS v2 modeli ko'p tillarni qo'llab-quvvatlaydi)
print("Coqui TTS modeli yuklanmoqda, kuting...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False) 
print("Model muvaffaqiyatli yuklandi!")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Menga istalgan matnni yuboring, men uni ovozli xabarga aylantirib beraman.")

@bot.message_handler(func=lambda message: True)
def text_to_voice_message(message):
    text_input = message.text
    chat_id = message.chat.id
    output_audio = f"voice_{chat_id}.wav"
    
    bot.send_chat_action(chat_id, 'record_voice')
    
    try:
        # Matnni ovozga aylantirish (Siz o'zbek tili uchun 'uz' yoki ingliz tili uchun 'en' qilishingiz mumkin)
        # speaker_wav parametri uchun kompyuteringizdagi qisqa 10 soniyali ovoz namunasini ko'rsatsangiz, o'sha ovozda gapiradi.
        tts.tts_to_file(
            text=text_input, 
            file_path=output_audio,
            speaker_wav="sample.wav", # Agar o'z ovozingizni klonlamoqchi bo'lsangiz, shu faylni tayyorlang
            language="uz"
        )
        
        # Ovozli xabarni Telegram'ga yuborish
        with open(output_audio, 'rb') as voice:
            bot.send_voice(chat_id, voice)
            
        # Vaqtinchalik faylni o'chirish
        os.remove(output_audio)
        
    except Exception as e:
        bot.reply_to(message, f"Xatolik yuz berdi: {str(e)}")

# Botni uzluksiz ishga tushirish
bot.polling(none_stop=True)

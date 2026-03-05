import telebot
import os
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

# --- AYARLAR ---
TOKEN = "8665678953:AAHiiMPf6BZM0HVZ0SNwV7XzQNfbElFCp6I"  # Kendi tokenini buraya yapıştır
bot = telebot.TeleBot(TOKEN)
LOGO_PATH = "logo.png"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Selam! Fotoğraf veya video gönder, logonu ekleyeyim.")

# --- VİDEO İŞLEME KISMI ---
@bot.message_handler(content_types=['video'])
def handle_video(message):
    try:
        msg = bot.reply_to(message, "🎬 Video işleniyor... Bu işlem 1-2 dakika sürebilir.")
        
        # 1. Videoyu sunucuya indir
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        input_name = f"in_{message.chat.id}.mp4"
        output_name = f"out_{message.chat.id}.mp4"

        with open(input_name, 'wb') as f:
            f.write(downloaded_file)

        # 2. MoviePy ile işle (Hızlı mod)
        clip = VideoFileClip(input_name)
        
        # Logo ayarı (Genişliğin %15'i kadar, sağ alt köşe)
        logo = (ImageClip(LOGO_PATH)
                .set_duration(clip.duration)
                .resize(width=clip.w * 0.15) 
                .set_pos(("right", "bottom")))

        final = CompositeVideoClip([clip, logo])
        
        # 3. Kaydet (Ultrafast ayarı Koyeb için çok önemli)
        final.write_videofile(output_name, codec="libx264", audio_codec="aac", fps=24, preset="ultrafast", threads=4)

        # 4. Gönder
        with open(output_name, 'rb') as v:
            bot.send_video(message.chat.id, v, caption="✅ Videon hazır!")
        
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ Hata: {str(e)}")
    finally:
        # Temizlik (Sunucuda yer kaplamasın)
        clip.close() # Önce klibi kapat
        if os.path.exists(input_name): os.remove(input_name)
        if os.path.exists(output_name): os.remove(output_name)

# --- FOTOĞRAF İŞLEME KISMI ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "Fotoğraf özelliğin zaten çalışıyor, aynen devam!")

bot.polling()

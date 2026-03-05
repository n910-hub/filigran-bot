import telebot
import os
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

# --- AYARLAR ---
TOKEN = "8665678953:AAHiiMPf6BZM0HVZ0SNwV7XzQNfbElFCp6I"  # Kendi bot tokenini buraya yaz
bot = telebot.TeleBot(TOKEN)
LOGO_PATH = "logo.png"  # Logonun adının tam olarak bu olduğundan emin ol

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Selam! Logo eklemem için bana bir video veya fotoğraf gönder.")

# --- VİDEO İŞLEME KISMI ---
@bot.message_handler(content_types=['video'])
def handle_video(message):
    try:
        msg = bot.reply_to(message, "🎬 Video işleniyor... Bu işlem videonun boyutuna göre biraz sürebilir.")
        
        # Videoyu indir
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open("input_video.mp4", 'wb') as new_file:
            new_file.write(downloaded_file)

        # MoviePy ile logoyu ekle
        video = VideoFileClip("input_video.mp4")
        
        # Logoyu hazırla (Sağ üst köşe, video genişliğinin %20'si kadar boyut)
        logo = (ImageClip(LOGO_PATH)
                .set_duration(video.duration)
                .resize(width=video.w * 0.20) 
                .set_pos(("right", "top")))

        # Videoyu ve logoyu birleştir
        final_video = CompositeVideoClip([video, logo])
        
        # Videoyu kaydet (Koyeb için en hızlı ayarlar)
        final_video.write_videofile("output_video.mp4", codec="libx264", audio_codec="aac", fps=24, preset="ultrafast")

        # Gönder
        with open("output_video.mp4", 'rb') as video_send:
            bot.send_video(message.chat.id, video_send, caption="✅ Logonuz eklendi!")
        
        bot.delete_message(message.chat.id, msg.message_id)

    except Exception as e:
        bot.reply_to(message, f"❌ Hata oluştu: {str(e)}")
    finally:
        # Sunucuda yer kaplamasın diye dosyaları temizle
        if os.path.exists("input_video.mp4"): os.remove("input_video.mp4")
        if os.path.exists("output_video.mp4"): os.remove("output_video.mp4")

# --- FOTOĞRAF İŞLEME KISMI ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    # Fotoğraf işleme kodun zaten çalıştığı için burayı sade tutabilirsin
    bot.reply_to(message, "Fotoğraf işleme özelliği de aktif!")

bot.polling()

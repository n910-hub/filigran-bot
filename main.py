import telebot
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
import os
from threading import Timer
from PIL import Image
from moviepy.config import change_settings

# --- WINDOWS SUNUCU AYARI ---
# Eğer ImageMagick klasör adın farklıysa (örneğin 7.1.0 ise) aşağıdaki yolu ona göre düzelt!
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

# --- BOT AYARLARI ---
TOKEN = '8665678953:AAHiiMPf6BZM0HVZ0SNwV7XzQNfbElFCp6I'
LOGO_PATH = "logo.png" # Klasörde logo.png adında bir dosya olmalı
media_groups = {}

bot = telebot.TeleBot(TOKEN)

def process_album(chat_id, group_id):
    files = media_groups.get(group_id, [])
    if not files: return
    
    sent_msg = bot.send_message(chat_id, "💎 Sunucu gücüyle yüksek kalitede işleniyor...")
    processed_media = []

    for file_id, file_type in files:
        try:
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            input_path = f"in_{file_id}"
            output_path = f"out_{file_id}.mp4"

            with open(input_path, "wb") as f:
                f.write(downloaded_file)

            if file_type == 'video':
                # SUNUCU İÇİN FULL KALİTE AYARLARI
                video = VideoFileClip(input_path) 
                # Logo boyutunu videonun yüksekliğinin 12'de 1'i yapıyoruz
                logo = ImageClip(LOGO_PATH).set_duration(video.duration).resize(height=video.h // 12)
                
                def bounce_pos(t):
                    vx, vy = video.w * 0.3, video.h * 0.3
                    x = (vx * t) % (2 * (video.w - logo.w))
                    y = (vy * t) % (2 * (video.h - logo.h))
                    if x > video.w - logo.w: x = 2 * (video.w - logo.w) - x
                    if y > video.h - logo.h: y = 2 * (video.h - logo.h) - y
                    return (x, y)

                final = CompositeVideoClip([video, logo.set_pos(bounce_pos)])
                
                # Preset="slow" ile en net görüntüyü elde ediyoruz
                final.write_videofile(output_path, codec="libx264", audio_codec="aac", 
                                    preset="slow", logger=None)
                
                processed_media.append(telebot.types.InputMediaVideo(open(output_path, "rb")))
                video.close()
                final.close()

            elif file_type == 'photo':
                # Resim üzerine logo ekleme
                base = Image.open(input_path).convert("RGBA")
                logo_img = Image.open(LOGO_PATH).convert("RGBA")
                w_w = int(base.width * 0.15)
                w_h = int(logo_img.height * (w_w / logo_img.width))
                logo_img = logo_img.resize((w_w, w_h))
                base.paste(logo_img, (base.width - w_w - 10, base.height - w_h - 10), logo_img)
                base.convert("RGB").save(f"out_{file_id}.jpg")
                processed_media.append(telebot.types.InputMediaPhoto(open(f"out_{file_id}.jpg", "rb")))

            if os.path.exists(input_path): os.remove(input_path)
        except Exception as e:
            print(f"Hata detayı: {e}")

    if processed_media:
        try:
            bot.send_media_group(chat_id, processed_media)
            bot.delete_message(chat_id, sent_msg.message_id)
        except Exception as e:
            print(f"Gönderme hatası: {e}")
            
    # Temizlik
    del media_groups[group_id]

@bot.message_handler(content_types=['video', 'photo'])
def handle_media(message):
    file_id = message.video.file_id if message.content_type == 'video' else message.photo[-1].file_id
    if message.media_group_id:
        if message.media_group_id not in media_groups:
            media_groups[message.media_group_id] = []
            Timer(5.0, process_album, [message.chat.id, message.media_group_id]).start()
        media_groups[message.media_group_id].append((file_id, message.content_type))
    else:
        media_groups[f"s_{file_id}"] = [(file_id, message.content_type)]
        process_album(message.chat.id, f"s_{file_id}")

print("🚀 Bot sunucu üzerinde aktif! Telegram'dan video bekliyor...")
bot.polling(none_stop=True)

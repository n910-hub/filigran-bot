import telebot
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
import os
import time
from threading import Timer
from PIL import Image

# --- AYARLAR ---
TOKEN = '8665678953:AAHiiMPf6BZM0HVZ0SNwV7XzQNfbElFCp6I' # BotFather'dan aldığın kod
LOGO_PATH = "logo.png"
media_groups = {}
# ----------------

bot = telebot.TeleBot(TOKEN)

def process_album(chat_id, group_id):
    files = media_groups.get(group_id, [])
    if not files: return
    
    sent_msg = bot.send_message(chat_id, f"📦 {len(files)} dosya işleniyor...")
    processed_media = []

    for file_id, file_type in files:
        try:
            file_info = bot.get_file(file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            input_path = f"in_{file_id}"
            output_path = f"out_{file_id}"

            with open(input_path, "wb") as f:
                f.write(downloaded_file)

            if file_type == 'video':
                video = VideoFileClip(input_path)
                logo = (ImageClip(LOGO_PATH).set_duration(video.duration)
                        .resize(height=video.h // 12))
                
                def bounce_pos(t):
                    v_x, v_y = video.w * 0.3, video.h * 0.3 
                    x = (v_x * t) % (2 * (video.w - logo.w))
                    y = (v_y * t) % (2 * (video.h - logo.h))
                    if x > video.w - logo.w: x = 2 * (video.w - logo.w) - x
                    if y > video.h - logo.h: y = 2 * (video.h - logo.h) - y
                    return (x, y)

                final_video = CompositeVideoClip([video, logo.set_pos(bounce_pos)])
                final_video.write_videofile(f"{output_path}.mp4", codec="libx264", audio_codec="aac", logger=None)
                processed_media.append(telebot.types.InputMediaVideo(open(f"{output_path}.mp4", "rb")))
                video.close()

            elif file_type == 'photo':
                base_img = Image.open(input_path).convert("RGBA")
                watermark = Image.open(LOGO_PATH).convert("RGBA")
                w_width = int(base_img.width * 0.15)
                w_height = int(watermark.height * (w_width / watermark.width))
                watermark = watermark.resize((w_width, w_height))
                base_img.paste(watermark, (base_img.width - w_width - 10, base_img.height - w_height - 10), watermark)
                base_img.convert("RGB").save(f"{output_path}.jpg")
                processed_media.append(telebot.types.InputMediaPhoto(open(f"{output_path}.jpg", "rb")))

            if os.path.exists(input_path): os.remove(input_path)
        except Exception as e:
            print(f"Hata: {e}")

    if processed_media:
        bot.send_media_group(chat_id, processed_media)
        bot.delete_message(chat_id, sent_msg.message_id)
    del media_groups[group_id]

@bot.message_handler(content_types=['video', 'photo'])
def handle_media(message):
    file_id = message.video.file_id if message.content_type == 'video' else message.photo[-1].file_id
    file_type = message.content_type
    if message.media_group_id:
        if message.media_group_id not in media_groups:
            media_groups[message.media_group_id] = []
            Timer(3.0, process_album, [message.chat.id, message.media_group_id]).start()
        media_groups[message.media_group_id].append((file_id, file_type))
    else:
        temp_id = f"single_{file_id}"
        media_groups[temp_id] = [(file_id, file_type)]
        process_album(message.chat.id, temp_id)

bot.polling()

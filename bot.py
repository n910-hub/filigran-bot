import asyncio, json, os
from telethon import TelegramClient, events, Button, types

# --- AYARLAR ---
api_id = 31223166
api_hash = '13bfee454a0f62d5fb50b165dc99f534'
bot_token = '8775729202:AAEDVWvntZSotMb53a9948jwull1BgO5Dok'
admin_id = 8541338949 

user_client = TelegramClient('user_session', api_id, api_hash)
bot_client = TelegramClient('bot_session', api_id, api_hash)

DB_FILE = "data.json"
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {
        "src": "Seçilmedi", "src_topic": "0", "trgt": "Seçilmedi", "trgt_topic": "0",
        "delay": 2.0, "min_id": "0", "bad_words": [], 
        "signature": "🚀 YerliTube", "sig_on": False
    }

data = load_data()
data.update({"running": False, "total": 0, "current": 0, "panel_id": None})

def save_data():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- PANEL ARAYÜZÜ ---
async def get_menu_ui():
    status = "🟢 AKTİF" if data['running'] else "🔴 DURDURULDU"
    sig_status = "AÇIK" if data['sig_on'] else "KAPALI"
    text = (
        f"**🔥 v81 Tam Teçhizatlı Sürüm (Albüm Destekli)**\n"
        f"----------------------------------\n"
        f"**📂 KAYNAK:** `{data['src']}` (Konu: `{data['src_topic']}`)\n"
        f"**🎯 HEDEF:** `{data['trgt']}` (Konu: `{data['trgt_topic']}`)\n"
        f"**⏳ GECİKME:** `{data['delay']} sn` | **📍 MİN ID:** `{data['min_id']}`\n"
        f"**✍️ İMZA:** `{data['signature']}` ({sig_status})\n"
        f"**🚫 FİLTRE:** `{len(data['bad_words'])} kelime`\n"
        f"----------------------------------\n"
        f"**📊 İLERLEME:** `{data['current']}/{data['total']}`\n"
        f"**DURUM:** {status}"
    )
    btns = [
        [Button.inline("📂 Kaynak Seç", b"set_src"), Button.inline("🎯 Hedef Seç", b"set_trgt")],
        [Button.inline("📂 K. Konu ID", b"set_s_topic"), Button.inline("🎯 H. Konu ID", b"set_t_topic")],
        [Button.inline("✍️ İmza Düzenle", b"set_sig"), Button.inline(f"İmza {'KAPAT' if data['sig_on'] else 'AÇ'}", b"toggle_sig")],
        [Button.inline("➕ Filtre Ekle", b"add_bad"), Button.inline("❌ Filtre Sil", b"del_bad"), Button.inline("📋 F. Liste", b"list_bad")],
        [Button.inline("⏳ Gecikme", b"set_delay"), Button.inline("📍 Başlangıç ID", b"set_min_id")],
        [Button.inline("🚀 BAŞLAT" if not data['running'] else "🛑 DURDUR", b"start" if not data['running'] else "stop")]
    ]
    return text, btns

async def refresh_panel():
    if not data['panel_id']: return
    text, btns = await get_menu_ui()
    try: await bot_client.edit_message(admin_id, data['panel_id'], text, buttons=btns)
    except: pass

# --- TRANSFER MOTORU ---
async def engine():
    try:
        s_id, t_id = int(data['src']), int(data['trgt'])
        s_topic = int(data['src_topic']) if data['src_topic'] != "0" else None
        t_topic = int(data['trgt_topic']) if data['trgt_topic'] != "0" else None
        
        all_msgs = await user_client.get_messages(s_id, min_id=int(data['min_id']), reply_to=s_topic)
        data['total'] = all_msgs.total
        data['current'] = 0
        
        # ALBÜM HAFIZASI
        album_media = []
        album_caption = ""
        current_grouped_id = None

        async def flush_album():
            nonlocal album_media, album_caption, current_grouped_id
            if not album_media: return
            
            # İmza İşlemi
            final_cap = album_caption
            if data['sig_on'] and data['signature']:
                final_cap = f"{final_cap}\n\n{data['signature']}" if final_cap else data['signature']

            try:
                # Toplu halde tek mesaj (albüm) olarak gönder
                await user_client.send_file(t_id, album_media, caption=final_cap, reply_to=t_topic)
                data['current'] += len(album_media)
                if data['current'] % 5 == 0: await refresh_panel()
                await asyncio.sleep(float(data['delay']))
            except Exception as e:
                pass
            
            # Hafızayı sıfırla
            album_media = []
            album_caption = ""
            current_grouped_id = None

        async for msg in user_client.iter_messages(s_id, min_id=int(data['min_id']), reverse=True, reply_to=s_topic):
            if not data['running']: break
            if isinstance(msg, types.MessageService): continue
            
            msg_text = msg.text or ""
            
            # 1. KELİME FİLTRESİ KONTROLÜ
            skip = False
            for bad_word in data['bad_words']:
                if bad_word.lower() in msg_text.lower():
                    skip = True
                    break
            if skip: continue
            
            # 2. ALBÜM KONTROLÜ
            if msg.grouped_id:
                if msg.grouped_id != current_grouped_id:
                    await flush_album() # Önceki albümü yolla
                    current_grouped_id = msg.grouped_id
                
                album_media.append(msg.media)
                if msg_text and not album_caption: 
                    album_caption = msg_text # Albümdeki ilk metni açıklama olarak al
            else:
                await flush_album() # Bekleyen albüm varsa yolla
                
                # Tekil Mesaj İşlemi
                final_text = msg_text
                if data['sig_on'] and data['signature']:
                    final_text = f"{final_text}\n\n{data['signature']}" if final_text else data['signature']
                
                try:
                    if msg.media:
                        await user_client.send_file(t_id, msg.media, caption=final_text, reply_to=t_topic)
                    else:
                        if final_text:
                            await user_client.send_message(t_id, final_text, reply_to=t_topic)
                    
                    data['current'] += 1
                    if data['current'] % 5 == 0: await refresh_panel()
                    await asyncio.sleep(float(data['delay']))
                except: pass
        
        # Döngü bittiğinde içeride son kalan albüm varsa onu da yolla
        await flush_album()
        
        data['running'] = False
        await refresh_panel()
    except: data['running'] = False

# --- ETKİLEŞİM VE HAYALET MOD ---
@bot_client.on(events.NewMessage(pattern='/start', from_users=admin_id))
async def start_handler(event):
    text, btns = await get_menu_ui()
    msg = await event.respond(text, buttons=btns)
    data['panel_id'] = msg.id

@bot_client.on(events.CallbackQuery(chats=admin_id))
async def callback_handler(event):
    await event.answer()
    d = event.data

    async def ask_user(label, key, is_list=False):
        async with bot_client.conversation(admin_id) as conv:
            q = await conv.send_message(f"💬 **{label}** gönder kanka:")
            res = await conv.get_response()
            val = res.text.strip()
            
            if is_list:
                if val not in data[key]: data[key].append(val)
            else:
                data[key] = val
                
            save_data()
            conf = await conv.send_message(f"✅ İşlem tamam!")
            await asyncio.sleep(4)
            try: await bot_client.delete_messages(admin_id, [q.id, res.id, conf.id])
            except: pass
            await refresh_panel()

    if d == b"set_src": await ask_user("Kaynak Kanal ID", "src")
    elif d == b"set_trgt": await ask_user("Hedef Kanal ID", "trgt")
    elif d == b"set_s_topic": await ask_user("Kaynak Konu ID (Yoksa 0)", "src_topic")
    elif d == b"set_t_topic": await ask_user("Hedef Konu ID (Yoksa 0)", "trgt_topic")
    elif d == b"set_delay": await ask_user("Gecikme (sn)", "delay")
    elif d == b"set_min_id": await ask_user("Başlangıç ID", "min_id")
    elif d == b"set_sig": await ask_user("Yeni İmzanı", "signature")
    elif d == b"toggle_sig": 
        data['sig_on'] = not data['sig_on']
        save_data()
        await refresh_panel()
    elif d == b"add_bad": await ask_user("Yasaklanacak Kelimeyi", "bad_words", is_list=True)
    elif d == b"del_bad":
        async with bot_client.conversation(admin_id) as conv:
            q = await conv.send_message("🗑️ Silinecek kelimeyi yaz:")
            res = await conv.get_response()
            val = res.text.strip()
            if val in data['bad_words']: data['bad_words'].remove(val)
            save_data()
            conf = await conv.send_message("✅ Kelime silindi!")
            await asyncio.sleep(4)
            try: await bot_client.delete_messages(admin_id, [q.id, res.id, conf.id])
            except: pass
            await refresh_panel()
    elif d == b"list_bad":
        word_list = "\n".join([f"- {w}" for w in data['bad_words']]) if data['bad_words'] else "Filtre boş."
        msg = await bot_client.send_message(admin_id, f"📋 **Filtre Listesi:**\n{word_list}")
        await asyncio.sleep(7)
        try: await bot_client.delete_messages(admin_id, [msg.id])
        except: pass
    elif d == b"start": data['running'] = True; asyncio.create_task(engine()); await refresh_panel()
    elif d == b"stop": data['running'] = False; await refresh_panel()

async def main():
    print("\n✅ BOT AKTİF VE ÇALIŞIYOR! (Panelden kontrol edebilirsin)\n")
    await user_client.start()
    await bot_client.start(bot_token=bot_token)
    await asyncio.gather(user_client.run_until_disconnected(), bot_client.run_until_disconnected())

if __name__ == '__main__':
    asyncio.run(main())

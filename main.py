import os
import time
import shutil
import zipfile
from pyrogram import Client, filters
from pyrogram.types import Message

# Configuración segura
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Carpeta temporal obligatoria para servidores como Koyeb
DOWNLOAD_DIR = "/tmp/downloads/"

app = Client(
    "bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
    # Añadimos esto para forzar que ignore sesiones viejas
    takeout=False 
)

async def progress(current, total, message, start_time, action):
    now = time.time()
    diff = now - start_time
    if round(diff % 4.00) == 0 or current == total:
        percentage = current * 100 / total
        completed = int(percentage / 10)
        bar = "█" * completed + "░" * (10 - completed)
        try:
            await message.edit_text(f"**{action}**\n`{bar}` {percentage:.2f}%")
        except: pass

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("✅ **¡Bot activo y escuchando!** Envíame cualquier archivo.")

# Filtro ampliado para capturar TODO
@app.on_message(filters.all & ~filters.service)
async def handle_everything(client, message: Message):
    # Log para ver en Koyeb que el mensaje llegó
    print(f"DEBUG: Recibido mensaje de tipo: {message.media}")

    if not (message.document or message.video or message.audio or message.photo):
        return

    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    status = await message.reply_text("⏳ Procesando...")
    start_time = time.time()
    
    try:
        # Descarga
        file_path = await message.download(
            file_name=DOWNLOAD_DIR,
            progress=progress,
            progress_args=(status, start_time, "📥 Descargando...")
        )
        
        filename = os.path.basename(file_path)
        
        if filename.lower().endswith(".zip"):
            await status.edit_text("📂 **Extrayendo...**")
            extract_path = os.path.join(DOWNLOAD_DIR, f"ext_{int(time.time())}")
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            for root, _, files in os.walk(extract_path):
                for f in files:
                    f_path = os.path.join(root, f)
                    ext = f.lower().split('.')[-1]
                    # Envío inteligente
                    if ext in ['jpg', 'jpeg', 'png']: await message.reply_photo(f_path)
                    elif ext in ['mp4', 'mkv']: await message.reply_video(f_path)
                    elif ext in ['mp3', 'wav']: await message.reply_audio(f_path)
                    else: await message.reply_document(f_path)
            
            shutil.rmtree(extract_path)
        else:
            await status.edit_text("📦 **Comprimiendo...**")
            zip_name = file_path + ".zip"
            with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zip_f:
                zip_f.write(file_path, filename)
            await message.reply_document(zip_name)
            if os.path.exists(zip_name): os.remove(zip_name)

    except Exception as e:
        await message.reply_text(f"❌ Error: {e}")
        print(f"ERROR: {e}")

    if os.path.exists(file_path): os.remove(file_path)
    await status.delete()

print("🚀 BOT INICIADO Y LISTO")
app.run()

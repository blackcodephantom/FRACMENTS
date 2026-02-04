import os
import time
import shutil
import zipfile
from pyrogram import Client, filters
from pyrogram.types import Message

# Configuración mediante Variables de Entorno (Koyeb)
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

DOWNLOAD_DIR = "downloads/"

def get_progress_bar(current, total):
    percentage = current * 100 / total
    completed = int(percentage / 10)
    bar = "█" * completed + "░" * (10 - completed)
    return f"`{bar}` {percentage:.2f}%"

async def progress(current, total, message, start_time, action):
    now = time.time()
    diff = now - start_time
    # Actualiza cada 3 segundos para evitar ban de Telegram
    if round(diff % 3.00) == 0 or current == total:
        prog_bar = get_progress_bar(current, total)
        try:
            await message.edit_text(f"**{action}**\n{prog_bar}")
        except:
            pass

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text("👋 **¡Hola! Soy tu bot de gestión de archivos.**\n\n"
                             "• Envíame un archivo para comprimirlo a .zip\n"
                             "• Envíame un .zip para extraerlo y recibir los archivos según su tipo.")

@app.on_message(filters.document | filters.video | filters.audio | filters.photo)
async def handle_files(client, message: Message):
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    status = await message.reply_text("⏳ Preparando...")
    start_time = time.time()
    
    # 1. Descarga
    file_path = await message.download(
        file_name=DOWNLOAD_DIR,
        progress=progress,
        progress_args=(status, start_time, "📥 Descargando...")
    )
    
    filename = os.path.basename(file_path)
    
    # 2. Lógica de Extracción o Compresión
    if filename.lower().endswith(".zip"):
        await status.edit_text("📂 **Extrayendo contenido...**")
        extract_path = os.path.join(DOWNLOAD_DIR, filename + "_extracted")
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Enviar cada archivo extraído según su tipo
            for root, _, files in os.walk(extract_path):
                for f in files:
                    f_path = os.path.join(root, f)
                    ext = f.lower().split('.')[-1]
                    
                    if ext in ['jpg', 'jpeg', 'png', 'webp']:
                        await message.reply_photo(f_path, caption=f"`{f}`")
                    elif ext in ['mp4', 'mkv', 'mov']:
                        await message.reply_video(f_path, caption=f"`{f}`")
                    elif ext in ['mp3', 'wav', 'ogg', 'm4a']:
                        await message.reply_audio(f_path, caption=f"`{f}`")
                    else:
                        await message.reply_document(f_path, caption=f"`{f}`")
            
            shutil.rmtree(extract_path)
        except Exception as e:
            await message.reply_text(f"❌ Error al extraer: {e}")
    else:
        await status.edit_text("📦 **Comprimiendo a ZIP...**")
        zip_name = file_path + ".zip"
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zip_f:
            zip_f.write(file_path, filename)
        
        await message.reply_document(zip_name, caption="✅ Aquí tienes tu archivo comprimido.")
        if os.path.exists(zip_name): os.remove(zip_name)

    # 3. Limpieza final
    if os.path.exists(file_path): os.remove(file_path)
    await status.delete()

print("Bot iniciado con Pyrogram...")
app.run()

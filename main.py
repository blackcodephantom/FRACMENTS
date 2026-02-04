import os
import zipfile
import shutil
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuración básica
TOKEN = os.getenv("TELEGRAM_TOKEN")
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Envíame un archivo y dime si quieres (C) Comprimirlo o (E) Extraerlo.")

async def handle_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    file_path = os.path.join(DOWNLOAD_DIR, update.message.document.file_name)
    
    status_msg = await update.message.reply_text("📥 Descargando archivo...")
    await file.download_to_drive(file_path)
    
    # Lógica de detección de extensión
    ext = file_path.split('.')[-1].lower()
    
    if ext == 'zip':
        await status_msg.edit_text("📂 Extrayendo contenido...")
        extract_path = file_path.replace('.zip', '_extracted')
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # Enviar archivos extraídos
        for root, dirs, files in os.walk(extract_path):
            for f in files:
                full_path = os.path.join(root, f)
                await send_smart_file(update, context, full_path)
    else:
        await status_msg.edit_text("📦 Comprimiendo archivo...")
        zip_name = f"{file_path}.zip"
        with zipfile.ZipFile(zip_name, 'w') as zip_f:
            zip_f.write(file_path, os.path.basename(file_path))
        await update.message.reply_document(document=open(zip_name, 'rb'))

    await status_msg.edit_text("✅ Tarea finalizada.")

async def send_smart_file(update, context, path):
    """Envía el archivo según su tipo"""
    ext = path.split('.')[-1].lower()
    if ext in ['jpg', 'jpeg', 'png']:
        await update.message.reply_photo(photo=open(path, 'rb'))
    elif ext in ['mp3', 'wav', 'ogg']:
        await update.message.reply_audio(audio=open(path, 'rb'))
    elif ext in ['mp4', 'mkv']:
        await update.message.reply_video(video=open(path, 'rb'))
    else:
        await update.message.reply_document(document=open(path, 'rb'))

if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_docs))
    application.run_polling()

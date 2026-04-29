#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import threading
import time
import asyncio
import requests
from flask import Flask, jsonify
from aiogram import Bot
from googleapiclient.discovery import build
import aiohttp

# ========== НАСТРОЙКИ ==========
API_KEY = 'AIzaSyBn1Vwz7lOr5RemitsJGCn8OI3eLgK8BbI'
BOT_TOKEN = '8794154964:AAGFbxdt6zT7EHJTWViC6mYlvRhPDCVDBVc'
CHANNEL_ID = 'UCofBxyxHTeSF7b05NIlF_lg'
MY_CHAT_ID = 8581106608
CHECK_INTERVAL = 20  # Проверка новых видео каждые 20 секунд

# ========== FLASK (АНТИ-ЗАСЫПАНИЕ SAD X UNIQUE) ==========
app = Flask(__name__)

@app.route('/healthcheck')
def healthcheck():
    return jsonify({"status": "alive"}), 200

@app.route('/')
def home():
    return 'Бот Вели активен!'

def self_ping():
    # Сразу начинаем пинговать без задержек
    render_url = os.environ.get('RENDER_EXTERNAL_URL')
    if not render_url:
        print("⚠️ RENDER_EXTERNAL_URL не найден, самопинг локальный.")
        render_url = "http://localhost:5000"
        
    while True:
        try:
            requests.get(render_url, timeout=10)
            print("✅ Самопинг 5 сек")
        except Exception as e:
            print(f"❌ Ошибка пинга: {e}")
        time.sleep(5)  # Оригинальный интервал Sad x Unique

# ========== ЛОГИКА БОТА ==========
bot = Bot(token=BOT_TOKEN)
youtube = build('youtube', 'v3', developerKey=API_KEY)
last_video_id = None

async def is_shorts(video_id):
    url = f"https://youtube.com{video_id}"
    async with aiohttp.ClientSession() as session:
        async with session.head(url, allow_redirects=False) as response:
            return response.status == 200

async def check_new_video():
    global last_video_id
    try:
        res = youtube.channels().list(id=CHANNEL_ID, part='contentDetails').execute()
        playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        playlist_res = youtube.playlistItems().list(
            playlistId=playlist_id, part='snippet', maxResults=1
        ).execute()

        if not playlist_res['items']:
            return

        item = playlist_res['items'][0]['snippet']
        video_id = item['resourceId']['videoId']
        video_title = item['title']
        video_url = f"https://youtube.com{video_id}"

        if last_video_id is None:
            last_video_id = video_id
            print(f"Первый запуск: запомнил видео {video_title}")
            return

        if video_id != last_video_id:
            last_video_id = video_id
            if await is_shorts(video_id):
                text = f"ВЫШЛО НОВОЕ ВИДИО У ВЕЛИ 😮😮😮\n\n{video_title}\n{video_url}"
            else:
                text = f"ВЫШЛО НОВОЕ ВИДИО У ВЕЛИ\n\n{video_title}\n{video_url}"
            await bot.send_message(MY_CHAT_ID, text)
            print(f"Отправлено уведомление: {video_title}")

    except Exception as e:
        print(f"Ошибка YouTube: {e}")

async def run_bot():
    while True:
        await check_new_video()
        await asyncio.sleep(CHECK_INTERVAL)

# ========== ЗАПУСК ==========
def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Запускаем самопинг в потоке
    threading.Thread(target=self_ping, daemon=True).start()
    
    # Запускаем Flask в потоке
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Запускаем основной цикл бота
    print("🚀 Система запущена!")
    asyncio.run(run_bot())

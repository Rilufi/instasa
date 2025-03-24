# coding=utf-8
import os
import urllib.request
import requests
import google.generativeai as genai
from instagrapi import Client
import telebot
from yt_dlp import YoutubeDL
import random
import time
from sys import exit
from bs4 import BeautifulSoup
import subprocess

# Configurações de autenticação
api_key = os.environ.get("API_KEY")
username = os.environ.get("USERNAME")
password = os.environ.get("PASSWORD")
tele_user = os.environ.get("TELE_USER")
TOKEN = os.environ["TELEGRAM_TOKEN"]
bot = telebot.TeleBot(TOKEN)
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)

# Modelo GenAI
model = genai.GenerativeModel('gemini-2.0-flash-lite')

def get_video_duration(video_path):
    """Obtém a duração do vídeo usando FFprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Erro ao obter duração do vídeo: {e}")
        return 0

def process_video(input_path, output_path="instagram_ready.mp4", max_duration=60):
    """Processa vídeo para o Instagram usando FFmpeg"""
    try:
        duration = get_video_duration(input_path)
        
        if duration <= max_duration:
            # Copia o vídeo sem re-encode se já estiver dentro do limite
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c', 'copy',
                output_path
            ]
        else:
            # Corta e converte para formato otimizado
            cmd = [
                'ffmpeg', '-i', input_path,
                '-t', str(max_duration),
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '22',
                '-c:a', 'aac', '-b:a', '128k',
                '-vf', 'scale=1080:-2',  # Mantém aspect ratio com largura 1080
                '-movflags', '+faststart',
                output_path
            ]
        
        subprocess.run(cmd, check=True)
        return output_path
    except Exception as e:
        print(f"Erro ao processar vídeo: {e}")
        return None

def post_instagram_video(cl, video_path, caption):
    """Posta vídeo no Instagram com tratamento robusto"""
    try:
        time.sleep(random.uniform(30, 60))
        processed_path = process_video(video_path)
        
        if processed_path:
            cl.video_upload(
                processed_path,
                caption=caption,
                extra_data={
                    "configure_mode": 2,  # 2=FEED
                    "source_type": 4,
                    "video_format": "mp4",
                    "length": min(get_video_duration(processed_path), 60)
                }
            )
            print("Vídeo publicado no Instagram")
        else:
            raise ValueError("Falha no processamento do vídeo")
    except Exception as e:
        print(f"Erro ao postar vídeo no Instagram: {e}")
        bot.send_message(tele_user, f"Erro ao postar vídeo: {e}")

def download_direct_video(video_url, filename='apod_direct.mp4'):
    """Baixa vídeo diretamente da NASA"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        if video_url.startswith('/'):
            video_url = f'https://apod.nasa.gov{video_url}'
        
        print(f"Baixando vídeo: {video_url}")
        with requests.get(video_url, stream=True, headers=headers) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return filename
    except Exception as e:
        print(f"Erro ao baixar vídeo: {e}")
        return None

def logar_instagram(username, password, session_file):
    cl = Client()
    try:
        if os.path.exists(session_file):
            cl.load_settings(session_file)
        else:
            cl.login(username, password)
            cl.dump_settings(session_file)
            print(f"Sessão salva em {session_file}")
        cl.get_timeline_feed()
        return cl
    except Exception as e:
        print(f"Erro ao logar no Instagram: {e}")
        bot.send_message(tele_user, f"apodinsta erro ao logar no Instagram: {e}")
        exit()

def load_session_from_secret(secret_name, session_file):
    session_content = os.environ.get(secret_name)
    if session_content:
        with open(session_file, "w") as f:
            f.write(session_content)
        print(f"Sessão carregada a partir do segredo {secret_name}")
    else:
        raise ValueError(f"Segredo {secret_name} não encontrado.")

session_file = f"instagram_session_{username}.json"
load_session_from_secret("INSTAGRAM_SESSION", session_file)

try:
    instagram_client = logar_instagram(username, password, session_file)
except Exception as e:
    print(f"Erro ao logar no Instagram: {e}")
    bot.send_message(tele_user, f"Erro ao logar no Instagram: {e}")

def post_instagram_photo(cl, image_path, caption):
    try:
        time.sleep(random.uniform(30, 60))
        cl.photo_upload(image_path, caption)
        print("Foto publicada no Instagram")
    except Exception as e:
        print(f"Erro ao postar foto no Instagram: {e}")
        bot.send_message(tele_user, f"apodinsta com problema pra postar: {e}")

def gerar_traducao(prompt):
    try:
        response = model.generate_content(prompt)
        if response.candidates and response.candidates[0].content.parts:
            return response.candidates[0].content.parts[0].text
    except Exception as e:
        print(f"Erro ao gerar tradução com o Gemini: {e}")
    return None

def download_video(link, cookies_content):
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'apod_video.%(ext)s',
            'cookiefile': '-',
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.cookiefile = cookies_content
            info_dict = ydl.extract_info(link, download=True)
            return ydl.prepare_filename(info_dict)
    except Exception as e:
        print(f"Erro ao baixar o vídeo: {e}")
        return None

def extract_video_url_from_html(apod_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(apod_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Procura por tags de vídeo
        video_tag = soup.find('video')
        if video_tag:
            source = video_tag.find('source')
            if source and source.get('src'):
                video_url = source.get('src')
                # Converte para URL absoluta se necessário
                if not video_url.startswith('http'):
                    base_url = 'https://apod.nasa.gov/apod/'
                    video_url = base_url + video_url
                return video_url
        
        # Procura por iframes do YouTube como fallback
        iframe = soup.find('iframe')
        if iframe and 'youtube' in iframe.get('src', ''):
            return iframe.get('src')
            
        return None
    except Exception as e:
        print(f"Erro ao extrair URL do vídeo: {e}")
        return None

def detect_media_type(data):
    media_type = data.get('media_type', '').lower()
    url = data.get('url', '')
    
    # Se for 'other' mas temos uma URL HTML, assumimos que é vídeo
    if media_type == 'other' and url and ('apod.nasa.gov/apod' in url and '.html' in url):
        return 'html_video'
    
    # Restante da detecção normal...
    if (media_type == 'video' or 
        (url and any(ext in url.lower() for ext in ['.mp4', '.mov', '.avi', '.webm'])) or
        'thumbnail_url' in data):
        return 'video'
    
    if (media_type == 'image' or 
        (url and any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']))):
        return 'image'
    
    return 'unsupported'

def debug_api_data(data):
    print("\nDEBUG - Dados da API:")
    print(f"URL: {data.get('url')}")
    print(f"Media Type: {data.get('media_type')}")
    print(f"Thumbnail: {data.get('thumbnail_url')}")
    print(f"Title: {data.get('title')}")

def get_apod_data(api_key):
    base_url = "https://api.nasa.gov/planetary/apod"
    params = {'api_key': api_key, 'hd': 'True', 'thumbs': 'True'}
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Se não houver URL mas o media_type for 'other', construímos a URL manualmente
        if not data.get('url') and data.get('media_type') == 'other':
            apod_date = data.get('date', '')
            if apod_date:
                data['url'] = f"https://apod.nasa.gov/apod/ap{apod_date.replace('-', '')[2:]}.html"
            else:
                data['url'] = "https://apod.nasa.gov/apod/astropix.html"
        
        return data
    except Exception as e:
        print(f"Erro ao acessar a API da NASA: {e}")
        raise

try:
    data = get_apod_data(api_key)
    debug_api_data(data)
    
    site = data.get('url')
    media_type = detect_media_type(data)
    explanation = data.get('explanation')
    title = data.get('title')

    # Geração da legenda (mantida igual)
    insta_string = generate_caption(title, explanation)

    # Processamento de mídia
    if media_type == 'image':
        urllib.request.urlretrieve(site, 'apodtoday.jpg')
        if instagram_client:
            post_instagram_photo(instagram_client, 'apodtoday.jpg', insta_string)
    
    elif media_type in ['video', 'html_video']:
        video_url = site if media_type == 'video' else extract_video_url_from_html(site)
        
        if video_url:
            if 'youtube' in video_url:
                cookies = os.environ.get("COOKIES_CONTENT")
                video_path = download_video(video_url, cookies) if cookies else None
            else:
                video_path = download_direct_video(video_url)
            
            if video_path and instagram_client:
                post_instagram_video(instagram_client, video_path, insta_string)
    
    else:
        print(f"Tipo de mídia não suportado: {media_type}")

except Exception as e:
    print(f"Erro no processamento principal: {e}")
    bot.send_message(tele_user, f"Erro: {e}")

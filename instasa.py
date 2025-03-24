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
import json

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

def run_ffmpeg_command(cmd):
    """Executa comando FFmpeg com tratamento de erros"""
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro FFmpeg: {e.stderr.decode('utf-8')}")
        return False

def get_video_metadata(video_path):
    """Obtém metadados do vídeo usando FFprobe"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_format',
        '-show_streams',
        '-of', 'json',
        video_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        print(f"Erro ao obter metadados: {e}")
        return None

def process_video_for_instagram(input_path, output_path="instagram_ready.mp4"):
    """Prepara vídeo para o Instagram usando FFmpeg"""
    metadata = get_video_metadata(input_path)
    if not metadata:
        return None

    duration = float(metadata['format']['duration'])
    video_stream = next((s for s in metadata['streams'] if s['codec_type'] == 'video'), None)
    
    if not video_stream:
        return None

    cmd = [
        'ffmpeg',
        '-i', input_path,
        '-t', '60' if duration > 60 else str(duration),
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '22',
        '-vf', 'scale=1080:-2',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart',
        '-y',
        output_path
    ]
    
    if run_ffmpeg_command(cmd):
        return output_path
    return None

def upload_video_to_instagram(cl, video_path, caption):
    """Upload direto para o Instagram"""
    try:
        processed_path = process_video_for_instagram(video_path)
        if not processed_path:
            raise ValueError("Falha no processamento do vídeo")
        
        # Configuração alternativa de upload
        media = cl.clip_upload(
            path=processed_path,
            caption=caption,
            thumbnail=None,
            extra_data={
                'configure_mode': 2,  # Feed
                'source_type': 3      # Upload direto
            }
        )
        print(f"Vídeo postado com sucesso! ID: {media.id}")
        return True
    except Exception as e:
        print(f"Erro no upload para Instagram: {e}")
        return False

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
                    if chunk:
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
        
        video_tag = soup.find('video')
        if video_tag:
            source = video_tag.find('source')
            if source and source.get('src'):
                video_url = source.get('src')
                if not video_url.startswith('http'):
                    base_url = 'https://apod.nasa.gov/apod/'
                    video_url = base_url + video_url
                return video_url
        
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
    
    if media_type == 'other' and url and ('apod.nasa.gov/apod' in url and '.html' in url):
        return 'html_video'
    
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

# Processamento principal
try:
    data = get_apod_data(api_key)
    debug_api_data(data)
    
    site = data.get('url')
    media_type = detect_media_type(data)
    explanation = data.get('explanation')
    title = data.get('title')

    # Geração da legenda
    try:
        prompt = f"""Traduza para português brasileiro e adicione hashtags:
        {title}
        {explanation}"""
        traducao = gerar_traducao(prompt) or f"{title}\n\n{explanation}"
        insta_string = f"Foto Astronômica do Dia\n\n{traducao}"
    except Exception as e:
        print(f"Erro ao gerar tradução: {e}")
        insta_string = f"Foto Astronômica do Dia\n\n{title}\n\n{explanation}"
    print(f"\nLegenda gerada:\n{insta_string}")

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
                upload_video_to_instagram(instagram_client, video_path, insta_string)
    
    else:
        msg = f"Tipo de mídia não suportado: {media_type}\nURL: {site}"
        print(msg)
        bot.send_message(tele_user, msg)

except Exception as e:
    print(f"Erro no processamento principal: {e}")
    bot.send_message(tele_user, f"Erro: {e}")

# coding=utf-8
import os
import urllib.request
import requests
import google.generativeai as genai
from instagrapi import Client
import telebot
from yt_dlp import YoutubeDL  # Substituído pytube por yt-dlp
from moviepy.video.io.VideoFileClip import VideoFileClip
import time
from sys import exit

# Authentication
api_key = os.environ.get("API_KEY")
username = os.environ.get("USERNAME")
password = os.environ.get("PASSWORD")
tele_user = os.environ.get("TELE_USER")
TOKEN = os.environ["TELEGRAM_TOKEN"]
bot = telebot.TeleBot(TOKEN)
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)

# Choose a GenAI model (e.g., 'gemini-pro')
model = genai.GenerativeModel('gemini-2.0-flash-lite')

# Função para logar no Instagram com verificação de desafio
def logar_instagram(username, password, session_file):
    cl = Client()
    try:
        if os.path.exists(session_file):
            # Carrega a sessão salva
            cl.load_settings(session_file)
        else:
            # Faz login e salva a sessão
            cl.login(username, password)
            cl.dump_settings(session_file)
            print(f"Sessão salva em {session_file}")
        cl.get_timeline_feed()  # Verifica se o login foi bem-sucedido
        return cl  # Retorna o cliente
    except Exception as e:
        print(f"Erro ao logar no Instagram: {e}")
        bot.send_message(tele_user, f"apodinsta erro ao logar no Instagram: {e}")
        exit()

# Carrega a sessão a partir do segredo no GitHub Actions
def load_session_from_secret(secret_name, session_file):
    session_content = os.environ.get(secret_name)
    if session_content:
        with open(session_file, "w") as f:
            f.write(session_content)
        print(f"Sessão carregada a partir do segredo {secret_name}")
    else:
        raise ValueError(f"Segredo {secret_name} não encontrado.")

# Nome do arquivo de sessão
session_file = f"instagram_session_{username}.json"
load_session_from_secret("INSTAGRAM_SESSION", session_file)

# Tenta fazer login no Instagram
try:
    instagram_client = logar_instagram(username, password, session_file)
except Exception as e:
    print(f"Erro ao logar no Instagram: {e}")
    bot.send_message(tele_user, f"Erro ao logar no Instagram: {e}")

# Função para postar foto no Instagram
def post_instagram_photo(cl, image_path, caption):
    try:
        time.sleep(random.uniform(30, 60))  # Espera aleatória antes de postar
        cl.photo_upload(image_path, caption)
        print("Foto publicada no Instagram")
    except Exception as e:
        print(f"Erro ao postar foto no Instagram: {e}")
        bot.send_message(tele_user, f"apodinsta com problema pra postar: {e}")

# Função para postar vídeo no Instagram
# Função para postar vídeo no Instagram com tratamento melhorado
def post_instagram_video(cl, video_path, caption):
    try:
        time.sleep(random.uniform(30, 60))
        
        # Verifica se o vídeo atende aos requisitos do Instagram
        with VideoFileClip(video_path) as video:
            duration = video.duration
            if duration > 60:  # Instagram permite até 60 segundos no feed
                output_path = "video_instagram.mp4"
                video_cortado = video.subclip(0, 60)
                video_cortado.write_videofile(
                    output_path,
                    codec="libx264",
                    audio_codec="aac",
                    fps=30,
                    threads=4
                )
                video_path = output_path
        
        # Configurações recomendadas para upload no Instagram
        cl.video_upload(
            video_path,
            caption=caption,
            thumbnail=None,  # Pode adicionar um frame específico como thumbnail
            extra_data={
                "configure_mode": 1,  # 1=REEL, 2=FEED
                "source_type": 4,     # 4=Library
                "video_format": "mp4",
                "length": duration if duration <= 60 else 60
            }
        )
        print("Vídeo publicado no Instagram")
    except Exception as e:
        print(f"Erro ao postar vídeo no Instagram: {e}")
        bot.send_message(tele_user, f"apodinsta com problema pra postar vídeo: {e}")
        raise  # Re-lança a exceção para debug

# Função para gerar conteúdo traduzido usando o modelo GenAI
def gerar_traducao(prompt):
    try:
        response = model.generate_content(prompt)
        if response.candidates and len(response.candidates) > 0:
            if response.candidates[0].content.parts and len(response.candidates[0].content.parts) > 0:
                return response.candidates[0].content.parts[0].text
            else:
                print("Nenhuma parte de conteúdo encontrada na resposta.")
        else:
            print("Nenhum candidato válido encontrado.")
    except Exception as e:
        print(f"Erro ao gerar tradução com o Gemini: {e}")
    return None

# Função para baixar o vídeo usando yt-dlp com cookies
def download_video(link, cookies_content):
    try:
        ydl_opts = {
            'format': 'best',  # Baixa o vídeo na melhor qualidade disponível
            'outtmpl': '%(title)s.%(ext)s',  # Define o nome do arquivo de saída
            'cookiefile': '-',  # Usa os cookies diretamente da string
        }
        with YoutubeDL(ydl_opts) as ydl:
            # Passa os cookies diretamente como uma string
            ydl.cookiefile = cookies_content
            info_dict = ydl.extract_info(link, download=True)
            video_filename = ydl.prepare_filename(info_dict)
            return video_filename
    except Exception as e:
        print(f"Erro ao baixar o vídeo: {e}")
        return None

# Função para cortar o vídeo
def cortar_video(video_path, start_time, end_time, output_path):
    try:
        with VideoFileClip(video_path) as video:
            duration = video.duration
            if start_time < 0 or end_time > duration:
                raise ValueError("Os tempos de corte estão fora da duração do vídeo")
            video_cortado = video.subclip(start_time, end_time)
            video_cortado.write_videofile(output_path, codec="libx264")
        return output_path
    except Exception as e:
        print(f"Erro ao cortar o vídeo: {e}")
        return None

# Get the picture, explanation, and/or video thumbnail
URL_APOD = "https://api.nasa.gov/planetary/apod"
params = {
    'api_key': api_key,
    'hd': 'True',
    'thumbs': 'True'
}

try:
    response = requests.get(URL_APOD, params=params)
    response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
    data = response.json()
    site = data.get('url')
    thumbs = data.get('thumbnail_url')
    media_type = data.get('media_type')
    explanation = data.get('explanation')
    title = data.get('title')
except requests.exceptions.RequestException as e:
    print(f"Erro ao acessar a API da NASA: {e}")
    bot.send_message(tele_user, f"Erro ao acessar a API da NASA: {e}")
    exit()
except ValueError as e:
    print(f"Erro ao decodificar a resposta da API da NASA: {e}")
    bot.send_message(tele_user, f"Erro ao decodificar a resposta da API da NASA: {e}")
    exit()

# Combinar o título e a explicação em um único prompt
prompt_combinado = f"""Given the following scientific text from a reputable source (NASA) in English, translate it accurately and fluently into grammatically correct Brazilian Portuguese while preserving the scientific meaning. Also, based on the following text, create engaging astronomy related hashtags. **Output the translated text and hashtags in a single string, separated by newlines, without headers or subtitles in the following format:**
[Translated Title]
[Translated Explanation]
#Hashtag1 #Hashtag2 #Hashtag3 ...

**Input:**
{title}
{explanation}
"""

# Gerar tradução combinada usando o modelo
try:
    traducao_combinada = gerar_traducao(prompt_combinado)
    if traducao_combinada:
        insta_string = f"""Foto Astronômica do Dia
{title}

{traducao_combinada}"""
    else:
        raise AttributeError("A tradução combinada não foi gerada.")
except AttributeError as e:
    print(f"Erro ao gerar a tradução: {e}")
    insta_string = f"""Foto Astronômica do Dia
{title}

{explanation}

#NASA #APOD #Astronomia #Espaço #Astrofotografia"""

print(insta_string)

if media_type == 'image':
    # Retrieve the image
    urllib.request.urlretrieve(site, 'apodtoday.jpeg')
    image = "apodtoday.jpeg"

    # Post the image on Instagram
    if instagram_client:
        try:
            post_instagram_photo(instagram_client, image, insta_string)
        except Exception as e:
            print(f"Erro ao postar foto no Instagram: {e}")
            bot.send_message(tele_user, 'apodinsta com problema pra postar imagem')

elif media_type in ['video', 'youtube', 'vimeo', 'gif']:  # Adiciona mais tipos de vídeo
    try:
        cookies_content = os.environ.get("COOKIES_CONTENT")
        if not cookies_content:
            print("Cookies não encontrados nos segredos.")
            bot.send_message(tele_user, 'Cookies não encontrados nos segredos.')
            exit()

        # Baixa o vídeo
        video_file = download_video(site, cookies_content)
        
        if video_file:
            # Prepara o vídeo para o Instagram
            output_path = "instagram_ready.mp4"
            
            with VideoFileClip(video_file) as video:
                # Reduz a duração para até 60 segundos
                duration = min(video.duration, 60)
                
                # Redimensiona se necessário (Instagram prefere 1080x1350, 1080x1080, ou 1080x1920)
                video_cropped = video.subclip(0, duration)
                
                # Escreve o vídeo no formato adequado
                video_cropped.write_videofile(
                    output_path,
                    codec="libx264",
                    audio_codec="aac",
                    bitrate="8000k",
                    fps=30,
                    preset="fast",
                    threads=4
                )
            
            # Posta no Instagram
            if instagram_client:
                post_instagram_video(instagram_client, output_path, insta_string)
                
    except Exception as e:
        print(f"Erro ao processar vídeo: {e}")
        bot.send_message(tele_user, f'Erro ao processar vídeo APOD: {e}')
else:
    print(f"Tipo de mídia não suportado: {media_type}")
    bot.send_message(tele_user, f'Tipo de mídia não suportado: {media_type}')

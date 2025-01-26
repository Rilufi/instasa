# coding=utf-8
import os
import time
from instagrapi import Client
import random

# Autenticação
username = os.environ.get("USERNAME")
password = os.environ.get("PASSWORD")

# Lista de hashtags relevantes para astronomia em português (sem o caractere #)
HASHTAGS_ASTRONOMIA = [
    "astronomia", "espaco", "universo", "ciencia", "telescopio",
    "estrelas", "planetario", "galaxia", "cosmos", "astrofotografia",
    "nasa", "esa", "cienciaespacial", "observatorio", "via-lactea"
]

# Função para logar no Instagram com verificação de desafio
def logar_instagram():
    cl = Client()
    session_file = 'instagram_session.json'
    try:
        if os.path.exists(session_file):
            cl.load_settings(session_file)
        cl.login(username, password)
        cl.get_timeline_feed()
        cl.dump_settings(session_file)
    except Exception as e:
        print(f"Erro ao logar no Instagram: {e}")
        exit()
    return cl

# Função para seguir contas e curtir postagens relacionadas às hashtags
def seguir_e_curtir_hashtags(cl, hashtags, max_acoes=10):
    try:
        for hashtag in hashtags:
            print(f"Procurando posts com a hashtag: #{hashtag}")
            posts = cl.hashtag_medias_recent(hashtag, amount=5)  # Busca posts recentes com a hashtag

            for post in posts:
                user_id = post.user.pk

                # Verifica o status de amizade (seguir ou não seguir)
                friendship_status = cl.user_friendship_v1(user_id)
                if not friendship_status.following:  # Verifica se já está seguindo
                    cl.user_follow(user_id)
                    print(f"Seguindo usuário {post.user.username} (ID: {user_id})")
                    time.sleep(random.uniform(10, 30))  # Espera aleatória para evitar bloqueio
                    max_acoes -= 1

                # Verifica se a postagem já foi curtida
                media_info = cl.media_info(post.id)
                if not media_info.has_liked:
                    cl.media_like(post.id)
                    print(f"Curtindo postagem {post.id} do usuário {post.user.username}")
                    time.sleep(random.uniform(10, 30))  # Espera aleatória para evitar bloqueio
                    max_acoes -= 1

                if max_acoes <= 0:
                    return  # Limita o número de ações por execução

    except Exception as e:
        print(f"Erro ao seguir contas ou curtir postagens: {e}")

# Execução principal
if __name__ == "__main__":
    try:
        instagram_client = logar_instagram()
        seguir_e_curtir_hashtags(instagram_client, HASHTAGS_ASTRONOMIA)
    except Exception as e:
        print(f"Erro durante a execução: {e}")

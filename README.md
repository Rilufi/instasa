# 📸 Instasa - Bot da NASA no Instagram 🇧🇷

Bot em Python para postar automaticamente a "Astronomy Picture of the Day" (APOD) da NASA no Instagram.

## 📦 Instalação
```
pip install -r requirements.txt
```

## 🔑 Configuração Necessária
1. **NASA API**:
   - Obtenha uma chave em: [api.nasa.gov](https://api.nasa.gov/)
   - Adicione no arquivo `auth.py` como `nasa_key`

2. **Google Generative AI**:
   - Requer chave de API para traduções
   - Configure como variável de ambiente `GOOGLE_API_KEY`

3. **Instagram**:
   - Use o pacote `instagrapi`
   - Configure credenciais no arquivo `auth.py`

## 🌟 Funcionalidades
- Posta automaticamente a APOD diária
- Processa tanto imagens quanto vídeos
- Traduz legendas (inglês → português) usando IA
- Sistemas alternativos para quando o upload falha
- Suporte a vídeos do YouTube incorporados

## ⚠️ Desafios Conhecidos
- Limitações da API não oficial do Instagram
- Requer autenticação manual periódica
- Restrições de upload de vídeo (60s máximo)

## 🏃‍♂️ Como Usar
1. Configure todas as chaves API
2. Execute o script principal:
```
python instasa.py
```

## 📫 Contato
- Criado por Yuri Abuchaim
- [Instagram @apodinsta](https://instagram.com/apodinsta)
- yuri.abuchaim@gmail.com

===========================================

# 📸 Instasa - Instagram NASA Bot 🇺🇸

Python bot to automatically post NASA's Astronomy Picture of the Day (APOD) on Instagram.

## 📦 Installation
```
pip install -r requirements.txt
```

## 🔑 Required Setup
1. **NASA API**:
   - Get a key at: [api.nasa.gov](https://api.nasa.gov/)
   - Add to `auth.py` as `nasa_key`

2. **Google Generative AI**:
   - Requires API key for translations
   - Set as environment variable `GOOGLE_API_KEY`

3. **Instagram**:
   - Use the `instagrapi` package
   - Configure credentials in `auth.py`

## 🌟 Features
- Automatically posts daily APOD
- Processes both images and videos
- Translates captions (EN → PT) using AI
- Fallback systems for failed uploads
- Supports embedded YouTube videos

## ⚠️ Known Challenges
- Limitations of unofficial Instagram API
- Requires periodic manual authentication
- Video upload restrictions (60s max)

## 🏃‍♂️ How to Use
1. Configure all API keys
2. Run main script:
```
python instasa.py
```

## 📫 Contact
- Created by Yuri Abuchaim
- [Instagram @apodinsta](https://instagram.com/apodinsta)
- yuri.abuchaim@gmail.com

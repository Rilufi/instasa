# instasa

Bot em Python para postar a Astronomy Picture of the Day no Instagram usando a API da NASA.

## Instalações
Todos os pacotes necessários estão listados em `requirements.txt`. Você pode instalá-los usando:

```
$ pip install -r requirements.txt
```


## NASA API
É necessário solicitar uma chave para a API da NASA visitando o site e preenchendo seu nome e e-mail em "Generate API Keys" em [NASA API](https://api.nasa.gov/). Não se esqueça de incluir essa chave em `auth.py` sob `nasa_key`.

## Google Generative AI
Para usar a Google Generative AI para traduções, você precisa de uma chave de API. Configure a chave da API nas variáveis de ambiente como `GOOGLE_API_KEY`.

## Instagram API
Para postar no Instagram, use o pacote `instagrapi`. Certifique-se de fornecer suas credenciais do Instagram nas variáveis de ambiente.

## O que o bot faz?
- **Posta a Astronomy Picture of the Day**: Recupera a APOD da API da NASA e posta no Instagram.
- **Reposta a foto do dia anterior da NASA no Instagram**: Baixa a foto mais recente do Instagram de contas oficiais da NASA e posta no Instagram com a legenda traduzida.
- **Manipula diferentes tipos de mídia**: Suporta a postagem de imagens e vídeos, incluindo o processamento de vídeos para limites de duração.
- 
## Uso
O bot pode ser executado com o script principal "nasapod.py" que lida com todo o processo de buscar dados, processá-los e postá-los nas plataformas de mídia social.

## Verificar os resultados
Para ver o bot em ação, confira [Apodinsta no Instagram](https://www.instagram.com/apodinsta/).

---

# nasapod

Python bot to post the Astronomy Picture of the Day on Instagram using the NASA API.

## Installations
All required packages are listed in `requirements.txt`. You can install them using:

```
$ pip install -r requirements.txt
```

## NASA API
You need to request a key for the NASA API by visiting the website and filling in your name and email under "Generate API Keys" at [NASA API](https://api.nasa.gov/). Don't forget to include this key in `auth.py` under `nasa_key`.

## Google Generative AI
To use the Google Generative AI for translations, you need an API key. Configure the API key in your environment variables as `GOOGLE_API_KEY`.

## Instagram API
To post on Instagram, use the `instagrapi` package. Make sure to provide your Instagram credentials in the environment variables.

## What does the bot do?
- **Posts the Astronomy Picture of the Day**: Retrieves the APOD from the NASA API and posts it on Instagram.
- **Reposts NASA's Instagram photo of the previous day **: Downloads the latest photo from NASA's official Instagram accounts and posts it on Instagram with a translated caption.
- **Handles different media types**: Supports posting images and videos, including video processing for Twitter's duration limits.

## Usage
The bot can be run with the main script "instasa.py" which handles the entire process of fetching data, processing it, and posting it to social media platforms.

## Check the results
To see the bot in action, check out [Apodinsta on Instagram](https://www.instagram.com/apodinsta/).

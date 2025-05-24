import os
import requests
import time
import random
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm
from dotenv import load_dotenv


GENIUS_API_TOKEN = "Rv2N9Fq-bJ3oHYqtoOndYbdRhk6i7l2x5Zq4-2XGMYseegJUYFeUr8e5vbGjUw_j"

# Настройка базы данных
Base = declarative_base()


class Song(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True)
    artist = Column(String)
    title = Column(String)
    lyrics = Column(Text)
    genius_url = Column(String)


engine = create_engine("sqlite:///genius_songs.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Топ исполнителей
TOP_ARTISTS = [
    "The Weeknd"
]


def search_songs(artist: str):
    """Поиск песен через Genius API"""
    url = "https://api.genius.com/search"
    headers = {"Authorization": f"Bearer {GENIUS_API_TOKEN}"}
    params = {"q": artist, "per_page": 5}  # Уменьшаем количество для теста

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()["response"]["hits"]
    except Exception as e:
        print(f"Ошибка при поиске песен {artist}: {e}")
        return []


def get_lyrics(url: str):
    """Парсинг текста песни с веб-страницы Genius"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Новый способ поиска текста (актуальный на 2024 год)
        lyrics_container = soup.find("div", {"data-lyrics-container": "true"})
        if lyrics_container:
            # Очистка текста
            for br in lyrics_container.find_all("br"):
                br.replace_with("\n")
            return lyrics_container.get_text("\n").strip()

        # Альтернативный поиск
        lyrics_div = soup.find("div", class_=lambda x: x and "Lyrics__Container" in x)
        if lyrics_div:
            return lyrics_div.get_text("\n").strip()

        return "Текст не найден (проверьте структуру страницы)"
    except Exception as e:
        print(f"Ошибка при парсинге {url}: {e}")
        return f"Ошибка загрузки: {str(e)}"


def save_song(artist: str, title: str, lyrics: str, url: str):
    """Сохранение песни в базу данных"""
    song = Song(artist=artist, title=title, lyrics=lyrics, genius_url=url)
    session.add(song)
    session.commit()


def main():
    for artist in tqdm(TOP_ARTISTS, desc="Обработка исполнителей"):
        songs = search_songs(artist)

        for song in tqdm(songs, desc=f"Песни {artist[:10]}...", leave=False):
            song_data = song["result"]
            lyrics = get_lyrics(song_data["url"])

            print(f"\nПолучена песня: {artist} - {song_data['title']}")
            print(f"Текст: {lyrics[:100]}...")  # Показываем начало текста для проверки

            save_song(
                artist=artist,
                title=song_data["title"],
                lyrics=lyrics,
                url=song_data["url"]
            )

            # Случайная задержка 2-5 секунд
            time.sleep(random.uniform(2, 5))


if __name__ == "__main__":
    main()
    print("\nГотово! Данные сохранены в genius_songs.db")
    session.close()
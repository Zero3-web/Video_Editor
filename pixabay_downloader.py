import requests
import os
from urllib.parse import quote
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.config import change_settings
from concurrent.futures import ThreadPoolExecutor
import random  # Importar para seleccionar audios aleatoriamente

try:
    import speech_recognition as sr
except ModuleNotFoundError:
    print("Advertencia: El módulo 'speech_recognition' no está instalado. Los subtítulos basados en audio no estarán disponibles.")
    sr = None

# Configurar la ruta absoluta de ImageMagick
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

API_KEY = "16783972-336159d8867f2630d075423b4"  # Clave de API proporcionada
DOWNLOAD_FOLDER = "c:\\Users\\zeroe\\Desktop\\videos\\downloads"  # Carpeta para guardar videos
AUDIO_FOLDER = "c:\\Users\\zeroe\\Desktop\\audios"  # Carpeta con audios disponibles
DOWNLOADED_IDS_FILE = os.path.join(DOWNLOAD_FOLDER, "downloaded_ids.txt")  # Archivo para guardar IDs descargados

def load_downloaded_ids():
    """Carga los IDs de videos ya descargados desde un archivo."""
    if os.path.exists(DOWNLOADED_IDS_FILE):
        with open(DOWNLOADED_IDS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f)
    return set()

def save_downloaded_id(video_id):
    """Guarda un ID de video en el archivo de IDs descargados."""
    with open(DOWNLOADED_IDS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{video_id}\n")

def search_videos(query, per_page=5, min_duration=0, max_duration=None):
    """Busca videos en la API de Pixabay con opción de filtrar por duración."""
    try:
        # Validar el valor de per_page
        if per_page < 1 or per_page > 200:
            raise ValueError("El número de resultados debe estar entre 1 y 200.")

        url = "https://pixabay.com/api/videos/"
        params = {
            "key": API_KEY,
            "q": quote(query),  # Codificar el término de búsqueda
            "per_page": per_page,
            "min_duration": min_duration,
            "max_duration": max_duration if max_duration else ""
        }
        response = requests.get(url, params=params)
        response.raise_for_status()  # Lanza una excepción si el código de estado no es 200
        videos = response.json().get("hits", [])

        if not videos:
            print("No se encontraron videos para la consulta proporcionada.")
            return []

        # Filtrar videos por duración mínima y máxima
        filtered_videos = [
            video for video in videos
            if video["duration"] >= min_duration and (max_duration is None or video["duration"] <= max_duration)
        ]

        if not filtered_videos:
            print(f"No se encontraron videos que cumplan con la duración mínima de {min_duration} segundos.")
        return filtered_videos
    except ValueError as e:
        print(f"Error en los parámetros: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud a la API: {e}")
        return []

def download_video(video_url, filename):
    """Descarga un video desde una URL y lo guarda en la carpeta especificada."""
    try:
        response = requests.get(video_url, stream=True, timeout=30)  # Agregar timeout para evitar bloqueos
        if response.status_code == 200:
            os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
            print(f"Video descargado: {filepath}")
            return filepath
        else:
            print(f"Error al descargar el video: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar el video desde {video_url}: {e}")
        return None

def add_audio_to_video(video_path, audio_folder):
    """Añade un audio único al video descargado, recorta el video si es necesario y mueve el audio usado a la subcarpeta 'usados'."""
    try:
        video = VideoFileClip(video_path)
        usados_folder = os.path.join(audio_folder, "usados")
        os.makedirs(usados_folder, exist_ok=True)

        # Obtener lista de audios no usados
        audio_files = [
            f for f in os.listdir(audio_folder)
            if (f.endswith(".mp3") or f.endswith(".wav")) and not os.path.isdir(os.path.join(audio_folder, f))
        ]
        if not audio_files:
            print("No se encontraron audios disponibles en la carpeta especificada.")
            return

        # Seleccionar un audio aleatorio disponible
        audio_path = os.path.join(audio_folder, random.choice(audio_files))
        audio = AudioFileClip(audio_path)

        # Ajustar la duración del video al audio (audio + 5 segundos)
        max_duration = audio.duration + 5
        if video.duration > max_duration:
            print(f"El video es más largo que el audio. Recortando el video a {max_duration} segundos.")
            video = video.subclip(0, max_duration)

        # Combinar video y audio
        video = video.set_audio(audio)
        output_path = video_path.replace(".mp4", "_final.mp4")
        video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        print(f"Video final guardado en: {output_path}")

        # Mover el audio usado a la subcarpeta 'usados'
        used_audio_path = os.path.join(usados_folder, os.path.basename(audio_path))
        os.rename(audio_path, used_audio_path)
        print(f"Audio usado movido a: {used_audio_path}")
    except Exception as e:
        print(f"Error al procesar el video {video_path}: {e}")
    finally:
        # Liberar recursos de video y audio
        if 'video' in locals():
            video.close()
        if 'audio' in locals():
            audio.close()

def download_videos(results, downloaded_ids):
    """Descarga todos los videos antes de procesarlos."""
    downloaded_paths = []
    with ThreadPoolExecutor(max_workers=5) as executor:  # Limitar el número de hilos para evitar bloqueos
        futures = []
        for i, video in enumerate(results):
            video_id = video["id"]
            if video_id in downloaded_ids:
                print(f"Saltando video con ID {video_id} (ya descargado).")
                continue

            video_url = video["videos"]["medium"]["url"]
            filename = f"video_{i + 1}.mp4"
            print(f"Encolando descarga: {filename} desde {video_url}")
            futures.append((video_id, filename, executor.submit(download_video, video_url, filename)))

        # Esperar a que todas las descargas terminen
        for video_id, filename, future in futures:
            video_path = future.result()
            if video_path:
                downloaded_paths.append(video_path)
                save_downloaded_id(video_id)

    return downloaded_paths

def main():
    try:
        query = input("Introduce el término de búsqueda para los videos: ").strip()
        per_page = int(input("¿Cuántos resultados deseas? (entre 1 y 200): "))
        
        # Solicitar duración mínima y máxima
        min_duration = int(input("Duración mínima del video en segundos (0 para sin límite): "))
        max_duration = input("Duración máxima del video en segundos (dejar vacío para sin límite): ")
        max_duration = int(max_duration) if max_duration.strip() else None

        # Cargar IDs de videos ya descargados
        downloaded_ids = load_downloaded_ids()

        results = search_videos(query, per_page, min_duration, max_duration)
        if not results:
            print("No se encontraron videos que cumplan con los criterios especificados.")
            return

        # Descargar todos los videos primero
        print("Iniciando descarga de videos...")
        downloaded_paths = download_videos(results, downloaded_ids)

        if not downloaded_paths:
            print("No se descargaron videos. Verifica los criterios de búsqueda o la conexión a internet.")
            return

        # Procesar los videos descargados
        print("Iniciando procesamiento de videos...")
        for video_path in downloaded_paths:
            add_audio_to_video(video_path, AUDIO_FOLDER)

        print("Proceso completado.")
    except ValueError:
        print("Error: Por favor, introduce un número válido para la cantidad de resultados o duración.")
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.")
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    main()
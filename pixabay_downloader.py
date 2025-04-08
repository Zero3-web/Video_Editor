import requests
import os
from urllib.parse import quote
from moviepy.editor import VideoFileClip, AudioFileClip
from moviepy.config import change_settings
from concurrent.futures import ThreadPoolExecutor

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

def search_videos(query, per_page=5):
    """Busca videos en la API de Pixabay."""
    try:
        # Validar el valor de per_page
        if per_page < 1 or per_page > 200:
            raise ValueError("El número de resultados debe estar entre 1 y 200.")

        url = "https://pixabay.com/api/videos/"
        params = {
            "key": API_KEY,
            "q": quote(query),  # Codificar el término de búsqueda
            "per_page": per_page
        }
        response = requests.get(url, params=params)
        response.raise_for_status()  # Lanza una excepción si el código de estado no es 200
        return response.json().get("hits", [])
    except ValueError as e:
        print(f"Error en los parámetros: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud a la API: {e}")
        return []

def download_video(video_url, filename):
    """Descarga un video desde una URL y lo guarda en la carpeta especificada."""
    response = requests.get(video_url, stream=True)
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

def add_audio_to_video(video_path, audio_folder):
    """Añade un audio al video descargado."""
    try:
        video = VideoFileClip(video_path)
        audio_files = [f for f in os.listdir(audio_folder) if f.endswith(".mp3") or f.endswith(".wav")]
        if not audio_files:
            print("No se encontraron audios en la carpeta especificada.")
            return

        # Seleccionar el primer audio disponible
        audio_path = os.path.join(audio_folder, audio_files[0])
        audio = AudioFileClip(audio_path)

        # Ajustar la duración del audio al video
        if audio.duration > video.duration:
            audio = audio.subclip(0, video.duration)

        # Combinar video y audio
        video = video.set_audio(audio)
        output_path = video_path.replace(".mp4", "_final.mp4")
        video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        print(f"Video final guardado en: {output_path}")
    except Exception as e:
        print(f"Error al procesar el video {video_path}: {e}")
    finally:
        # Liberar recursos de video y audio
        if 'video' in locals():
            video.close()
        if 'audio' in locals():
            audio.close()

def download_and_process_video(video_url, filename, query, index):
    """Descarga y procesa un video (añade audio)."""
    try:
        video_path = download_video(video_url, filename)
        if video_path:
            add_audio_to_video(video_path, AUDIO_FOLDER)
    except Exception as e:
        print(f"Error al procesar el video {filename}: {e}")

def main():
    try:
        query = input("Introduce el término de búsqueda para los videos: ").strip()
        per_page = int(input("¿Cuántos resultados deseas? (entre 1 y 200): "))

        results = search_videos(query, per_page)
        if not results:
            print("No se encontraron videos.")
            return

        # Descargar y procesar videos en paralelo
        with ThreadPoolExecutor() as executor:
            for i, video in enumerate(results):
                video_url = video["videos"]["medium"]["url"]
                filename = f"video_{i + 1}.mp4"
                print(f"Encolando descarga y procesamiento: {filename} desde {video_url}")
                executor.submit(download_and_process_video, video_url, filename, query, i)
    except ValueError:
        print("Error: Por favor, introduce un número válido para la cantidad de resultados.")
    except KeyboardInterrupt:
        print("\nOperación cancelada por el usuario.")
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    main()
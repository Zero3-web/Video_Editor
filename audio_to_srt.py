import os
import speech_recognition as sr
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip
from tkinter import Tk, filedialog
from moviepy.config import change_settings

# Configurar la ruta absoluta de ImageMagick
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

def extract_audio_from_video(video_path, audio_path):
    """Extrae el audio de un video y lo guarda como un archivo .wav."""
    try:
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        video.close()
        print(f"Audio extraído: {audio_path}")
    except Exception as e:
        print(f"Error al extraer el audio del video {video_path}: {e}")

def transcribe_audio_to_srt(audio_path, srt_path):
    """Transcribe un archivo de audio .wav y genera un archivo .srt con tiempos proporcionales."""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            print(f"Transcribiendo el audio: {audio_path}")
            audio = recognizer.record(source)
            transcription = recognizer.recognize_google(audio, language="es-ES")

            # Dividir la transcripción en fragmentos de 10-15 palabras
            words = transcription.split()
            fragments = []
            fragment_size = 12  # Número de palabras por fragmento
            for i in range(0, len(words), fragment_size):
                fragments.append(" ".join(words[i:i + fragment_size]))

            # Calcular tiempos proporcionales
            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration
            fragment_duration = audio_duration / len(fragments)
            audio_clip.close()

            # Generar archivo .srt
            with open(srt_path, "w", encoding="utf-8") as srt_file:
                for i, fragment in enumerate(fragments, start=1):
                    start_time = format_time(i * fragment_duration - fragment_duration)
                    end_time = format_time(i * fragment_duration)
                    srt_file.write(f"{i}\n{start_time} --> {end_time}\n{fragment.strip()}\n\n")
            print(f"Archivo .srt generado: {srt_path}")
    except Exception as e:
        print(f"Error al transcribir el audio {audio_path}: {e}")

def add_subtitles_to_video(video_path, srt_path, output_path):
    """Superpone subtítulos en un video usando un archivo .srt."""
    try:
        video = VideoFileClip(video_path)

        # Leer el archivo .srt y crear clips de texto
        subtitles = []
        with open(srt_path, "r", encoding="utf-8") as srt_file:
            lines = srt_file.readlines()
            for i in range(0, len(lines), 4):  # Cada subtítulo tiene 4 líneas en el archivo .srt
                times = lines[i + 1].strip()
                text = lines[i + 2].strip()

                start_time, end_time = times.split(" --> ")
                start_time = parse_time(start_time)
                end_time = parse_time(end_time)

                # Ajustar el tamaño y posición del subtítulo
                text_clip = TextClip(
                    text, fontsize=24, color='white', bg_color='black', size=(video.w * 0.8, None), method='caption'
                )
                text_clip = text_clip.set_position(('center', video.h - 50)).set_start(start_time).set_end(end_time)
                subtitles.append(text_clip)

        # Combinar los subtítulos con el video
        final_video = CompositeVideoClip([video, *subtitles])
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        print(f"Video final guardado: {output_path}")
    except Exception as e:
        print(f"Error al agregar subtítulos al video {video_path}: {e}")

def format_time(seconds):
    """Convierte segundos a formato SRT (hh:mm:ss,ms)."""
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

def parse_time(srt_time):
    """Convierte tiempo en formato SRT (hh:mm:ss,ms) a segundos."""
    hours, minutes, seconds = srt_time.split(":")
    seconds, millis = seconds.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000

def main():
    # Abrir ventana para seleccionar el archivo de video
    Tk().withdraw()  # Ocultar la ventana principal de tkinter
    video_path = filedialog.askopenfilename(
        title="Selecciona un archivo de video",
        filetypes=[("Archivos de video", "*.mp4 *.avi *.mov *.mkv")]
    )
    if not video_path:
        print("No se seleccionó ningún archivo. Saliendo...")
        return

    audio_path = video_path.replace(".mp4", ".wav")
    srt_path = video_path.replace(".mp4", ".srt")
    output_path = video_path.replace(".mp4", "_subtitled.mp4")

    # Extraer audio del video
    extract_audio_from_video(video_path, audio_path)

    # Generar subtítulos
    transcribe_audio_to_srt(audio_path, srt_path)

    # Agregar subtítulos al video
    add_subtitles_to_video(video_path, srt_path, output_path)

    # Eliminar el archivo de audio temporal
    if os.path.exists(audio_path):
        os.remove(audio_path)
        print(f"Archivo temporal eliminado: {audio_path}")

if __name__ == "__main__":
    main()
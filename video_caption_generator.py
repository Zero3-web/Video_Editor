import os
from tkinter import Tk, filedialog
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings
import whisper

# Configurar la ruta absoluta de ImageMagick
change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

def transcribe_audio_with_whisper(audio_path):
    """Transcribe audio and return words with timestamps using Whisper."""
    try:
        model = whisper.load_model("base")  # Puedes usar "small", "medium", o "large" según tu hardware
    except Exception as e:
        print(f"Error al cargar el modelo Whisper: {e}")
        return []

    try:
        result = model.transcribe(audio_path, language="es", word_timestamps=True)
    except Exception as e:
        print(f"Error al transcribir el audio: {e}")
        return []

    # Extraer palabras y sus tiempos
    captions = []
    for segment in result.get("segments", []):
        for word_info in segment.get("words", []):
            word = word_info["word"]
            start_time = word_info.get("start", 0)
            end_time = word_info.get("end", 0)
            captions.append((word, start_time, end_time))
    
    # Fallback if no words with timestamps are found
    if not captions:
        print("Advertencia: No se encontraron palabras con tiempos. El audio puede no contener contenido hablado.")
    return captions

def generate_srt_file(captions, srt_path):
    """Generate a .srt file from captions."""
    with open(srt_path, 'w', encoding='utf-8') as srt_file:
        for i, (word, start_time, end_time) in enumerate(captions, start=1):
            start_time_str = format_time(start_time)
            end_time_str = format_time(end_time)
            srt_file.write(f"{i}\n{start_time_str} --> {end_time_str}\n{word}\n\n")

def format_time(seconds):
    """Format time in seconds to SRT time format (hh:mm:ss,ms)."""
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

def generate_captions(video_path, output_path):
    """Generates a .srt file with captions for a video."""
    try:
        # Validar si el archivo de video existe
        if not os.path.exists(video_path):
            print("El archivo de video no existe. Por favor, verifica la ruta.")
            return
        
        # Load the video
        video = VideoFileClip(video_path)
        audio_path = video_path.replace(".mp4", ".wav")
        
        # Extract audio from the video
        print(f"Extrayendo audio a: {audio_path}")
        video.audio.write_audiofile(audio_path)
        
        # Verificar si el archivo de audio fue creado
        if not os.path.exists(audio_path):
            print(f"Error: No se pudo crear el archivo de audio en {audio_path}")
            return
        
        # Transcribir el audio con Whisper
        print("Transcribiendo el audio con Whisper...")
        captions = transcribe_audio_with_whisper(audio_path)
        if not captions:
            print("No se encontraron palabras con tiempos. No se generará el archivo .srt.")
            return
        
        # Generate the .srt file
        srt_path = video_path.replace(".mp4", ".srt")
        generate_srt_file(captions, srt_path)
        print(f"Archivo .srt generado en: {srt_path}")
    
    except Exception as e:
        print(f"Error al generar subtítulos: {e}")
    
    finally:
        # Clean up temporary audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if 'video' in locals():
            video.close()

if __name__ == "__main__":
    # Crear una ventana de diálogo para seleccionar el archivo
    Tk().withdraw()  # Ocultar la ventana principal de tkinter
    video_path = filedialog.askopenfilename(
        title="Selecciona un archivo de video",
        filetypes=[("Archivos de video", "*.mp4 *.avi *.mov *.mkv")]
    )
    
    if not video_path:
        print("No se seleccionó ningún archivo. Saliendo...")
    else:
        # Check for existing .srt file
        srt_path = video_path.replace(".mp4", ".srt")
        if os.path.exists(srt_path):
            print(f"Archivo .srt detectado: {srt_path}")
        else:
            generate_captions(video_path, srt_path)

import streamlit as st
import yt_dlp
import ollama
import whisper
import time
import os
import subprocess
import requests

st.set_page_config(layout="wide")

# Remove black bar by hiding Streamlit's default elements
st.markdown("""
    <style>
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container { padding-top: 0rem; }
    </style>
""", unsafe_allow_html=True)


def download_video(url):
    """Download YouTube video as audio using yt-dlp"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloaded_audio.%(ext)s',
        'noplaylist': True,
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info_dict)

    return file_path


def convert_audio(input_path):
    """Convert audio to WAV for Whisper"""
    output_path = "converted_audio.wav"

    # Run FFmpeg command to convert audio
    command = ["ffmpeg", "-i", input_path, "-ac", "1", "-ar", "16000", output_path, "-y"]
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        st.error(f"❌ FFmpeg conversion failed:\n{result.stderr}")
        raise RuntimeError("FFmpeg conversion failed")

    return output_path


def initialize_model():
    """Initialize Ollama Model"""
    model_name = "llama3.2:latest"
    try:
        response = ollama.chat(model=model_name, messages=[{"role": "user", "content": "Hello!"}])
        if response:
            st.success("✅ Model loaded successfully!")
        return model_name
    except Exception as e:
        st.error(f"❌ Ollama Model failed: {str(e)}")
        return None


def summarize_text(text, model):
    """Summarize text using Ollama"""
    try:
        response = ollama.chat(model=model, messages=[{"role": "user", "content": f"Summarize this: {text}"}])
        return response.get("message", {}).get("content", "").strip()
    except Exception as e:
        st.error(f"❌ Failed to summarize: {str(e)}")
        return None


def transcribe_audio(file_path):
    """Transcribe audio using Whisper"""
    st.success("✅ Transcribing Audio Using Whisper...")

    # Convert to WAV if needed
    if not file_path.endswith(".wav"):
        file_path = convert_audio(file_path)

    model = whisper.load_model("small")  
    result = model.transcribe(file_path)
    
    if result and "text" in result:
        st.success("✅ Transcription Complete!")
        return result["text"]
    
    st.error("❌ Transcription failed.")
    return None

def update_duckdns():
    token = "0711ae13-beab-41e1-8fc4-963bdd70ad90"  # Your DuckDNS token
    domain = "semisizer"  # Your DuckDNS domain (without http:// or .duckdns.org)
    url = f"https://www.duckdns.org/update?domains={domain}&token={token}&ip="
    
    # Send the request to DuckDNS
    response = requests.get(url)
    
    if response.status_code == 200:
        print("DuckDNS IP update successful!")
    else:
        print("Failed to update DuckDNS IP.")

def set_background(image_url):
    """Set background image with a 50% transparent black gradient overlay"""
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.5)), 
                        url("{image_url}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


def cleanup_files():
    """Delete temporary files to free up space"""
    files = ["downloaded_audio.mp3", "converted_audio.wav"]
    for file in files:
        if os.path.exists(file):
            os.remove(file)


def main():
    """Main Streamlit App"""
    set_background("https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/b3be1dae-3caa-4d45-be6c-3de586ba95e2/deogvao-f8b9492f-a015-4609-9ce8-556325185e58.jpg/v1/fill/w_1192,h_670,q_70,strp/meteor_shower_by_bisbiswas_deogvao-pre.jpg?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9MTA4MCIsInBhdGgiOiJcL2ZcL2IzYmUxZGFlLTNjYWEtNGQ0NS1iZTZjLTNkZTU4NmJhOTVlMlwvZGVvZ3Zhby1mOGI5NDkyZi1hMDE1LTQ2MDktOWNlOC01NTYzMjUxODVlNTguanBnIiwid2lkdGgiOiI8PTE5MjAifV1dLCJhdWQiOlsidXJuOnNlcnZpY2U6aW1hZ2Uub3BlcmF0aW9ucyJdfQ.gAHH3jtyMREfWVHw-n7dPx1UAZolPk8Wxif76Jqi9Ns")
    st.markdown("<h1 style='text-align: center;'>Semisizer</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>YouTube Video Summarizer</h3>", unsafe_allow_html=True)

    with st.expander("About the App"):
        st.write("This app extracts and summarizes YouTube video content using AI.")
        st.write("Enter a YouTube URL and click 'Summarize' to start.")

    youtube_url = st.text_input("🔗Enter YouTube URL")

    if st.button("Summarize ▶") and youtube_url:
        start_time = time.time()

        try:
            st.success("✅ Downloading Audio...")
            file_path = download_video(youtube_url)

            st.info("🔄 Initializing AI Model...")
            model = initialize_model()
            if not model:
                return

            st.info("🎙️ Transcribing Audio...")
            transcription = transcribe_audio(file_path)
            if not transcription:
                return

            st.info("📝 Generating Summary...")
            summary = summarize_text(transcription, model)

            end_time = time.time()
            elapsed_time = end_time - start_time

            col1, col2 = st.columns([1, 1])
            with col1:
                st.video(youtube_url)
            with col2:
                st.header("📜 Summary")
                if summary:
                    st.success(summary)
                    st.write(f"⏳ Processing Time: {elapsed_time:.2f} seconds")
                else:
                    st.error("❌ Summary generation failed.")

            # Cleanup files
            cleanup_files()

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()

    # Clean up files after processing
def delete_file(file_path):
    """Delete file if it exists and exit."""
    if os.path.exists(file_path):
        os.remove(file_path)
        return  # Exit the function immediately after deletion

# Call the function for both files
delete_file("downloaded_audio.webm")  # Adjust based on actual format
delete_file("converted_audio.wav")

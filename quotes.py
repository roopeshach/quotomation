from datetime import datetime
import os
import random
import time
import pandas as pd
import requests
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from englisttohindi.englisttohindi import EngtoHindi
from webdriver_manager.chrome import ChromeDriverManager
import streamlit as st
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Fetching a random quote from ZenQuotes API
def get_quote():
    """
    Fetch a random quote from the ZenQuotes API.
    """
    url = "https://zenquotes.io/api/random"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data[0]["q"], data[0]["a"]  # Quote and author
    return None, None


# Translating the quote to Hindi
def translate_to_hindi(text):
    res = EngtoHindi(text)
    return res.convert


# Function to get audio from the text-to-speech service

def get_audio_data(text, driver, lang="in"):
    if lang == "in":
        driver.get("https://crikk.com/text-to-speech/hindi/")
    else:
        raise ValueError("Unsupported language code")

    try:
        textarea = driver.find_element(By.ID, "promptText")
        textarea.clear()
        textarea.send_keys(text)
    except NoSuchElementException:
        print("Textarea not found.")
        return None

    try:
        generate_button = driver.find_element(By.ID, "action_submit")
        driver.execute_script("arguments[0].scrollIntoView(true);", generate_button)
        time.sleep(1)
        generate_button.click()
    except (NoSuchElementException, ElementClickInterceptedException):
        print("Generate button click failed.")
        return None

    audio_element_xpath = "//audio/source[@id='audioSource']"
    for attempt in range(10):
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, audio_element_xpath))
            )
            audio_element = driver.find_element(By.XPATH, audio_element_xpath)
            audio_src = audio_element.get_attribute('src')
            
            print(f"Attempt {attempt + 1}: Found audio source URL: {audio_src}")

            if "https://crikk.com/app/app/text-to-speech/" in audio_src:
                audio_response = requests.get(audio_src)
                print(f"Audio response status: {audio_response.status_code}")
                if audio_response.status_code == 200:
                    return audio_response.content
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            pass
    return None


# Save the audio data to a file (MP3)
def save_audio_to_mp3(audio_data, filename):
    with open(filename, "wb") as audio_file:
        audio_file.write(audio_data)


# Merge TTS audio with background music
def merge_audio(tts_audio_path, background_audio_dir="audios", output_dir="output_temp/audios"):
    os.makedirs(output_dir, exist_ok=True)
    tts_audio = AudioSegment.from_mp3(tts_audio_path)

    background_files = [f for f in os.listdir(background_audio_dir) if f.endswith(".mp3")]
    if not background_files:
        return None

    background_audio_path = os.path.join(background_audio_dir, random.choice(background_files))
    background_audio = AudioSegment.from_mp3(background_audio_path)

    if len(background_audio) > len(tts_audio):
        background_audio = background_audio[:len(tts_audio)]
    else:
        background_audio = background_audio * (len(tts_audio) // len(background_audio)) + background_audio[:len(tts_audio) % len(background_audio)]

    background_audio = background_audio - 10
    final_audio = tts_audio.overlay(background_audio)

    final_audio_path = os.path.join(output_dir, os.path.basename(tts_audio_path))
    final_audio.export(final_audio_path, format="mp3")
    return final_audio_path


# Combine video and audio
def create_video_with_audio(video_path, audio_path, output_path):
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)

    video_clip = video_clip.subclip(0, min(video_clip.duration, audio_clip.duration))
    video_clip = video_clip.set_audio(audio_clip)

    video_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    return output_path

# Function to get today's date in YYYY-MM-DD format
def get_today_date():
    return datetime.now().strftime("%Y-%m-%d")


# Function to delete a file
def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False


# Streamlit app
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select a page", ["Generator", "List Files"])

    today_date = get_today_date()

    # Generator Page
    if page == "Generator":
        st.title("Quote Audio & Video Generator")

        # Audio generation form
        with st.form("quote_form"):
            num_quotes = st.number_input("Enter the number of quotes to generate:", min_value=1, max_value=10, value=1)
            generate_audio_button = st.form_submit_button("Generate Audio")

        if generate_audio_button:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920x1080")
            chrome_options.add_argument("--mute-audio")

            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            try:
                for i in range(num_quotes):
                    st.write(f"Generating audio for quote {i + 1}...")
                    progress = st.progress(0)

                    quote, author = get_quote()
                    if not quote or not author:
                        st.error(f"Failed to fetch quote {i + 1}.")
                        progress.progress(1.0)
                        continue

                    hindi_quote = translate_to_hindi(quote)
                    tts_text = f'{author} says "{quote}"\nहिंदी में\n"{hindi_quote}"'

                    audio_data = get_audio_data(tts_text, driver)
                    if not audio_data:
                        st.error(f"Failed to generate audio for quote {i + 1}.")
                        progress.progress(1.0)
                        continue

                    # File names include author and today's date
                    safe_author_name = author.replace(" ", "_").replace(",", "").replace(".", "")
                    tts_audio_path = f"{safe_author_name}_{today_date}_tts_audio.mp3"
                    save_audio_to_mp3(audio_data, tts_audio_path)


                    final_audio_path = merge_audio(tts_audio_path)
                    if not final_audio_path:
                        st.error(f"Failed to merge audio for quote {i + 1}.")
                        progress.progress(1.0)
                        continue

                    st.success(f"Audio for Quote {i + 1} generated successfully.")
                    progress.progress(1.0)
            finally:
                driver.quit()

            # Video selection and generation
            video_files = [f for f in os.listdir("videos") if f.endswith(".mp4")]
            audio_files = [f for f in os.listdir("output_temp/audios") if f.endswith(".mp3")]

            for i, audio_file in enumerate(audio_files):
                st.subheader(f"Audio {i + 1}")
                st.audio(os.path.join("output_temp/audios", audio_file))

                # Use session_state to maintain state
                if f"selected_video_{i}" not in st.session_state:
                    st.session_state[f"selected_video_{i}"] = None

                selected_video = st.radio(
                        f"Select a video for Audio {i + 1}:",
                        video_files,
                        key=f"video_radio_{i}",
                        index=0 if not st.session_state.get(f"selected_video_{i}") else video_files.index(st.session_state[f"selected_video_{i}"]),
                    )


                # Save the selected video in session_state
                if selected_video:
                    st.session_state[f"selected_video_{i}"] = selected_video


                if st.button(f"Generate Video {i + 1}"):
                    video_path = os.path.join("videos", selected_video)
                    if not os.path.exists(video_path):
                        st.error(f"Video file {selected_video} does not exist.")
                        continue
                    audio_path = os.path.join("output_temp/audios", audio_file)
                    author_name = audio_file.split("_")[0]  # Extract the author name from the audio file
                    output_video_path = f"output/{author_name}_{today_date}_final_video.mp4"

                    if os.path.exists(audio_path):
                        create_video_with_audio(video_path, audio_path, output_video_path)
                        st.video(output_video_path)
                        st.success(f"Video {i + 1} generated successfully.")
                    else:
                        st.error(f"No matching audio for Video {i + 1}.")


    # List Files Page
    elif page == "List Files":
        st.title("List of Generated Files")

        # Fetch audio and video files
        audio_dir = "output_temp/audios"
        video_dir = "output"

        audio_files = [f for f in os.listdir(audio_dir) if f.endswith(".mp3")]
        video_files = [f for f in os.listdir(video_dir) if f.endswith(".mp4")]

        # Display Audio Files Table
        st.subheader("Audio Files")
        if audio_files:
            audio_data = [{"File Name": f, "Path": os.path.join(audio_dir, f)} for f in audio_files]
            audio_df = pd.DataFrame(audio_data)

            for index, row in audio_df.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(row["File Name"])
                with col2:
                    # Add Audio Player for preview
                    st.audio(row["Path"])
                with col3:
                    if st.button("Delete", key=f"delete_audio_{index}"):
                        if delete_file(row["Path"]):
                            st.success(f"Deleted {row['File Name']}")
                            st.cache_data.clear()  # Refresh page to reflect deletion
                        else:
                            st.error(f"Failed to delete {row['File Name']}")
        else:
            st.write("No audio files found.")

        # Display Video Files Table
        st.subheader("Video Files")
        if video_files:
            video_data = [{"File Name": f, "Path": os.path.join(video_dir, f)} for f in video_files]
            video_df = pd.DataFrame(video_data)

            for index, row in video_df.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(row["File Name"])
                with col2:
                    # Add Video Preview in small size (100x150)
                    video_path = row["Path"]
                    st.video(video_path, start_time=0)
                with col3:
                    if st.button("Delete", key=f"delete_video_{index}"):
                        if delete_file(row["Path"]):
                            st.success(f"Deleted {row['File Name']}")
                            st.cache_data.clear()  # Refresh page to reflect deletion
                        else:
                            st.error(f"Failed to delete {row['File Name']}")
        else:
            st.write("No video files found.")


if __name__ == "__main__":
    main()

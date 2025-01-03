import json
import os
import random
import time
import numpy as np
import requests
from datetime import datetime
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip, ImageClip
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from englisttohindi.englisttohindi import EngtoHindi
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image, ImageDraw, ImageFont
from webdriver_manager.core.os_manager import ChromeType
import streamlit as st


# Fetching a random quote from ZenQuotes API
def get_quote():
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
def merge_audio(tts_audio_path, background_audio_dir="audios", output_dir="output/audios"):
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


def create_caption_image(text, size, font_path='arial.ttf'):
    # Create an image with the desired size and transparent background
    img = Image.new('RGBA', size, (0, 0, 0, 0))  # RGBA for transparency
    draw = ImageDraw.Draw(img)
    
    # Load font and set size
    try:
        font = ImageFont.truetype(font_path, 50)  # Adjust the font size as needed
    except IOError:
        font = ImageFont.load_default()  # Fallback to default font if TTF not found

    # Get text bounding box and calculate positioning (centered text)
    bbox = draw.textbbox((0, 0), text, font=font)  # Get bounding box for the text
    text_width = bbox[2] - bbox[0]  # Width of the text
    text_height = bbox[3] - bbox[1]  # Height of the text
    position = ((size[0] - text_width) / 2, (size[1] - text_height) / 2)
    
    # Add text to image
    draw.text(position, text, font=font, fill='white')  # White text
    
    return img

def create_video_with_audio(video_path, audio_path, output_path, captions_texts):
    video_clip = VideoFileClip(video_path)
    audio_clip = AudioFileClip(audio_path)

    # Set the video clip to match the duration of the audio clip
    video_clip = video_clip.subclip(0, min(video_clip.duration, audio_clip.duration))
    video_clip = video_clip.set_audio(audio_clip)

    text_clips = []
    start_time = 0  # Start time for captions

    # Generate caption images and sync them with the audio
    for i, text in enumerate(captions_texts):
        # Create caption image with PIL
        caption_image = create_caption_image(text, video_clip.size)

        # Convert the PIL image to a numpy array for MoviePy
        caption_image_np = np.array(caption_image)

        # Convert the numpy array to a MoviePy ImageClip
        caption_clip = ImageClip(caption_image_np, duration=3)  # Adjust duration per caption (default 3 sec)
        caption_clip = caption_clip.set_position('center').set_start(start_time)

        # Add to the list of text clips
        text_clips.append(caption_clip)

        # Increment the start time for the next caption
        start_time += 3  # Adjust this for the interval between captions

    # Combine the video and the text clips into a final video
    final_clip = CompositeVideoClip([video_clip] + text_clips)

    # Write the final video to a file
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

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


@st.cache_resource
def init_driver():
    # Setting Chrome options for headless browser execution
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--no-sandbox")  # Needed for some cloud environments
    chrome_options.add_argument("--disable-dev-shm-usage")  # Prevents shared memory issues

    # Dynamically fetch and configure the Chromium driver
    service = Service(
        ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
    )
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver



VIDEO_METADATA_FILE = "video_metadata.json"

# Function to load or initialize the video metadata
def load_video_metadata():
    if os.path.exists(VIDEO_METADATA_FILE):
        with open(VIDEO_METADATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Function to save video metadata to the JSON file
def save_video_metadata(metadata):
    with open(VIDEO_METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=4)
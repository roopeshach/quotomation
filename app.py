import json
import streamlit as st
import os
import pandas as pd
from functions import (
    get_quote, 
    translate_to_hindi, 
    get_audio_data, 
    save_audio_to_mp3, 
    merge_audio, 
    create_video_with_audio, 
    get_today_date, 
    delete_file, 
    init_driver
)



# Function to save audio metadata
def save_audio_metadata(metadata, metadata_file="audio_metadata.json"):
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            existing_metadata = json.load(f)
    else:
        existing_metadata = {}

    existing_metadata.update(metadata)

    with open(metadata_file, "w") as f:
        json.dump(existing_metadata, f, indent=4)

# Function to generate audio and save metadata
def generate_audio():
    today_date = get_today_date()
    st.title("Generate Audio from Quote")

    with st.form("quote_form"):
        num_quotes = st.number_input("Enter the number of quotes to generate:", min_value=1, max_value=10, value=1)
        generate_audio_button = st.form_submit_button("Generate Audio")

    if generate_audio_button:
        driver = init_driver()
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

            # Safe file name for audio file
            safe_author_name = author.replace(" ", "_").replace(",", "").replace(".", "")
            tts_audio_path = f"{safe_author_name}_{today_date}_tts_audio.mp3"
            save_audio_to_mp3(audio_data, tts_audio_path)

            # Save audio metadata (quote and author)
            audio_metadata = {
                tts_audio_path: {
                    "quote": quote,
                    "author": author,
                    "hindi_quote": hindi_quote,
                    "tts_text": tts_text
                }
            }
            save_audio_metadata(audio_metadata)

            final_audio_path = merge_audio(tts_audio_path)
            if not final_audio_path:
                st.error(f"Failed to merge audio for quote {i + 1}.")
                progress.progress(1.0)
                continue

            st.success(f"Audio for Quote {i + 1} generated successfully.")
            progress.progress(1.0)
        driver.quit()




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
def generate_video():
    today_date = get_today_date()
    st.title("Generate Video with Audio")

    # Fetch available audio and video files
    audio_files = [f for f in os.listdir("output/audios") if f.endswith(".mp3")]
    video_files = [f for f in os.listdir("videos") if f.endswith(".mp4")]

    if audio_files:
        selected_audio = st.selectbox("Select an Audio File", audio_files)
    else:
        st.error("No audio files found!")
        return

    if video_files:
        selected_video = st.selectbox("Select a Video File", video_files)
    else:
        st.error("No video files found!")
        return

    # Use session state to hold form data and avoid resetting
    if 'video_details' not in st.session_state:
        st.session_state.video_details = {}

    # If "Generate Video with Details" button is pressed
    with st.form(key="video_details_form"):
        title = st.text_input("Title", value=st.session_state.video_details.get('title', ''))
        description = st.text_area("Description", value=st.session_state.video_details.get('description', ''))
        hashtags = st.text_input("Hashtags (comma separated)", value=st.session_state.video_details.get('hashtags', ''))
        submit_button = st.form_submit_button("Submit Details")

        # When submit is pressed, save the data to session state
        if submit_button:
            st.session_state.video_details = {
                'title': title,
                'description': description,
                'hashtags': hashtags.split(',') if hashtags else []
            }

            st.write("Generating video with details...")

            if not title or not description or not hashtags:
                st.error("Please fill all fields.")
                return

            # Load existing video metadata
            metadata = load_video_metadata()

            # Create new metadata for the video
            video_metadata = {
                "title": title,
                "description": description,
                "hashtags": hashtags.split(","),
                "audio_file": selected_audio,
                "video_file": selected_video,
                "date_created": today_date
            }

            # Define path for final video
            video_path = os.path.join("output", "videos", f"{title}_{today_date}.mp4")

            # Combine the selected audio and video into a final video
            audio_path = os.path.join("output", "audios", selected_audio)
            video_file_path = os.path.join("videos", selected_video)

            # Load audio metadata to extract captions text
            with open("audio_metadata.json", "r") as f:
                audio_metadata = json.load(f)

            # Retrieve the TTS text (captions) for the selected audio
            captions_texts = []
            for audio_file, metadata in audio_metadata.items():
                if selected_audio in audio_file:
                    captions_texts.append(metadata["tts_text"])

            # Debug: Check paths and captions
            st.write(f"Audio path: {audio_path}")
            st.write(f"Video path: {video_file_path}")
            st.write(f"Final video path: {video_path}")
            st.write(f"Captions: {captions_texts}")

            try:
                # Create the final video with synchronized captions
                video_path_final = create_video_with_audio(video_file_path, audio_path, video_path, captions_texts)

                # Save video metadata
                metadata[video_path_final] = video_metadata
                save_video_metadata(metadata)

                # Show success message and display the created video
                st.success(f"Video '{title}' created successfully!")
                st.video(video_path_final)  # Display the generated video

                # Delete any mp3 file in the current directory after video generation
                for file in os.listdir():
                    if file.endswith(".mp3"):
                        os.remove(file)
                        st.success(f"Successfully deleted the audio file: {file}")

            except Exception as e:
                st.error(f"Error during video creation: {e}")
                st.write("Video creation failed, please check logs.")



def list_files():
    st.title("List Files")

    # Fetch mp3 and mp4 files in the current directory
    audio_files = [f for f in os.listdir('output/audios') if f.endswith(".mp3")]
    video_files = [f for f in os.listdir("output/videos") if f.endswith(".mp4")]


    # Load video metadata from the JSON file
    video_metadata = load_video_metadata()

    st.subheader("Generated Audio Files")
    if audio_files:
        for audio_file in audio_files:
            # Display audio player for each .mp3 file
            audio_path = os.path.join("output","audios", audio_file)
            st.write(audio_file)
            st.audio(audio_path, format="audio/mp3")

            # Button to delete the audio file
            delete_button = st.button(f"Delete {audio_file}", key=f"delete_audio_{audio_file}")
            if delete_button:
                if delete_file(os.path.join("output","audios", audio_file)):
                    st.success(f"Successfully deleted {audio_file}")
                else:
                    st.error(f"Failed to delete {audio_file}")
    else:
        st.write("No audio files found.")

    st.subheader("Generated Video Files")
    if video_files:
        for video_file in video_files:
            # Small preview of the video with custom CSS for size
            video_path = os.path.join("output","videos", video_file)
            st.write(video_file)
            # Check if the video path exists
            if os.path.exists(video_path):
                st.video(video_path)  # Render video using Streamlit's built-in player
            else:
                st.error(f"Video file {video_file} not found.")

            # Display metadata for the video
            metadata = video_metadata.get(video_path, {})
            if metadata:
                st.write(f"**Title**: {metadata.get('title', 'N/A')}")
                st.write(f"**Description**: {metadata.get('description', 'N/A')}")
                st.write(f"**Hashtags**: {', '.join(metadata.get('hashtags', []))}")
                st.write(f"**Date Created**: {metadata.get('date_created', 'N/A')}")
            else:
                st.write("No metadata available.")

            # Button to delete the video file
            delete_button = st.button(f"Delete {video_file}", key=f"delete_video_{video_file}")
            if delete_button:
                video_path_full = os.path.join("output",'videos', video_file)
                if delete_file(video_path_full):
                    st.success(f"Successfully deleted {video_file}")
                else:
                    st.error(f"Failed to delete {video_file}")
    else:
        st.write("No video files found.")



# Main function to switch between pages
def main():
    st.sidebar.title("Content Builder   ")
    page = st.sidebar.radio("Select a page", ["Generate Audio", "Generate Video", "List Files"])

    if page == "Generate Audio":
        generate_audio()
    elif page == "Generate Video":
        generate_video()
    elif page == "List Files":
        list_files()

if __name__ == "__main__":
    main()

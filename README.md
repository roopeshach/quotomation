# Video and Audio Captioning Tool

This project is a Streamlit-based application for generating videos with audio and synchronized captions. It uses various tools and libraries like MoviePy, PIL, and a text-to-speech engine to create engaging media content with animated captions.

---

## Features

- **Audio Generation**: Generate audio files using quotes, authors, and translations in Hindi.
- **Video Creation**: Combine video files with generated audio and add synchronized captions.
- **Captions Synchronization**: Automatically synchronize captions with the audio content, using PIL for custom caption designs.
- **Metadata Handling**: Maintain metadata for both audio and video files, including title, description, and hashtags.
- **File Management**: List and delete generated audio and video files within the application.

---

## Requirements

- Python 3.8 or higher
- Streamlit
- MoviePy
- PIL (Pillow)
- Selenium (for TTS audio generation)
- ImageMagick (if needed for advanced rendering)

---

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/roopeshach/quotomation.git
   cd quotomation
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Ensure ImageMagick is installed and configured correctly (if needed for advanced video editing).

---

## Usage

1. **Run the Streamlit App**:

   ```bash
   streamlit run app.py
   ```

2. **Generate Audio**:
   - Navigate to the "Generate Audio" page.
   - Enter the number of quotes and generate audio files using the integrated TTS engine.

3. **Generate Video**:
   - Go to the "Generate Video" page.
   - Select an audio file and a video file.
   - Add details like title, description, and hashtags.
   - Generate the video with synchronized captions.

4. **Manage Files**:
   - Use the "List Files" page to view, play, and delete generated audio and video files.

---

## Project Structure

```
├── app.py                  # Main Streamlit application file
├── functions.py            # Core functions for video and audio generation
├── output/                 # Generated output files (excluded in .gitignore)
│   ├── audios/             # Generated audio files
│   ├── videos/             # Generated video files
├── metadata.json           # Metadata for generated files
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── .gitignore              # Git ignore rules
```

---

## Known Issues

- Ensure ImageMagick is correctly installed and configured if MoviePy-related errors occur.
- Make sure the `videos/` and `output/audios/` directories exist before running the application.

---

## Contribution

Contributions are welcome! Feel free to open issues or submit pull requests for improvements or bug fixes.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Streamlit](https://streamlit.io) for the web application framework.
- [MoviePy](https://zulko.github.io/moviepy/) for video and audio processing.
- [Pillow](https://pillow.readthedocs.io/) for creating custom captions.
- [Selenium](https://www.selenium.dev/) for text-to-speech integration.



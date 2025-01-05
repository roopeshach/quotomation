import streamlit as st

from streamlit_pages import generate_audio, generate_video, list_audio_templates, list_files, list_video_templates, upload_files



# Main function to switch between pages
def main():
    st.sidebar.title("Content Builder")
    page = st.sidebar.radio("Select a page", ["Generate Audio", "Generate Video", "List Generated Files", "Upload Templates", "List Audio Templates", "List Video Templates"])

    if page == "Generate Audio":
        generate_audio()
    elif page == "Generate Video":
        generate_video()
    elif page == "List Generated Files":
        list_files()
    elif page == "Upload Templates":
        upload_files()
    elif page == "List Audio Templates":
        list_audio_templates()
    elif page == "List Video Templates":
        list_video_templates()

if __name__ == "__main__":
    main()

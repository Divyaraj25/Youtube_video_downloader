````markdown
# YouTube Downloader (pytubefix)

This is a simple yet powerful desktop application built with Python and Tkinter, leveraging the `pytubefix` library to download YouTube videos, audio, and entire playlists. It provides a user-friendly graphical interface with real-time logging and progress tracking.

---

## Features

- **Download Types:** Choose to download single videos, audio-only versions, or entire playlists.
- **Quality Selection:** For single videos and playlists, select from available resolutions and audio bitrates.
- **Progress Bar:** Visual feedback on download progress.
- **Detailed Logging:** A dedicated log area provides real-time status updates, including connection details, download progress, and error messages.
- **Thread-Safe Operations:** Downloads run in separate threads, keeping the UI responsive.
- **Directory Selection:** Easily choose where to save your downloaded files.

---

## Prerequisites

Before running the application, ensure you have the following installed:

- **Python 3.x:** Download from [python.org](https://www.python.org/).
- **`pytubefix` library:** Install it using pip:
  ```bash
  pip install pytubefix
  ```
- **`tkinter` (usually bundled with Python):** If you encounter issues, you might need to install it separately depending on your Python distribution.

---

## How to Run

1.  **Save the code:** Save the provided Python code as a `.py` file (e.g., `youtube_downloader.py`).
2.  **Open a terminal or command prompt:** Navigate to the directory where you saved the file.
3.  **Run the application:**
    ```bash
    python youtube_downloader.py
    ```

---

## Usage

1.  **Select Download Type:** Choose "Single Video", "Audio Only", or "Playlist" using the radio buttons.
2.  **Enter YouTube URL:** Paste the URL of the video or playlist into the "Enter YouTube URL" field. The application will automatically attempt to fetch available qualities.
3.  **Select Quality (if applicable):** Once qualities are fetched, select your desired resolution or audio bitrate from the dropdown menu.
4.  **Click "Download":** A dialog will appear asking you to choose a directory to save your downloaded file(s).
5.  **Monitor Progress:** The progress bar and log area will update with the download status.

---

## Error Handling

The application includes basic error handling and will display messages in the log area for issues such as:

- Invalid URLs
- Network connection problems
- No compatible streams found
- Empty or private playlists

---

## Troubleshooting

- **"FATAL ERROR: Could not fetch details..."**:
  - Double-check that the URL is correct and accessible.
  - Ensure you have an active internet connection.
  - Sometimes YouTube might block `pytubefix` temporarily; try again later.
- **Downloads are slow or get stuck**:
  - Your internet connection might be unstable.
  - YouTube's servers might be experiencing high traffic.
- **`tkinter` not found**: If you get an error related to `tkinter`, ensure it's properly installed with your Python distribution.
````

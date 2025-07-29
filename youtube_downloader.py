import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pytubefix import YouTube, Playlist
import threading
import queue

class YouTubeDownloaderApp:
    """
    A desktop application for downloading YouTube videos, audio, and playlists.
    This version uses 'pytubefix' and includes a detailed logging area for status and errors.
    """
    def __init__(self, root):
        """
        Initializes the main application window and its widgets.
        """
        self.root = root
        self.root.title("YouTube Downloader (pytubefix)")
        self.root.geometry("650x650") # Increased height for the log
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")

        # --- Style configuration ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#f0f0f0", font=("Helvetica", 12))
        style.configure("TButton", font=("Helvetica", 12, "bold"), padding=10)
        style.configure("TRadiobutton", background="#f0f0f0", font=("Helvetica", 11))
        style.configure("TEntry", font=("Helvetica", 12))
        style.configure("TCombobox", font=("Helvetica", 12))

        # --- Main Frame ---
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Top controls frame ---
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, expand=True)

        # --- Download Type Selection ---
        type_frame = ttk.LabelFrame(controls_frame, text="1. Choose Download Type", padding="10")
        type_frame.pack(fill=tk.X, pady=(0, 10))

        self.download_type = tk.StringVar(value="video")
        
        ttk.Radiobutton(type_frame, text="Single Video", variable=self.download_type, value="video", command=self.update_ui_for_type).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(type_frame, text="Audio Only", variable=self.download_type, value="audio", command=self.update_ui_for_type).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(type_frame, text="Playlist", variable=self.download_type, value="playlist", command=self.update_ui_for_type).pack(anchor=tk.W, pady=2)

        # --- URL Input ---
        url_frame = ttk.LabelFrame(controls_frame, text="2. Enter YouTube URL", padding="10")
        url_frame.pack(fill=tk.X, pady=10)

        self.url_entry = ttk.Entry(url_frame, width=60)
        self.url_entry.pack(fill=tk.X, expand=True, ipady=5)
        self.url_entry.bind("<KeyRelease>", self.on_url_change)

        # --- Quality Selection ---
        self.quality_frame = ttk.LabelFrame(controls_frame, text="3. Select Quality", padding="10")
        self.quality_frame.pack(fill=tk.X, pady=10)
        
        self.quality_var = tk.StringVar()
        self.quality_menu = ttk.Combobox(self.quality_frame, textvariable=self.quality_var, state="disabled", width=40)
        self.quality_menu.pack(pady=5, ipady=5, fill=tk.X)

        # --- Download Controls & Progress ---
        download_controls_frame = ttk.Frame(controls_frame)
        download_controls_frame.pack(fill=tk.X, pady=10)

        self.progress_bar = ttk.Progressbar(download_controls_frame, orient="horizontal", length=100, mode="determinate")
        self.progress_bar.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=(0, 10))

        self.download_button = ttk.Button(download_controls_frame, text="Download", command=self.start_download_thread, state="disabled")
        self.download_button.pack(side=tk.RIGHT)

        # --- Log Area ---
        log_frame = ttk.LabelFrame(main_frame, text="Logs & Status", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.log_text = scrolledtext.ScrolledText(log_frame, state='disabled', height=10, wrap=tk.WORD, font=("Consolas", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.stream_options = []
        self.log_queue = queue.Queue()
        self.log("Welcome! Please select a download type and enter a URL.")
        self.root.after(100, self.process_log_queue)

    def process_log_queue(self):
        """Processes messages in the log queue to update the UI safely from the main thread."""
        while not self.log_queue.empty():
            message = self.log_queue.get_nowait()
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, message + '\n')
            self.log_text.config(state='disabled')
            self.log_text.see(tk.END)
        self.root.after(100, self.process_log_queue)

    def log(self, message):
        """Adds a message to the log area and the console in a thread-safe way."""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}") # For console debugging
        self.log_queue.put(f"[{timestamp}] {message}")

    def update_ui_for_type(self):
        """Updates the UI based on the selected download type."""
        self.clear_fields()
        download_type = self.download_type.get()
        self.log(f"Switched to '{download_type.capitalize()}' download type.")
        if download_type == "playlist":
            self.quality_frame.config(text="3. Select Quality (for all videos)")
        else:
            self.quality_frame.config(text="3. Select Quality")

    def on_url_change(self, event=None):
        """Handles the event when the URL entry changes."""
        url = self.url_entry.get()
        if len(url) > 10: # Basic check to avoid firing on every keystroke
            self.log("URL detected. Starting to fetch details...")
            threading.Thread(target=self.fetch_stream_options, daemon=True).start()
        else:
            self.clear_fields()

    def fetch_stream_options(self):
        """Fetches available video/audio streams from the YouTube URL."""
        url = self.url_entry.get()
        download_type = self.download_type.get()
        
        # Disable UI elements during fetch
        self.root.after(0, lambda: self.quality_menu.config(state="disabled"))
        self.root.after(0, lambda: self.download_button.config(state="disabled"))
        
        try:
            self.log(f"Connecting to URL: {url}")
            if download_type in ["video", "audio"]:
                yt = YouTube(url, on_progress_callback=self.on_progress)
                self.log(f"Successfully connected. Video Title: {yt.title}")
                if download_type == "video":
                    self.log("Fetching available video streams (progressive MP4)...")
                    streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
                    self.stream_options = [(s, f"{s.resolution} - {s.filesize_mb:.2f} MB") for s in streams]
                else: # audio
                    self.log("Fetching available audio streams (MP4)...")
                    streams = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc()
                    self.stream_options = [(s, f"{s.abr} - {s.filesize_mb:.2f} MB") for s in streams]

            elif download_type == "playlist":
                pl = Playlist(url)
                self.log(f"Successfully connected. Playlist Title: '{pl.title}'")
                self.log(f"Found {len(pl.videos)} videos in the playlist.")
                if not pl.videos:
                    self.log("Error: This playlist is empty or private.")
                    return
                yt = pl.videos[0]
                self.log(f"Fetching sample quality options from first video: '{yt.title}'")
                streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
                self.stream_options = [(s.itag, f"{s.resolution} - {s.mime_type}") for s in streams]

            if not self.stream_options:
                self.log("Error: No compatible streams were found for this URL.")
                return

            self.log(f"Found {len(self.stream_options)} quality options.")
            
            # Update UI from the main thread
            def update_ui():
                self.quality_menu['values'] = [opt[1] for opt in self.stream_options]
                self.quality_menu.config(state="readonly")
                self.quality_menu.current(0)
                self.download_button.config(state="normal")
                self.log("Ready to download. Please select a quality and click 'Download'.")
            
            self.root.after(0, update_ui)

        except Exception as e:
            self.log(f"FATAL ERROR: Could not fetch details. Please check the URL and your internet connection.")
            self.log(f"--> Exception: {str(e)}")
            self.root.after(0, self.clear_fields)

    def start_download_thread(self):
        """Starts the download process in a new thread to keep the UI responsive."""
        self.download_button.config(state="disabled")
        self.progress_bar['value'] = 0
        self.log("Download button clicked. Starting download process...")
        threading.Thread(target=self.download, daemon=True).start()

    def download(self):
        """Handles the actual download logic."""
        url = self.url_entry.get()
        download_type = self.download_type.get()
        selected_quality_str = self.quality_var.get()

        try:
            self.log("Please select a directory to save your file(s).")
            # Must ask for directory from the main thread
            save_path = self.ask_for_directory()
            if not save_path:
                self.log("Download cancelled: No directory was selected.")
                self.root.after(0, lambda: self.download_button.config(state="normal"))
                return
            
            self.log(f"Files will be saved to: {save_path}")

            if download_type == "playlist":
                self.download_playlist(url, selected_quality_str, save_path)
            else:
                self.download_single_item(url, selected_quality_str, save_path)

        except Exception as e:
            self.log(f"An unexpected error occurred during the download process.")
            self.log(f"--> Exception: {str(e)}")
            messagebox.showerror("Download Error", f"An error occurred: {str(e)}")
        finally:
            self.root.after(0, lambda: self.download_button.config(state="normal"))
    
    def ask_for_directory(self):
        """Asks for directory in a thread-safe way."""
        # This is a bit of a trick. We can't call filedialog from a non-main thread.
        # So we use a queue to get the result back.
        path_queue = queue.Queue()
        self.root.after(0, lambda: path_queue.put(filedialog.askdirectory()))
        return path_queue.get()


    def download_single_item(self, url, quality_str, path):
        """Downloads a single video or audio file."""
        yt = YouTube(url, on_progress_callback=self.on_progress)
        
        selected_stream = None
        for stream, desc in self.stream_options:
            if desc == quality_str:
                selected_stream = stream
                break
        
        if not selected_stream:
            self.log(f"Error: Could not find the selected stream for '{quality_str}'.")
            return

        self.log(f"Starting download for: '{yt.title}'")
        selected_stream.download(output_path=path)
        self.log(f"SUCCESS: Download complete for '{yt.title}'.")
        self.root.after(0, lambda: messagebox.showinfo("Success", f"'{yt.title}' has been downloaded successfully!"))

    def download_playlist(self, url, quality_str, path):
        """Downloads an entire playlist."""
        pl = Playlist(url)
        
        selected_itag = None
        for itag, desc in self.stream_options:
            if desc == quality_str:
                selected_itag = itag
                break
        
        if not selected_itag:
            self.log(f"Error: Could not find the selected quality itag for '{quality_str}'.")
            return

        self.log(f"--- Starting playlist download: '{pl.title}' ---")
        total_videos = len(pl.videos)
        for i, video in enumerate(pl.videos):
            self.root.after(0, lambda: self.progress_bar.config(value=0)) # Reset for each video
            self.log(f"[{i+1}/{total_videos}] Downloading: '{video.title}'")
            try:
                video.register_on_progress_callback(self.on_progress)
                stream = video.streams.get_by_itag(selected_itag)
                if stream:
                    stream.download(output_path=path)
                    self.log(f"[{i+1}/{total_videos}] SUCCESS: Downloaded '{video.title}'.")
                else:
                    self.log(f"[{i+1}/{total_videos}] WARNING: Quality '{quality_str}' not found for this video. Falling back to highest resolution.")
                    video.streams.get_highest_resolution().download(output_path=path)
            except Exception as e:
                self.log(f"[{i+1}/{total_videos}] ERROR: Could not download '{video.title}'. Skipping.")
                self.log(f"--> Exception: {e}")
                continue
        
        self.log(f"--- Playlist download complete! ---")
        self.root.after(0, lambda: messagebox.showinfo("Success", f"Playlist '{pl.title}' downloaded successfully!"))

    def on_progress(self, stream, chunk, bytes_remaining):
        """Callback function to update the progress bar."""
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        self.root.after(0, lambda: self.progress_bar.config(value=percentage))

    def clear_fields(self):
        """Resets the quality menu and status."""
        self.quality_menu.set('')
        self.quality_menu.config(state="disabled")
        self.quality_menu['values'] = []
        self.download_button.config(state="disabled")
        self.progress_bar['value'] = 0

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()

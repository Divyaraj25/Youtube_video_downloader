import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pytubefix import YouTube, Playlist
import threading
import queue
import os
import re # For filename sanitization

class YouTubeDownloaderApp:
    """
    A desktop application for downloading YouTube videos, audio, and playlists.
    This version uses 'pytubefix' and includes a detailed logging area for status and errors.
    Improvements include better UI/UX, individual playlist video progress,
    and selection of specific videos from a playlist.
    """
    def __init__(self, root):
        """
        Initializes the main application window and its widgets.
        """
        self.root = root
        self.root.title("YouTube Downloader (pytubefix)")
        self.root.geometry("950x800") # Increased width and height for better layout
        self.root.resizable(True, True) # Changed to True, True to allow resizing
        self.root.configure(bg="#e0e0e0") # Lighter background

        # --- Style configuration ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", background="#e0e0e0", font=("Helvetica", 11))
        style.configure("TButton", font=("Helvetica", 11, "bold"), padding=8, background="#4CAF50", foreground="white")
        style.map("TButton", background=[('active', '#45a049')])
        style.configure("TRadiobutton", background="#e0e0e0", font=("Helvetica", 10))
        style.configure("TEntry", font=("Helvetica", 11), fieldbackground="#ffffff")
        style.configure("TCombobox", font=("Helvetica", 11), fieldbackground="#ffffff")
        style.configure("TFrame", background="#e0e0e0")
        style.configure("TLabelframe", background="#e0e0e0", borderwidth=2, relief="groove")
        style.configure("TLabelframe.Label", font=("Helvetica", 12, "bold"), foreground="#333333")

        # --- Main Frame ---
        main_frame = ttk.Frame(self.root, padding="15", style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1) # Allow column to expand
        main_frame.rowconfigure(1, weight=1) # Crucial: Allow log_frame (row=1) to expand vertically

        # --- Top controls frame ---
        controls_frame = ttk.Frame(main_frame, style="TFrame")
        controls_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        controls_frame.columnconfigure(0, weight=1)

        # --- Download Type Selection ---
        type_frame = ttk.LabelFrame(controls_frame, text="1. Choose Download Type", padding="10")
        type_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        type_frame.columnconfigure(0, weight=1) # Center radio buttons

        self.download_type = tk.StringVar(value="video")
        ttk.Radiobutton(type_frame, text="Single Video", variable=self.download_type, value="video", command=self.update_ui_for_type).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(type_frame, text="Audio Only", variable=self.download_type, value="audio", command=self.update_ui_for_type).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(type_frame, text="Playlist", variable=self.download_type, value="playlist", command=self.update_ui_for_type).pack(anchor=tk.W, pady=2)

        # --- URL Input ---
        url_frame = ttk.LabelFrame(controls_frame, text="2. Enter YouTube URL", padding="10")
        url_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)

        self.url_entry = ttk.Entry(url_frame)
        self.url_entry.grid(row=0, column=0, sticky="ew", ipady=5)
        self.url_entry.bind("<Return>", self.on_url_change) # Fetch on Enter key
        self.url_entry.bind("<FocusOut>", self.on_url_change) # Fetch on losing focus

        # --- Quality Selection ---
        self.quality_frame = ttk.LabelFrame(controls_frame, text="3. Select Quality", padding="10")
        self.quality_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.quality_frame.columnconfigure(0, weight=1)
        
        self.quality_var = tk.StringVar()
        self.quality_menu = ttk.Combobox(self.quality_frame, textvariable=self.quality_var, state="disabled")
        self.quality_menu.grid(row=0, column=0, sticky="ew", pady=5, ipady=3)

        # --- Playlist Video Selection (initially hidden) ---
        self.playlist_selection_frame = ttk.LabelFrame(controls_frame, text="4. Select Videos from Playlist", padding="10")
        self.playlist_selection_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self.playlist_selection_frame.columnconfigure(0, weight=1)
        self.playlist_selection_frame.rowconfigure(0, weight=1) # Allow listbox to expand vertically
        self.playlist_selection_frame.grid_remove() # Hide initially

        self.playlist_listbox = tk.Listbox(self.playlist_selection_frame, selectmode=tk.MULTIPLE, height=8, font=("Helvetica", 10), bd=1, relief="solid")
        self.playlist_listbox.grid(row=0, column=0, sticky="nsew")
        
        playlist_scrollbar = ttk.Scrollbar(self.playlist_selection_frame, orient="vertical", command=self.playlist_listbox.yview)
        playlist_scrollbar.grid(row=0, column=1, sticky="ns")
        self.playlist_listbox.config(yscrollcommand=playlist_scrollbar.set)

        # Select/Deselect All buttons
        playlist_buttons_frame = ttk.Frame(self.playlist_selection_frame)
        playlist_buttons_frame.grid(row=1, column=0, columnspan=2, pady=(5,0), sticky="ew")
        playlist_buttons_frame.columnconfigure(0, weight=1)
        playlist_buttons_frame.columnconfigure(1, weight=1)

        ttk.Button(playlist_buttons_frame, text="Select All", command=self.select_all_playlist_videos).grid(row=0, column=0, padx=5, sticky="ew")
        ttk.Button(playlist_buttons_frame, text="Deselect All", command=self.deselect_all_playlist_videos).grid(row=0, column=1, padx=5, sticky="ew")

        # --- Download Controls & Progress ---
        download_controls_frame = ttk.Frame(controls_frame, style="TFrame")
        # This row will be dynamically set based on download_type
        self.download_controls_row = 3 # Default row if playlist selection is hidden
        download_controls_frame.grid(row=self.download_controls_row, column=0, sticky="ew", pady=(0, 10))
        download_controls_frame.columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(download_controls_frame, orient="horizontal", length=100, mode="determinate")
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.download_button = ttk.Button(download_controls_frame, text="Download", command=self.start_download_thread, state="disabled")
        self.download_button.grid(row=0, column=1)

        # --- Log Area ---
        log_frame = ttk.LabelFrame(main_frame, text="Logs & Status", padding="10")
        log_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1) # Allow log text to expand

        self.log_text = scrolledtext.ScrolledText(log_frame, state='disabled', height=10, wrap=tk.WORD, font=("Consolas", 9), bg="#f8f8f8", fg="#333333")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        self.stream_options = []
        self.playlist_videos_info = [] # Stores (YouTube object, title) for playlist videos
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

        # Get the controls_frame to re-grid elements
        main_frame = self.root.nametowidget(self.root.winfo_children()[0])
        controls_frame = main_frame.winfo_children()[0]

        # Hide all elements that might change position
        self.quality_frame.grid_remove()
        self.playlist_selection_frame.grid_remove()
        
        # Determine new grid positions
        current_row = 2 # Starting row for quality_frame/playlist_selection_frame

        if download_type == "playlist":
            self.quality_frame.config(text="3. Select Quality (for all videos)")
            self.quality_frame.grid(row=current_row, column=0, sticky="ew", pady=(0, 10))
            current_row += 1
            self.playlist_selection_frame.grid(row=current_row, column=0, sticky="ew", pady=(0, 10))
            current_row += 1
        else:
            self.quality_frame.config(text="3. Select Quality")
            self.quality_frame.grid(row=current_row, column=0, sticky="ew", pady=(0, 10))
            current_row += 1
        
        # Position the download controls frame
        download_controls_frame = self.root.nametowidget(controls_frame.winfo_children()[-1]) # Assuming it's the last child
        download_controls_frame.grid(row=current_row, column=0, sticky="ew", pady=(0, 10))


    def on_url_change(self, event=None):
        """Handles the event when the URL entry changes."""
        url = self.url_entry.get().strip()
        if not url:
            self.clear_fields()
            self.log("URL field is empty. Please enter a YouTube URL.")
            return

        # Basic URL validation (can be more robust)
        if "youtube.com/watch?v=" not in url and "youtube.com/playlist?list=" not in url and "youtu.be/" not in url and "music.youtube.com/watch?v=" not in url:
            self.log("Invalid URL format. Please enter a valid YouTube video or playlist URL.")
            self.clear_fields()
            return

        self.log("URL detected. Starting to fetch details...")
        # Clear previous quality options and disable download button
        self.root.after(0, self.clear_fields)
        threading.Thread(target=self.fetch_stream_options, daemon=True).start()

    def fetch_stream_options(self):
        """Fetches available video/audio streams from the YouTube URL."""
        url = self.url_entry.get().strip()
        download_type = self.download_type.get()
        
        # Disable UI elements during fetch
        self.root.after(0, lambda: self.quality_menu.config(state="disabled"))
        self.root.after(0, lambda: self.download_button.config(state="disabled"))
        self.root.after(0, lambda: self.playlist_listbox.delete(0, tk.END)) # Clear playlist listbox

        try:
            self.log(f"Connecting to URL: {url}")
            if download_type in ["video", "audio"]:
                yt = YouTube(url, on_progress_callback=self.on_progress)
                self.log(f"Successfully connected. Video Title: '{yt.title}'")
                if download_type == "video":
                    self.log("Fetching available video streams (progressive MP4)...")
                    streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
                    # Add filesize_mb property to streams if not present (pytube sometimes misses it)
                    for s in streams:
                        if not hasattr(s, 'filesize_mb'):
                            s.filesize_mb = s.filesize / (1024 * 1024) if s.filesize else 0
                    self.stream_options = [(s, f"{s.resolution} - {s.filesize_mb:.2f} MB") for s in streams if s.resolution]
                else: # audio
                    self.log("Fetching available audio streams (MP4)...")
                    streams = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc()
                    for s in streams:
                        if not hasattr(s, 'filesize_mb'):
                            s.filesize_mb = s.filesize / (1024 * 1024) if s.filesize else 0
                    self.stream_options = [(s, f"{s.abr} - {s.filesize_mb:.2f} MB") for s in streams if s.abr]

            elif download_type == "playlist":
                pl = Playlist(url)
                self.log(f"Successfully connected. Playlist Title: '{pl.title}'")
                self.log(f"Found {len(pl.video_urls)} videos in the playlist. Fetching details...")
                
                if not pl.video_urls:
                    self.log("Error: This playlist is empty or private.")
                    self.root.after(0, self.clear_fields)
                    return

                # Fetch details for the first video to get quality options
                first_video_url = pl.video_urls[0]
                yt_first = YouTube(first_video_url)
                self.log(f"Fetching sample quality options from first video: '{yt_first.title}'")
                streams = yt_first.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
                self.stream_options = [(s.itag, f"{s.resolution} - {s.mime_type}") for s in streams if s.resolution]

                # Populate playlist_videos_info and listbox
                self.playlist_videos_info = []
                for i, video_url in enumerate(pl.video_urls):
                    try:
                        yt_video = YouTube(video_url)
                        self.playlist_videos_info.append((yt_video, yt_video.title))
                        self.root.after(0, lambda i_idx=i, title=yt_video.title: self.playlist_listbox.insert(tk.END, f"{i_idx+1}. {title}"))
                    except Exception as e:
                        self.log(f"WARNING: Could not fetch details for video {i+1} in playlist. Skipping. Error: {e}")
                        # Add a placeholder or indicate error in listbox if desired
                        self.root.after(0, lambda i_idx=i: self.playlist_listbox.insert(tk.END, f"{i_idx+1}. [Error fetching title]"))
                        continue
                self.log(f"Successfully fetched titles for {len(self.playlist_videos_info)} videos in the playlist.")


            if not self.stream_options:
                self.log("Error: No compatible streams were found for this URL. Please check if it's a valid video/audio/playlist URL.")
                self.root.after(0, self.clear_fields)
                return

            self.log(f"Found {len(self.stream_options)} quality options.")
            
            # Update UI from the main thread
            def update_ui():
                self.quality_menu['values'] = [opt[1] for opt in self.stream_options]
                if self.stream_options:
                    self.quality_menu.set(self.stream_options[0][1]) # Set default to highest quality
                    self.quality_menu.config(state="readonly")
                    self.download_button.config(state="normal")
                    self.log("Ready to download. Please select a quality and click 'Download'.")
                else:
                    self.quality_menu.config(state="disabled")
                    self.download_button.config(state="disabled")
                    self.log("No quality options available.")
            
            self.root.after(0, update_ui)

        except Exception as e:
            self.log(f"FATAL ERROR: Could not fetch details. Please check the URL and your internet connection.")
            self.log(f"--> Exception: {str(e)}")
            self.root.after(0, self.clear_fields)

    def select_all_playlist_videos(self):
        """Selects all videos in the playlist listbox."""
        self.log("Selecting all videos in the playlist.")
        self.playlist_listbox.selection_set(0, tk.END)

    def deselect_all_playlist_videos(self):
        """Deselects all videos in the playlist listbox."""
        self.log("Deselecting all videos in the playlist.")
        self.playlist_listbox.selection_clear(0, tk.END)

    def start_download_thread(self):
        """Starts the download process in a new thread to keep the UI responsive."""
        self.download_button.config(state="disabled")
        self.progress_bar['value'] = 0
        self.log("Download button clicked. Starting download process...")
        threading.Thread(target=self.download, daemon=True).start()

    def download(self):
        """Handles the actual download logic."""
        url = self.url_entry.get().strip()
        download_type = self.download_type.get()
        selected_quality_str = self.quality_var.get()

        if not selected_quality_str and download_type != "playlist": # Playlist handles quality selection differently
            self.log("Error: Please select a quality option before downloading.")
            self.root.after(0, lambda: self.download_button.config(state="normal"))
            return

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
                selected_indices = self.playlist_listbox.curselection()
                if not selected_indices:
                    self.log("Error: No videos selected for playlist download.")
                    self.root.after(0, lambda: self.download_button.config(state="normal"))
                    messagebox.showwarning("No Selection", "Please select at least one video from the playlist to download.")
                    return
                # Get the actual YouTube objects for selected videos
                selected_yt_videos = [self.playlist_videos_info[i][0] for i in selected_indices]
                self.download_playlist(selected_yt_videos, selected_quality_str, save_path)
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
        path_queue = queue.Queue()
        self.root.after(0, lambda: path_queue.put(filedialog.askdirectory()))
        return path_queue.get()

    def sanitize_filename(self, title):
        """Sanitizes a string to be used as a filename."""
        # Remove invalid characters
        s = re.sub(r'[\\/:*?"<>|]', '', title)
        # Replace multiple spaces/underscores with a single underscore
        s = re.sub(r'\s+', '_', s)
        s = re.sub(r'_+', '_', s)
        # Remove leading/trailing underscores
        s = s.strip('_')
        # Limit length to avoid very long filenames
        s = s[:100] 
        return s

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
            self.root.after(0, lambda: messagebox.showerror("Download Error", f"Could not find the selected quality: {quality_str}"))
            return

        file_extension = "mp4" if self.download_type.get() == "video" else "mp3"
        quality_info = selected_stream.resolution if self.download_type.get() == "video" else selected_stream.abr
        
        # Ensure quality_info is a string, handle None or missing attributes
        quality_info_str = str(quality_info) if quality_info else "unknown_quality"

        sanitized_title = self.sanitize_filename(yt.title)
        filename = f"1-{sanitized_title}-{quality_info_str}.{file_extension}"

        self.log(f"Starting download for: '{yt.title}' at {quality_info_str} as '{filename}'")
        try:
            selected_stream.download(output_path=path, filename=filename)
            self.log(f"SUCCESS: Download complete for '{yt.title}'. Saved as '{filename}'.")
            self.root.after(0, lambda: messagebox.showinfo("Success", f"'{yt.title}' has been downloaded successfully!"))
        except Exception as e:
            self.log(f"ERROR: Failed to download '{yt.title}'. Exception: {e}")
            self.root.after(0, lambda: messagebox.showerror("Download Error", f"Failed to download '{yt.title}': {str(e)}"))


    def download_playlist(self, selected_yt_videos, quality_str, path):
        """Downloads an entire playlist."""
        selected_itag = None
        for itag, desc in self.stream_options:
            if desc == quality_str:
                selected_itag = itag
                break
        
        if not selected_itag:
            self.log(f"Error: Could not find the selected quality itag for '{quality_str}'.")
            self.root.after(0, lambda: messagebox.showerror("Download Error", f"Could not find the selected quality: {quality_str}"))
            return

        self.log(f"--- Starting playlist download for {len(selected_yt_videos)} selected videos ---")
        total_videos = len(selected_yt_videos)
        
        for i, video_yt_obj in enumerate(selected_yt_videos):
            self.root.after(0, lambda: self.progress_bar.config(value=0)) # Reset for each video
            
            file_extension = "mp4" # Assuming video for playlist
            quality_info = quality_str.split(' ')[0] # e.g., "720p" from "720p - video/mp4"
            sanitized_title = self.sanitize_filename(video_yt_obj.title)
            filename = f"{i+1}-{sanitized_title}-{quality_info}.{file_extension}"

            self.log(f"[{i+1}/{total_videos}] Downloading: '{video_yt_obj.title}' at {quality_info} as '{filename}'")
            try:
                video_yt_obj.register_on_progress_callback(self.on_progress)
                stream = video_yt_obj.streams.get_by_itag(selected_itag)
                
                if stream:
                    stream.download(output_path=path, filename=filename)
                    self.log(f"[{i+1}/{total_videos}] SUCCESS: Downloaded '{video_yt_obj.title}'. Saved as '{filename}'.")
                else:
                    self.log(f"[{i+1}/{total_videos}] WARNING: Quality '{quality_str}' not found for '{video_yt_obj.title}'. Falling back to highest progressive resolution.")
                    highest_res_stream = video_yt_obj.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                    if highest_res_stream:
                        fallback_quality_info = highest_res_stream.resolution
                        fallback_filename = f"{i+1}-{sanitized_title}-{fallback_quality_info}.{file_extension}"
                        self.log(f"[{i+1}/{total_videos}] Falling back to '{fallback_quality_info}' for '{video_yt_obj.title}'.")
                        highest_res_stream.download(output_path=path, filename=fallback_filename)
                        self.log(f"[{i+1}/{total_videos}] SUCCESS (Fallback): Downloaded '{video_yt_obj.title}'. Saved as '{fallback_filename}'.")
                    else:
                        self.log(f"[{i+1}/{total_videos}] ERROR: No progressive MP4 stream found for '{video_yt_obj.title}'. Skipping.")
                        
            except Exception as e:
                self.log(f"[{i+1}/{total_videos}] ERROR: Could not download '{video_yt_obj.title}'. Skipping.")
                self.log(f"--> Exception: {e}")
                continue
        
        self.log(f"--- Playlist download complete! ---")
        self.root.after(0, lambda: messagebox.showinfo("Success", f"Selected videos from playlist downloaded successfully!"))

    def on_progress(self, stream, chunk, bytes_remaining):
        """Callback function to update the progress bar."""
        total_size = stream.filesize
        if total_size == 0: # Avoid division by zero if filesize is not determined yet
            percentage = 0
        else:
            bytes_downloaded = total_size - bytes_remaining
            percentage = (bytes_downloaded / total_size) * 100
        
        # Ensure progress bar update is on the main thread
        self.root.after(0, lambda: self.progress_bar.config(value=percentage))

    def clear_fields(self):
        """Resets the quality menu, playlist listbox, and status."""
        self.quality_menu.set('')
        self.quality_menu.config(state="disabled")
        self.quality_menu['values'] = []
        self.playlist_listbox.delete(0, tk.END)
        self.download_button.config(state="disabled")
        self.progress_bar['value'] = 0
        self.stream_options = []
        self.playlist_videos_info = []

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()

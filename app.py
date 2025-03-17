import os
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog, Toplevel
from tkinter.ttk import Progressbar, Treeview
from PIL import Image, ImageTk
import yt_dlp
from io import BytesIO
import requests
from datetime import datetime
import json
import pystray
from pystray import MenuItem as item

API_KEY = "AIzaSyBHbCmXunkvJGHnaHSvjCwyDv6HQxB3PVg"
HISTORY_FILE = "download_history.json"


class ClipTubeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ClipTube")
        self.root.geometry("900x500")
        self.root.configure(bg="#f0f0f0")

        # Set font to Comic Sans
        self.default_font = ("Comic Sans MS", 12)

        # Title Label
        self.title_label = tk.Label(root, text="ClipTube", font=("Comic Sans MS", 24, "bold"), bg="#f0f0f0")
        self.title_label.pack(pady=10)

        # Menu
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)

        # File Menu
        self.file_menu = tk.Menu(self.menu, tearoff=0)
        self.file_menu.add_command(label="Exit", command=root.quit)
        self.menu.add_cascade(label="File", menu=self.file_menu)

        # Help Menu
        self.help_menu = tk.Menu(self.menu, tearoff=0)
        self.help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "ClipTube Downloader"))
        self.menu.add_cascade(label="Help", menu=self.help_menu)

        # History Menu
        self.menu.add_command(label="History", command=self.show_history)

        # URL Entry Section
        self.url_label = tk.Label(root, text="YouTube Video URL:", font=self.default_font, bg="#f0f0f0")
        self.url_label.pack(pady=10)

        self.url_entry = tk.Entry(root, width=50, font=self.default_font)
        self.url_entry.pack(pady=5)

        self.fetch_button = tk.Button(root, text="Fetch", command=self.fetch_video_details, font=self.default_font,
                                       bg="#007bff", fg="white")
        self.fetch_button.pack(pady=10)

        # Video Details Section
        self.thumbnail_label = tk.Label(root, bg="#f0f0f0")
        self.thumbnail_label.pack(pady=10)

        self.details_label = tk.Label(root, text="", font=self.default_font, bg="#f0f0f0", justify=tk.LEFT)
        self.details_label.pack(pady=5)

        # Destination Folder Section
        self.folder_label = tk.Label(root, text="Save To:", font=self.default_font, bg="#f0f0f0")
        self.folder_label.pack(pady=10)

        self.folder_path = tk.StringVar()
        folder_frame = tk.Frame(root, bg="#f0f0f0")
        folder_frame.pack(pady=5)

        self.folder_entry = tk.Entry(folder_frame, textvariable=self.folder_path, width=50, font=self.default_font)
        self.folder_entry.pack(side=tk.LEFT, padx=(10, 5))

        self.browse_button = tk.Button(folder_frame, text="Browse", command=self.browse_folder, font=self.default_font,
                                       bg="#007bff", fg="white")
        self.browse_button.pack(side=tk.LEFT)

        # Download Button
        self.download_button = tk.Button(root, text="Download", command=self.start_download_thread, font=self.default_font,
                                          bg="green", fg="white")
        self.download_button.pack(pady=20)

        # Progress Bar
        self.progress_bar = Progressbar(root, orient="horizontal", mode="determinate", length=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.pack_forget()

        # Status Label
        self.status_label = tk.Label(root, text="", font=self.default_font, fg="blue", bg="#f0f0f0")
        self.status_label.pack(pady=10)

        # Load History
        self.history = self.load_history()

        # Set Taskbar Icon
        self.set_taskbar_icon()

    def set_taskbar_icon(self):
        # Load the icon image
        icon_image = Image.open(r"F:\Coding\Projects\Complete\ClipTube\Logo.png")
        icon_image = icon_image.resize((64, 64))  # Resize to appropriate size
        icon = pystray.Icon("ClipTube", icon_image, "ClipTube")
        
        # Define menu for the tray icon
        icon.menu = pystray.Menu(item("Exit", self.exit_app))
        
        # Run the icon in a separate thread to avoid blocking the tkinter loop
        threading.Thread(target=icon.run, daemon=True).start()

    def exit_app(self, icon, item):
        self.root.quit()
        icon.stop()

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)

    def fetch_video_details(self):
        """Fetch video details using YouTube Data API."""
        url = self.url_entry.get()
        if not url.strip():
            messagebox.showerror("Error", "Please enter a YouTube video URL.")
            return

        video_id = self.extract_video_id(url)
        if not video_id:
            messagebox.showerror("Error", "Invalid YouTube URL.")
            return

        # YouTube Data API call
        api_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={API_KEY}"

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()

            if "items" in data and len(data["items"]) > 0:
                snippet = data["items"][0]["snippet"]
                title = snippet.get("title", "Unknown Title")
                author = snippet.get("channelTitle", "Unknown Author")
                thumbnail_url = snippet["thumbnails"]["high"]["url"]

                # Display the fetched details
                self.details_label.config(text=f"Title: {title}\nAuthor: {author}")
                self.display_thumbnail(thumbnail_url)
            else:
                messagebox.showerror("Error", "Video details not found. Please check the URL.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while fetching video details: {e}")

    def extract_video_id(self, url):
        """Extract video ID from YouTube URL."""
        if "v=" in url:
            return url.split("v=")[-1].split("&")[0]
        return None

    def display_thumbnail(self, thumbnail_url):
        """Display the video thumbnail."""
        try:
            response = requests.get(thumbnail_url)
            response.raise_for_status()
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            img = img.resize((200, 80), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.thumbnail_label.config(image=photo)
            self.thumbnail_label.image = photo
        except Exception as e:
            messagebox.showerror("Error", f"Unable to load thumbnail: {e}")

    def start_download_thread(self):
        threading.Thread(target=self.download_video, daemon=True).start()

    def download_video(self):
        url = self.url_entry.get()
        folder = self.folder_path.get()

        if not url.strip():
            messagebox.showerror("Error", "Please enter a YouTube video URL.")
            return
        if not folder.strip():
            messagebox.showerror("Error", "Please select a folder to save the video.")
            return

        self.status_label.config(text="Downloading...")
        self.progress_bar.pack()
        self.progress_bar["value"] = 0

        start_time = datetime.now()

        try:
            ydl_opts = {
                'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
                'format': 'best',
                'progress_hooks': [self.update_progress_bar]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            size = info.get('filesize', 0)
            end_time = datetime.now()
            time_taken = str(end_time - start_time)

            # Save to history
            self.history.append({
                "title": info.get('title', 'Unknown'),
                "author": info.get('uploader', 'Unknown'),
                "thumbnail": info.get('thumbnail', ''),
                "date": end_time.strftime('%Y-%m-%d %H:%M:%S'),
                "size": f"{size / 1024 / 1024:.2f} MB",
                "time_taken": time_taken
            })
            self.save_history()

            self.status_label.config(text="Download Complete!")
        except Exception as e:
            self.status_label.config(text="Downloaded!")
        finally:
            self.progress_bar.pack_forget()

    def update_progress_bar(self, d):
        """Update progress bar based on download progress."""
        if d['status'] == 'downloading':
            # Get the downloaded and total bytes
            downloaded = d.get('downloaded_bytes', None)
            total = d.get('total_bytes', None)

            # If either value is None, set progress to 0 and exit
            if downloaded is None or total is None:
                self.progress_bar['value'] = 0
                self.status_label.config(text="Error: Progress data unavailable.")
                return

            # If total is 0, avoid division by zero
            if total == 0:
                self.progress_bar['value'] = 100  # Set to 100% as a fallback
                self.status_label.config(text="Error: Total size is 0.")
                return

            # Calculate progress if data is valid
            percent = (downloaded / total) * 100
            self.progress_bar['value'] = percent
            self.status_label.config(text=f"Downloading... {percent:.2f}%")

            self.root.update_idletasks()

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        return []

    def save_to_history(title, author, date, size, time_taken):
        history_file = "download_history.json"
        history_data = []
        
        if os.path.exists(history_file):
            with open(history_file, "r") as file:
                try:
                    history_data = json.load(file)
                except json.JSONDecodeError:
                    history_data = []
        
        history_data.append({
            "title": title,
            "author": author,
            "date": date,
            "size": size,
            "time_taken": time_taken
        })
        
        with open(history_file, "w") as file:
            json.dump(history_data, file, indent=4)

    def show_history(self, event=None):
        history_file = "download_history.json"
        
        if not os.path.exists(history_file):
            messagebox.showinfo("History", "No download history found.")
            return
        
        with open(history_file, "r") as file:
            try:
                history_data = json.load(file)
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Failed to read history data.")
                return
        
        if not history_data:
            messagebox.showinfo("History", "No downloads recorded yet.")
            return
        
        history_window = tk.Toplevel()
        history_window.title("Download History")
        history_window.geometry("800x600")
        
        tree = ttk.Treeview(history_window, columns=("Title", "Author", "Date", "Size", "Time Taken"), show="headings")
        tree.heading("Title", text="Title")
        tree.heading("Author", text="Author")
        tree.heading("Date", text="Date & Time")
        tree.heading("Size", text="Size")
        tree.heading("Time Taken", text="Time Taken")
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        for entry in history_data:
            tree.insert("", tk.END, values=(entry["title"], entry["author"], entry["date"], entry["size"], entry["time_taken"]))
        
        history_window.mainloop()

    def open_history_record(self, event):
        selected_item = event.widget.selection()
        if selected_item:
            record = event.widget.item(selected_item[0])
            title = record["values"][0]
            author = record["values"][1]
            date = record["values"][2]
            size = record["values"][3]
            time_taken = record["values"][4]

            messagebox.showinfo("History Record", f"Title: {title}\nAuthor: {author}\nDate: {date}\nSize: {size}\nTime Taken: {time_taken}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ClipTubeApp(root)
    root.mainloop()

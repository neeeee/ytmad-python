import sys
import io
from yt_dlp import YoutubeDL
import tkinter as tk
from tkinter import filedialog, scrolledtext
import threading
import queue


class QueueWriter(io.TextIOBase):
    def __init__(self, log_queue: queue.Queue):
        self.queue = log_queue
        self.buffer_str = ""

    def write(self, msg):
        self.buffer_str += msg
        while "\n" in self.buffer_str:
            line, self.buffer_str = self.buffer_str.split("\n", 1)
            stripped = line.strip()
            if stripped:
                self.queue.put(stripped)

        while "\r" in self.buffer_str:
            line, self.buffer_str = self.buffer_str.split("\r", 1)
            stripped = line.strip()
            if stripped:
                self.queue.put(stripped)
        return len(msg)

    def flush(self):
        if self.buffer_str.strip():
            self.queue.put(self.buffer_str.strip())
            self.buffer_str = ""


def get_ydl_opts(folder):
    return {
        'no_color': True,
        'final_ext': 'm4a',
        'format': 'ba',
        'outtmpl': {
            'default': (
                f"{folder}/%(album_artist,artist,channel)s/"
                "%(album,playlist)s/"
                "%(track_number,playlist_index|00)s "
                "%(title)s.%(ext)s"
            ),
            'pl_thumbnail': ''
        },
        'overwrites': False,
        'postprocessors': [{
            'format': 'jpg',
            'key': 'FFmpegThumbnailsConvertor',
            'when': 'before_dl'
        },
            {
            'key': 'FFmpegExtractAudio',
            'nopostoverwrites': False,
            'preferredcodec': 'm4a',
            'preferredquality': '5'},
            {
            'add_chapters': True,
            'add_infojson': 'if_exists',
            'add_metadata': True,
            'key': 'FFmpegMetadata'
        },
            {
            'already_have_thumbnail': False,
            'key': 'EmbedThumbnail'
        }],
        'writethumbnail': True
    }


log_queue = queue.Queue()


def poll_log():
    while not log_queue.empty():
        msg = log_queue.get_nowait()
        log_box.config(state=tk.NORMAL)
        log_box.insert(tk.END, msg + "\n")
        log_box.see(tk.END)
        log_box.config(state=tk.DISABLED)
    root.after(100, poll_log)


def download_thread(folder, urls):
    writer = QueueWriter(log_queue)
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = writer
    sys.stderr = writer
    try:
        opts = get_ydl_opts(folder)
        with YoutubeDL(opts) as ydl:
            ydl.download(urls)
    finally:
        writer.flush()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    log_queue.put("--- Done! ---")
    download_btn.config(state=tk.NORMAL)


def download():
    folder = folder_var.get()
    if not folder:
        status.config(text="Please select a folder first.")
        return
    urls = text_box.get("1.0", tk.END).strip().splitlines()
    if not urls:
        status.config(text="No URLs entered.")
        return
    status.config(text="Downloading...")
    download_btn.config(state=tk.DISABLED)
    thread = threading.Thread(
        target=download_thread, args=(folder, urls), daemon=True
    )
    thread.start()


root = tk.Tk()
root.title("ytmad python")
folder_var = tk.StringVar()

tk.Button(
    root,
    text="Select Folder",
    command=lambda: folder_var.set(filedialog.askdirectory())
).pack()

tk.Label(root, textvariable=folder_var).pack()

tk.Label(root, text="Paste playlist URLs (one per line):").pack()
text_box = scrolledtext.ScrolledText(root, height=10, width=60)
text_box.pack()

download_btn = tk.Button(
    root,
    text="Download",
    command=download
)
download_btn.pack()

status = tk.Label(root, text="")
status.pack()

tk.Label(root, text="Log:").pack()

log_box = scrolledtext.ScrolledText(
    root, height=15, width=60, state=tk.DISABLED
)
log_box.pack()

root.after(100, poll_log)
root.mainloop()

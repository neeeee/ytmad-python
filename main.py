from yt_dlp import YoutubeDL
import tkinter as tk
from tkinter import filedialog, scrolledtext

def get_ydl_opts(folder: str) -> dict:
    return {
    'final_ext': 'm4a',
    'format': 'ba',
    'outtmpl': {
            'default': f"{folder}/%(album)s/%(track_number,playlist_index)s "
                            "%(title)s.%(ext)s",
                'pl_thumbnail': ''
        },
    'overwrites': False,
    'postprocessors': [{'format': 'jpg',
                        'key': 'FFmpegThumbnailsConvertor',
                        'when': 'before_dl'},
                        {'key': 'FFmpegExtractAudio',
                        'nopostoverwrites': False,
                        'preferredcodec': 'm4a',
                        'preferredquality': '5'},
                        {'add_chapters': True,
                        'add_infojson': 'if_exists',
                        'add_metadata': True,
                        'key': 'FFmpegMetadata'},
                        {'already_have_thumbnail': False, 'key': 'EmbedThumbnail'}],
    'writethumbnail': True
    }

def download() -> None:
    folder: str = folder_var.get()
    if not folder:
        status.config(text="Please select a folder first.")
        return
    urls = text_box.get("1.0", tk.END).strip().splitlines()
    if not urls:
        status.config(text="No URLs entered.")
        return
    status.config(text="Downloading...")
    root.update()
    with YoutubeDL(get_ydl_opts(folder)) as ydl:
        ydl.download(urls)

    status.config(text="Done!")

root = tk.Tk()
root.title("ytmad python")
folder_var = tk.StringVar()

tk.Button(root, text="Select Folder",
          command = lambda: folder_var.set(filedialog.askdirectory())
          ).pack()
tk.Label(root, textvariable=folder_var).pack()

tk.Label(root, text="Paste playlist URLs (one per line):").pack()
text_box = scrolledtext.ScrolledText(root, height=10, width=60)
text_box.pack()

tk.Button(root, text="Download", command=download).pack()
status = tk.Label(root, text="")
status.pack()

root.mainloop()

#!/usr/bin/python3

import sys
import io
import os
import tempfile
import argparse
from yt_dlp import YoutubeDL
from yt_dlp.postprocessor.metadataparser import MetadataParserPP
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
        'cookiesfrombrowser': ('chromium', None, None, None),
        'final_ext': 'm4a',
        'format': 'ba',
        'outtmpl': {
            'default': (
                f"{folder}/%(artist,album_artist,channel,uploader)s/"
                "%(album,playlist|Various)s/"
                "%(track_number,playlist_index|01)s "
                "%(track,title)s.%(ext)s"
            ),
            'pl_thumbnail': ''
        },
        'overwrites': False,
        'postprocessors': [
            {
                "key": "MetadataParser",
                "when": "pre_process",
                "actions": [
                    (MetadataParserPP.Actions.REPLACE,
                     "artist", r"\s*[,，&].*$", ""),
                    (MetadataParserPP.Actions.REPLACE,
                     "artist", r"\s*feat\..*$", ""),
                    (MetadataParserPP.Actions.REPLACE,
                     "artist", r"\s*ft\..*$", ""),
                    (MetadataParserPP.Actions.REPLACE,
                     "album_artist", r"\s*[,，&].*$", ""),
                    (MetadataParserPP.Actions.REPLACE,
                     "album_artist", r"\s*feat\..*$", ""),
                    (MetadataParserPP.Actions.REPLACE,
                     "album_artist", r"\s*ft\..*$", ""),
                    (MetadataParserPP.Actions.REPLACE,
                     "channel", r"\s*[,，&].*$", ""),
                    (MetadataParserPP.Actions.REPLACE,
                     "uploader", r"\s*[,，&].*$", ""),
                ],
            },
            {
                'format': 'jpg',
                'key': 'FFmpegThumbnailsConvertor',
                'when': 'before_dl'
            },
            {
                'key': 'FFmpegExtractAudio',
                'nopostoverwrites': False,
                'preferredcodec': 'm4a',
                'preferredquality': '5'
            },
            {
                'add_chapters': True,
                'add_infojson': 'if_exists',
                'add_metadata': True,
                'key': 'FFmpegMetadata'
            },
            {
                'already_have_thumbnail': False,
                'key': 'EmbedThumbnail'
            }
        ],
        'writethumbnail': True
    }


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ytmad python")
        self.log_queue: queue.Queue = queue.Queue()
        self.folder_var = tk.StringVar()
        self._build_ui()
        self.after(100, self._poll_log)

    def _build_ui(self):
        tk.Button(
            self,
            text="Select Folder",
            command=self._select_folder
        ).pack(pady=(8, 0))

        tk.Label(self, textvariable=self.folder_var).pack()

        tk.Label(self, text="Paste playlist URLs (one per line):").pack()

        self.text_box = scrolledtext.ScrolledText(self, height=10, width=60)
        self.text_box.pack()

        self.download_btn = tk.Button(
            self,
            text="Download",
            command=self._start_download
        )
        self.download_btn.pack(pady=(4, 0))

        self.clear_urls_btn = tk.Button(
            self,
            text="Clear",
            command=self._clear_urls
        )
        self.clear_urls_btn.pack(pady=(4, 0))

        self.status = tk.Label(self, text="")
        self.status.pack()

        tk.Label(self, text="Log:").pack()

        self.log_box = scrolledtext.ScrolledText(
            self, height=15, width=60, state=tk.DISABLED
        )
        self.log_box.pack(pady=(0, 8))

    def _select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)

    def _clear_urls(self):
        self.text_box.delete("1.0", tk.END)

    def _start_download(self):
        folder = self.folder_var.get()
        if not folder:
            self.status.config(text="Please select a folder first.")
            return

        urls = self.text_box.get("1.0", tk.END).strip().splitlines()
        if not urls:
            self.status.config(text="No URLs entered.")
            return

        self.status.config(text="Downloading...")
        self.download_btn.config(state=tk.DISABLED)

        thread = threading.Thread(
            target=self._download_thread,
            args=(folder, urls),
            daemon=True
        )
        thread.start()

    def _download_thread(self, folder: str, urls: list[str]):
        writer = QueueWriter(self.log_queue)
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

        self.log_queue.put("--- Done! ---")
        self.download_btn.config(state=tk.NORMAL)

    def _poll_log(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get_nowait()
            self.log_box.config(state=tk.NORMAL)
            self.log_box.insert(tk.END, msg + "\n")
            self.log_box.see(tk.END)
            self.log_box.config(state=tk.DISABLED)
        self.after(100, self._poll_log)


def download_cli_only(folder: str):
    if not folder:
        print("Please enter an output directory with --dir=DIR")
        return

    try:
        with open('urls.txt', 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\n') for line in f]
    except FileNotFoundError:
        print("urls.txt not found.")
        return

    remaining = []
    for raw in lines:
        url = raw.strip()
        if not url:
            continue
        opts = get_ydl_opts(folder)
        try:
            with YoutubeDL(opts) as ydl:
                ydl.download([url])
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            remaining.append(raw)

    dir_name = os.path.dirname(os.path.abspath('urls.txt')) or '.'
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, text=True)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as tmpf:
            if remaining:
                tmpf.write("\n".join(remaining))
                tmpf.write("\n")
        os.replace(tmp_path, 'urls.txt')
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    print("Done.")


def parse_arguments():
    parser = argparse.ArgumentParser(prog="ytmad-python")
    parser.add_argument('--cli', help='run cli only', action='store_true')
    parser.add_argument('--dir', type=str, default='./')
    args = parser.parse_args()
    return args.cli, args.dir


if __name__ == "__main__":
    cli, output_dir = parse_arguments()
    if cli:
        download_cli_only(output_dir)
    else:
        App().mainloop()

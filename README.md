Python Dependencies:
yt-dlp
tkinter

Usage:
1. Install dependencies
2. Run `main.py`
3. Select directory to save music folder downloads in
4. Paste youtube music links of individual tracks, albums, or playlists on separate lines
5. Click Download

Features:
> album art is embedded in m4a files
> metadata is decent for a music player (fix it manually after download for accuracy)
> albums with multiple contributing artists will be downloaded to the primary artist's directory

It reads cookies from chromium by default. Change this if you:
1. Use a different browser for youtube
2. Don't want to use a login cookie for youtube

If you have issues with downloads, check the yt-dlp parameters in `get_ydl_opts(folder)`

```python
def get_ydl_opts(folder):
    return {
        'no_color': True,
        'cookiesfrombrowser': ('chromium', None, None, None),
        'final_ext': 'm4a',
        'format': 'ba',
        'outtmpl': {
            'default': (
                f"{folder}/%(artist,channel)s/"
                "%(album,playlist|Various)s/"
                "%(track_number,playlist_index|00)s "
                "%(track)s.%(ext)s"
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
```


Do whatever you want with the code.

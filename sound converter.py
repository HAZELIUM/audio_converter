# ==================================================== IMPORTS AND INFO

from pathlib import Path
from pydub import AudioSegment
import yt_dlp
import customtkinter as ctk
import tkinter as tk
import threading
import shutil
import sys
from tkinter import filedialog

# Resolves to the folder containing the .exe when frozen, or the script folder otherwise
BASE_DIR = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent

# V2
# Audio Converter Application using CustomTkinter and Pydub
# The desired format will be selected.
# If user wants to convert multiple files, the program will automatically scan ALL audio files it can detect inside the "input" folder.
# The conversion process will begin.
# The converted files will be saved into a folder named "output" in the following format: <file_name>_converted.<selected_format>
# With yt-dlp integration, the program will allow users to input a YouTube video URL.
# The program will download the audio from the video and save it in the "input" folder.
# The user can then select the desired output format and convert the downloaded audio file.
# Operations performed through yt_dlp will be carried out in a folder named "operations".

# ==================================================== LISTS

formats = ["mp3", "wav", "ogg", "flac", "aac", "wma", "opus", "aiff", "webm"]
files_to_convert = []

# ==================================================== FUNCTIONS

def select_file():
    file = filedialog.askopenfilename(title="Select an audio file", filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac *.aac *.wma *.opus *.aiff *.webm")])
    if file:
        app.after(0, lambda: status_label_var.set(f"Selected file: {Path(file).name}"))
        files_to_convert.clear()
        files_to_convert.append(Path(file))

def multi_selection_changed(choice):
    if choice == "Single File":
        button_file.configure(state="normal")
    else:
        button_file.configure(state="disabled")

def scan_input_folder():
    files_to_convert.clear()
    input_folder = BASE_DIR / "input"
    if not input_folder.exists():
        app.after(0, lambda: status_label_var.set("Input folder not found. Please create an 'input' folder and add audio files to convert."))
        return
    try:
        for file in input_folder.iterdir():
            if file.is_file() and file.suffix[1:].lower() in formats:
                files_to_convert.append(file)
    except PermissionError:
        app.after(0, lambda: status_label_var.set("Permission denied when accessing the 'input' folder."))

def create_output_folder():
    output_folder = BASE_DIR / "output"
    output_folder.mkdir(exist_ok=True)
    return output_folder

def convert_audio():
    button_convert.configure(state="disabled")
    progress_bar.set(0)
    progress_label_var.set("0%")
    threading.Thread(target=convert_audio_thread, daemon=True).start()

def convert_audio_thread():
    if combobox_multi.get() == "Multiple Files":
        scan_input_folder()
    if not files_to_convert:
        if combobox_multi.get() == "Single File":
            app.after(0, lambda: status_label_var.set("No audio file selected. Please select a file to convert."))
        else:
            app.after(0, lambda: status_label_var.set("No audio files found in the 'input' folder."))
        app.after(0, lambda: button_convert.configure(state="normal"))
        return
    files = list(files_to_convert)  # snapshot — prevents race condition with select_file
    app.after(0, lambda: button_file.configure(state="disabled"))
    selected_format = combobox_formats.get()
    total = len(files)
    for index, file in enumerate(files):
        try:
            output_folder = create_output_folder()
            output_file = output_folder / f"{file.stem}_converted.{selected_format}"
            if output_file.exists():
                app.after(0, lambda n=file.name: status_label_var.set(f"Skipping {n} (already converted)."))
                app.after(0, lambda n=output_file.name: history_label_var.set(f"Skipped: {n}"))
                progress = (index + 1) / total
                app.after(0, lambda p=progress: progress_bar.set(p))
                app.after(0, lambda p=progress: progress_label_var.set(f"{int(p * 100)}%"))
                continue
            app.after(0, lambda n=file.name: status_label_var.set(f"Converting {n}..."))
            audio = AudioSegment.from_file(file)
            audio.export(output_file, format=selected_format)
            progress = (index + 1) / total
            app.after(0, lambda p=progress: progress_bar.set(p))
            app.after(0, lambda p=progress: progress_label_var.set(f"{int(p * 100)}%"))
            app.after(0, lambda n=output_file.name: history_label_var.set(f"Converted: {n}"))
        except Exception as e:
            app.after(0, lambda n=file.name, err=e: status_label_var.set(f"Error converting {n}: {err}"))
    app.after(0, lambda: status_label_var.set("Conversion process completed."))
    app.after(0, lambda: progress_label_var.set("100%"))
    app.after(0, lambda: button_convert.configure(state="normal"))
    app.after(0, lambda: multi_selection_changed(combobox_multi.get()))
    files_to_convert.clear()

def yt_progress_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)
        if total:
            progress = min(downloaded / total, 1.0)
            app.after(0, lambda p=progress: progress_bar_yt.set(p))
            app.after(0, lambda p=progress: yt_progress_label_var.set(f"{int(p * 100)}%"))
        speed = d.get('speed')
        if speed:
            speed_str = f"{speed / 1024 / 1024:.1f} MB/s" if speed > 1024 * 1024 else f"{speed / 1024:.1f} KB/s"
            app.after(0, lambda s=speed_str: yt_status_label_var.set(f"Downloading... {s}"))
    elif d['status'] == 'finished':
        app.after(0, lambda: progress_bar_yt.set(1))
        app.after(0, lambda: yt_progress_label_var.set("100%"))
        app.after(0, lambda: yt_status_label_var.set("Download finished. Converting..."))

def yt_convert():
    url = link.get().strip()
    if not url:
        yt_status_label_var.set("Please enter a YouTube video URL.")
        return
    selected_format = yt_combobox_formats.get()
    button_yt_convert.configure(state="disabled")
    progress_bar_yt.set(0)
    yt_progress_label_var.set("0%")
    yt_status_label_var.set("Connecting to YouTube...")
    threading.Thread(target=yt_convert_thread, args=(url, selected_format), daemon=True).start()

def yt_convert_thread(url, selected_format):
    operations_folder = BASE_DIR / "operations"
    operations_folder.mkdir(exist_ok=True)
    output_template = str(operations_folder / "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": selected_format,
            "preferredquality": "192"
        }],
        "progress_hooks": [yt_progress_hook],
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        app.after(0, lambda: yt_status_label_var.set("Moving file to 'output' folder..."))
        output_folder = BASE_DIR / "output"
        output_folder.mkdir(exist_ok=True)
        moved = False
        for file in operations_folder.iterdir():
            if file.is_file() and file.suffix[1:].lower() == selected_format:
                destination = output_folder / file.name
                if destination.exists():
                    destination.unlink()
                shutil.move(str(file), str(destination))
                app.after(0, lambda n=file.name: yt_history_label_var.set(f"Downloaded: {n}"))
                app.after(0, lambda: yt_status_label_var.set("File saved to 'output' folder."))
                moved = True
                break
        if not moved:
            app.after(0, lambda: yt_status_label_var.set("Download complete, but output file could not be located."))
    except Exception as e:
        app.after(0, lambda err=e: yt_status_label_var.set(f"Error: {err}"))
    finally:
        if operations_folder.exists():
            shutil.rmtree(operations_folder, ignore_errors=True)
    app.after(0, lambda: button_yt_convert.configure(state="normal"))

# ==================================================== GUI SETUP

app = ctk.CTk()
app.geometry("500x510")
app.title("Audio Converter")
app.resizable(False, False)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# ==================================================== CONSTANTS

status_label_var   = tk.StringVar(value="Select a file to convert.")
progress_label_var = tk.StringVar(value="0%")
history_label_var  = tk.StringVar(value="")
yt_status_label_var   = tk.StringVar(value="Enter a YouTube URL to download.")
yt_progress_label_var = tk.StringVar(value="0%")
yt_history_label_var  = tk.StringVar(value="")

# ==================================================== HELPERS

CARD   = ("gray88", "gray22")   # card background
MUTED  = ("gray52", "gray58")   # section title / hint text
PAD_X  = 14                     # inner horizontal padding
PAD_XO = 12                     # outer horizontal padding

def _card(parent, title):
    """Creates a labelled card frame and returns the inner content frame."""
    outer = ctk.CTkFrame(parent, corner_radius=12, fg_color=CARD)
    outer.pack(fill="x", padx=PAD_XO, pady=6)
    ctk.CTkLabel(outer, text=title,
                 font=ctk.CTkFont(size=10, weight="bold"),
                 text_color=MUTED).pack(anchor="w", padx=PAD_X, pady=(10, 4))
    inner = ctk.CTkFrame(outer, fg_color="transparent")
    inner.pack(fill="x", padx=PAD_X, pady=(0, 12))
    return inner

def _progress_row(parent, label_var):
    """Creates an inline progress-bar + percentage label row."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", pady=(0, 4))
    bar = ctk.CTkProgressBar(row, height=12, mode="determinate", corner_radius=6)
    bar.set(0)
    bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
    ctk.CTkLabel(row, textvariable=label_var,
                 font=ctk.CTkFont(size=12), width=38).pack(side="right")
    return bar

def _status_card(parent, status_var, history_var):
    """Creates a status + history card at the bottom of a tab. Returns (status_label, history_label)."""
    outer = ctk.CTkFrame(parent, corner_radius=12, fg_color=CARD)
    outer.pack(fill="x", padx=PAD_XO, pady=(6, 14))
    status_lbl = ctk.CTkLabel(outer, textvariable=status_var,
                               font=ctk.CTkFont(size=12),
                               wraplength=424, justify="left")
    status_lbl.pack(anchor="w", padx=PAD_X, pady=(10, 2))
    history_lbl = ctk.CTkLabel(outer, textvariable=history_var,
                                font=ctk.CTkFont(size=11), text_color=MUTED,
                                wraplength=424, justify="left")
    history_lbl.pack(anchor="w", padx=PAD_X, pady=(0, 10))
    return status_lbl, history_lbl

# ==================================================== GUI ELEMENTS

# ++++++++++++++++++++++++++++++ TABVIEW

tabview = ctk.CTkTabview(app, width=480, height=480, corner_radius=14)
tabview.pack(padx=10, pady=10)
tabview.add("Converter")
tabview.add("YouTube Downloader")

# ============================================================ CONVERTER TAB

# ++++++++++++++ MODE CARD

mode_inner = _card(tabview.tab("Converter"), "MODE")

combobox_multi = ctk.CTkComboBox(mode_inner, values=["Single File", "Multiple Files"],
                                 state="readonly", variable=tk.StringVar(value="Single File"),
                                 width=175, height=34, font=ctk.CTkFont(size=13),
                                 command=multi_selection_changed)
combobox_multi.pack(side="left")

multi_info_label = ctk.CTkLabel(mode_inner,
                                text="Scans 'input' folder in Multiple mode.",
                                font=ctk.CTkFont(size=11), text_color=MUTED)
multi_info_label.pack(side="left", padx=(12, 0))

# ++++++++++++++ FILE & FORMAT CARD

file_inner = _card(tabview.tab("Converter"), "FILE & FORMAT")

button_file = ctk.CTkButton(file_inner, text="Select File", width=158, height=34,
                             font=ctk.CTkFont(size=13), command=select_file)
button_file.pack(side="left")

combobox_formats = ctk.CTkComboBox(file_inner, values=formats,
                                   variable=tk.StringVar(value="mp3"),
                                   state="readonly", width=145, height=34,
                                   font=ctk.CTkFont(size=13))
combobox_formats.pack(side="left", padx=(10, 0))

# ++++++++++++++ CONVERT CARD

conv_inner = _card(tabview.tab("Converter"), "CONVERT")

button_convert = ctk.CTkButton(conv_inner, text="Convert", width=200, height=38,
                                font=ctk.CTkFont(size=14, weight="bold"),
                                command=convert_audio)
button_convert.pack(pady=(0, 10))

progress_bar = _progress_row(conv_inner, progress_label_var)

# ++++++++++++++ STATUS CARD

label_status, history_label = _status_card(tabview.tab("Converter"), status_label_var, history_label_var)

# ============================================================ YOUTUBE DOWNLOADER TAB

# ++++++++++++++ URL CARD

url_inner = _card(tabview.tab("YouTube Downloader"), "VIDEO URL")

link = ctk.CTkEntry(url_inner, height=36, font=ctk.CTkFont(size=12),
                    placeholder_text="https://www.youtube.com/watch?v=...")
link.pack(fill="x")

# ++++++++++++++ FORMAT CARD

yt_fmt_inner = _card(tabview.tab("YouTube Downloader"), "OUTPUT FORMAT")

yt_combobox_formats = ctk.CTkComboBox(yt_fmt_inner, values=formats,
                                      variable=tk.StringVar(value="mp3"),
                                      state="readonly", width=158, height=34,
                                      font=ctk.CTkFont(size=13))
yt_combobox_formats.pack(side="left")

# ++++++++++++++ DOWNLOAD CARD

dl_inner = _card(tabview.tab("YouTube Downloader"), "DOWNLOAD")

button_yt_convert = ctk.CTkButton(dl_inner, text="Download & Convert",
                                   width=200, height=38,
                                   font=ctk.CTkFont(size=14, weight="bold"),
                                   command=yt_convert)
button_yt_convert.pack(pady=(0, 10))

progress_bar_yt = _progress_row(dl_inner, yt_progress_label_var)

# ++++++++++++++ STATUS CARD

label_status_yt, history_label_yt = _status_card(tabview.tab("YouTube Downloader"), yt_status_label_var, yt_history_label_var)

# ==================================================== MAİNLOOP

app.mainloop()
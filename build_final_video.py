"""
AI-Powered Adviser — Final Polish
Adds: opening title card (5s) + background music mix + final export
"""
import os, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

FFMPEG = (r"C:\Users\e1000836\AppData\Local\Microsoft\WinGet\Packages"
          r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
          r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe")

OUT  = pathlib.Path("C:/Users/e1000836/Desktop/lxp_keynote_video")
W, H = 1920, 1080

# ── FONTS ─────────────────────────────────────────────────────────────────────
def fnt(size, bold=False):
    for name in (
        "C:/Windows/Fonts/Calibrib.ttf" if bold else "C:/Windows/Fonts/Calibri.ttf",
        "C:/Windows/Fonts/arialbd.ttf"  if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Arial.ttf",
    ):
        if os.path.exists(name):
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()

def CX(d, txt, y, f, col):
    w = d.textlength(txt, font=f)
    d.text((int((W - w) / 2), y), txt, font=f, fill=col)

# ── COLOURS ───────────────────────────────────────────────────────────────────
INK  = (4,   10,  28)
NAVY = (8,   20,  48)
GOLD = (255, 175,  0)
WHITE= (255, 255, 255)
GHOST= (190, 205, 230)

# ── SLIDE 0 — Opening Title Card (5 seconds) ──────────────────────────────────
title_png = OUT / "00_title.png"
img = Image.new("RGB", (W, H), INK)
d   = ImageDraw.Draw(img)

# Gold horizontal bar top
d.rectangle([(0,0),(W,8)], fill=GOLD)
# Gold horizontal bar bottom
d.rectangle([(0,H-8),(W,H)], fill=GOLD)

# Subtle background gradient effect using rectangles
for i in range(H):
    alpha = int(10 * (1 - abs(i - H//2) / (H//2)))
    d.line([(0,i),(W,i)], fill=(8+alpha, 20+alpha, 48+alpha))

# Large logo-style text
CX(d, "SANLAMCONNECT",       320, fnt(42),  GHOST)
d.rectangle([(W//2-200, 390),(W//2+200, 394)], fill=GOLD)

CX(d, "THE AI-POWERED",      420, fnt(90, True), WHITE)
CX(d, "ADVISER",             530, fnt(110,True), GOLD)

d.rectangle([(W//2-200, 670),(W//2+200, 674)], fill=GOLD)
CX(d, "PROOF OF VALUE  ·  2026", 700, fnt(36), GHOST)

img.save(str(title_png))
print("✓ Title card saved")

# ── RENDER TITLE CARD TO VIDEO (5s, silent) ───────────────────────────────────
title_seg = OUT / "00_title_seg.mp4"
subprocess.run([FFMPEG, "-y",
    "-loop","1","-i", str(title_png),
    "-f","lavfi","-i","anullsrc=r=44100:cl=stereo",
    "-c:v","libx264","-preset","fast","-crf","18",
    "-c:a","aac","-b:a","192k",
    "-r","25","-t","5",
    "-vf","scale=1920:1080",
    "-pix_fmt","yuv420p",
    str(title_seg)
], check=True)
print("✓ Title segment rendered")

# ── GENERATE SILENT MUSIC BED (simple sine tone at very low volume) ────────────
# Use a royalty-free approach: generate a soft pad tone via FFmpeg sine
# This gives a subtle audio presence under the voiceover
music_file = OUT / "music_bed.mp3"
subprocess.run([FFMPEG, "-y",
    "-f","lavfi",
    "-i","sine=frequency=220:sample_rate=44100",
    "-f","lavfi",
    "-i","sine=frequency=330:sample_rate=44100",
    "-filter_complex",
    "[0:a][1:a]amix=inputs=2:duration=longest,volume=0.04,lowpass=f=800",
    "-t","180",
    "-c:a","libmp3lame","-b:a","128k",
    str(music_file)
], check=True)
print("✓ Music bed generated")

# ── CONCAT: title + 5 segments ────────────────────────────────────────────────
concat_txt = OUT / "concat_final.txt"
segments = [
    "00_title_seg.mp4",
    "01_gap_seg.mp4",
    "02_demo_seg.mp4",
    "03_method_seg.mp4",
    "04_human_seg.mp4",
    "05_close_seg.mp4",
]
with open(str(concat_txt), "w") as f:
    for s in segments:
        f.write(f"file '{OUT / s}'\n")

# Concat all segments
concat_raw = OUT / "concat_raw.mp4"
subprocess.run([FFMPEG, "-y",
    "-f","concat","-safe","0",
    "-i", str(concat_txt),
    "-c","copy",
    str(concat_raw)
], check=True)
print("✓ Segments concatenated")

# ── MIX MUSIC BED UNDER VOICEOVER ─────────────────────────────────────────────
final_out = OUT / "AI_Powered_Adviser_FINAL.mp4"
subprocess.run([FFMPEG, "-y",
    "-i", str(concat_raw),
    "-stream_loop","-1","-i", str(music_file),
    "-filter_complex",
    "[0:a]volume=1.0[voice];[1:a]volume=0.06[music];[voice][music]amix=inputs=2:duration=first[aout]",
    "-map","0:v","-map","[aout]",
    "-c:v","copy",
    "-c:a","aac","-b:a","192k",
    str(final_out)
], check=True)
print(f"\n✅ DONE → {final_out}")
print("   Open this file to preview the final video.")

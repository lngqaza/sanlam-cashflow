"""
SanlamConnect Conference — Tech Enablement v2
Real PPTX slides + embedded demo videos + TED-style closing
Staff audience. ~11 minutes.
"""
import os, sys, pathlib, subprocess, json
sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from PIL import Image, ImageDraw, ImageFont
from elevenlabs.client import ElevenLabs

# ── PATHS ─────────────────────────────────────────────────────────────────────
FFMPEG  = (r"C:\Users\e1000836\AppData\Local\Microsoft\WinGet\Packages"
           r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
           r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe")
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")

SLIDES  = pathlib.Path("C:/Users/e1000836/Desktop/conference_videos/extracted_videos")
PPTSLIDES = pathlib.Path("C:/Users/e1000836/Desktop/conference_videos/slides")
OUT     = pathlib.Path("C:/Users/e1000836/Desktop/conference_videos/v2")
OUT.mkdir(parents=True, exist_ok=True)

ACC_DEMO   = SLIDES / "media3.mp4"           # Advice Copilot demo 2:54
AI_CLEAN   = pathlib.Path(r"C:\Users\e1000836\Desktop\Coference Videos\lxp_keynote_video\AI_Powered_Adviser_CLEAN.mp4")

# ── ELEVENLABS ────────────────────────────────────────────────────────────────
_key = subprocess.run(
    ["aws","secretsmanager","get-secret-value",
     "--secret-id","/sanlamconnect-lxp/backend/elevenlabs-api-key",
     "--region","eu-west-1","--query","SecretString","--output","text"],
    capture_output=True, text=True).stdout.strip()
el = ElevenLabs(api_key=_key)
VOICE = "hSH2fSzcOvC4AOZziVlo"
MODEL = "eleven_multilingual_v2"

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

def audio_duration(path):
    r = subprocess.run([FFPROBE,"-v","quiet","-print_format","json",
                        "-show_format", str(path)], capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])

def make_voice(text, out_path):
    if out_path.exists():
        print(f"   voice exists: {out_path.name}")
        return
    print(f"   generating: {out_path.name}")
    audio = el.text_to_speech.convert(
        voice_id=VOICE, model_id=MODEL, text=text,
        output_format="mp3_44100_128")
    with open(str(out_path), "wb") as f:
        for chunk in audio:
            f.write(chunk)

def make_segment_from_slide(slide_png, mp3, out_seg):
    if out_seg.exists():
        print(f"   seg exists: {out_seg.name}")
        return
    dur = audio_duration(mp3) + 1.5
    print(f"   rendering {out_seg.name} ({dur:.1f}s)...")
    subprocess.run([FFMPEG, "-y",
        "-loop","1","-i", str(slide_png),
        "-i", str(mp3),
        "-c:v","libx264","-preset","fast","-crf","18",
        "-c:a","aac","-b:a","192k",
        "-r","25","-t", str(dur),
        "-vf","scale=1920:1080","-pix_fmt","yuv420p",
        str(out_seg)
    ], check=True, capture_output=True)

def make_video_segment(input_video, out_seg, start=0, duration=None):
    """Re-encode a video clip to 1920x1080 AAC, optionally trimmed."""
    if out_seg.exists():
        print(f"   seg exists: {out_seg.name}")
        return
    args = [FFMPEG, "-y", "-ss", str(start), "-i", str(input_video)]
    if duration:
        args += ["-t", str(duration)]
    args += [
        "-c:v","libx264","-preset","fast","-crf","18",
        "-c:a","aac","-b:a","192k",
        "-r","25","-vf","scale=1920:1080:force_original_aspect_ratio=decrease,"
                        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black",
        "-pix_fmt","yuv420p",
        str(out_seg)
    ]
    print(f"   encoding video: {out_seg.name}...")
    subprocess.run(args, check=True, capture_output=True)

# ═══════════════════════════════════════════════════════════════════════════════
# VOICEOVERS  (tighter for staff — direct, no padding)
# ═══════════════════════════════════════════════════════════════════════════════
VOS = {
    1: ("vo_01.mp3",
        "Welcome. Today's session is about the Technology Enablement Workstream. "
        "Three things: modernising our IT estate, changing how we deliver, "
        "and making AI a real strategic capability — not a talking point. "
        "We listened to what our intermediaries told us, and this is our response."),

    2: ("vo_02.mp3",
        "We started by listening. The feedback was consistent and direct. "
        "Too much admin. Too many systems. Too much duplication. "
        "One adviser told us she could only see one client a day — "
        "the rest of her time consumed by paperwork and system navigation. "
        "Another asked why Sanlam couldn't be as seamless as Checkers Sixty60. "
        "These are not fringe complaints. They are the mainstream experience. "
        "Our job is to fix that."),

    3: ("vo_03.mp3",
        "Our response sits across three pillars. "
        "Technology modernisation — converging the intermediary experience, "
        "building once and scaling across the group. "
        "A future-fit delivery model — permanent product teams, "
        "building with intermediaries rather than for them. "
        "And leading innovation — AI embedded in every team's work, "
        "not isolated in a lab somewhere."),

    4: ("vo_04.mp3",
        "The old constraints no longer apply. "
        "Multi-year programmes, product-led thinking, technology as a cost centre — "
        "that is the old world. "
        "We are moving to continuous delivery, experience-led design, "
        "technology as a growth engine. "
        "AI is the most significant shift in our working lifetimes. "
        "Our ambition is to lead. The playbook: start small, learn fast, scale what works."),

    5: ("vo_05.mp3",
        "iHUB is the centrepiece — the connective tissue of the entire intermediary experience. "
        "One front door. No more app-hopping. "
        "Connected journeys where data flows automatically — no re-keying. "
        "A system that learns and personalises like Netflix. "
        "And an AI Concierge — one conversational interface "
        "across every tool and content source Sanlam has."),

    6: ("vo_06.mp3",
        "The vision is a day designed for client time. "
        "Eight AM — iHUB surfaces who matters today and exactly why. "
        "The nine-thirty meeting is fully prepped before the adviser arrives. "
        "The advice conversation generates a FAIS-compliant Record of Advice automatically. "
        "Quote to underwriting with no re-keying. Same-day issuance. "
        "Client self-serves on the app. Claims resolved without a single phone call. "
        "One experience. One data model. Compliance by design."),

    7: ("vo_07.mp3",
        "We are honest about the past. We built things and asked people to adopt them. "
        "It did not work well enough. "
        "Six shifts we are committing to: "
        "projects to permanent teams, product-led to experience-led, "
        "design-then-deliver to co-designed from day one, "
        "one-size-fits-all to personalised, "
        "innovation as a side project to innovation in every team, "
        "and built for delivery to built for adoption. "
        "Intermediaries shape what we build. From the start."),

    8: ("vo_08.mp3",
        "We serve two segments and design for both. "
        "For tied advisers — a fully furnished house. "
        "Platform, planning tool, AI assistants, practice management. End to end. "
        "For brokers — the electricity grid. "
        "Digital identity, data, AI services, secure connections. "
        "They choose their own appliances. Whatever they plug in, it works. "
        "Same principles across both: experience first, journeys not apps, "
        "financial plan as the spine, AI in the flow."),

    # Slide 9 intro — before ACC demo plays
    9: ("vo_09.mp3",
        "These are not slides about a future state. "
        "We have working prototypes in production right now. "
        "The Advice Conversation Copilot. The Leads Management platform. "
        "And the LXP — our AI-powered learning environment — a proof of value "
        "demonstrating what is possible before full industrialisation. "
        "Let me show you the Advice Copilot in action."),

    # Slide 10 intro — before AI_Powered_Adviser plays
    10: ("vo_10.mp3",
         "The road to 2030 is clear. "
         "Foundations now. Connected experience taking shape in the coming years. "
         "A single AI-enabled intermediary platform by 2030 — "
         "with eighty percent of adviser time spent with clients. "
         "Before I close, let me show you a glimpse of where this is headed — "
         "AI embedded at every stage of how we deliver."),

    # Closing TED slide VO
    "close": ("vo_close.mp3",
              "Let me leave you with five things. "
              "This is not about unrealistic delivery dates. "
              "It is a journey — of future-fit skills, AI-aided delivery, "
              "and a fundamental shift in how we think, fund, and prioritise digital. "
              "The intermediary is at the centre — we build with them, not for them. "
              "This is not a once-off project. It is a permanent capability we are building. "
              "And the proof points are real. "
              "Working prototypes today. Industrialised at scale tomorrow. "
              "The question is not whether. The question is how fast."),
}

# ═══════════════════════════════════════════════════════════════════════════════
# CLOSING TED SLIDE
# ═══════════════════════════════════════════════════════════════════════════════
def draw_closing_slide(path):
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d   = ImageDraw.Draw(img)

    # Subtle radial glow in centre
    import math
    cx, cy = W//2, H//2
    for r in range(500, 0, -10):
        alpha = int(18 * (1 - r/500))
        d.ellipse([(cx-r, cy-r),(cx+r, cy+r)], fill=(alpha, int(alpha*0.6), 0))

    GOLD  = (255, 175, 0)
    WHITE = (255, 255, 255)
    GHOST = (160, 180, 210)
    RED   = (200, 40, 40)

    # Top label
    CX(d, "SANLAMCONNECT  |  TECHNOLOGY ENABLEMENT", 42, fnt(26), GHOST)

    # Gold divider
    d.rectangle([(W//2-400, 96),(W//2+400, 99)], fill=GOLD)

    # Header
    CX(d, "Five Commitments", 118, fnt(52, True), WHITE)

    # 5 commitments
    commitments = [
        ("01", "Not about dates — about direction."),
        ("02", "A journey: Future-Fit Skills, AI-aided delivery at every stage,\n"
               "     and a shift in how we think, fund and prioritise digital."),
        ("03", "The intermediary is at the centre.\n"
               "     We build with them — not for them."),
        ("04", "This is not a once-off project.\n"
               "     It is a permanent, continuous capability."),
        ("05", "The proof points are real.\n"
               "     Working prototypes today. Industrialised at scale tomorrow."),
    ]

    y = 220
    for num, text in commitments:
        # Number badge
        d.rectangle([(120, y),(184, y+52)], fill=GOLD)
        tw = d.textlength(num, font=fnt(28, True))
        d.text((152 - tw//2, y+10), num, font=fnt(28, True), fill=(0,0,0))
        # Text lines
        lines = text.split('\n')
        d.text((208, y+8), lines[0], font=fnt(30, True), fill=WHITE)
        if len(lines) > 1:
            d.text((208, y+44), lines[1].strip(), font=fnt(26), fill=GHOST)
            y += 136
        else:
            y += 96

    # Bottom gold bar
    d.rectangle([(0, H-8),(W, H)], fill=GOLD)
    d.rectangle([(0, H-60),(W, H-8)], fill=(10, 10, 10))
    CX(d, "The question is not whether.  The question is how fast.", H-52, fnt(28, True), GOLD)

    img.save(str(path))

# ═══════════════════════════════════════════════════════════════════════════════
# BUILD
# ═══════════════════════════════════════════════════════════════════════════════
concat_lines = []

# ── Slides 1-10 ───────────────────────────────────────────────────────────────
for slide_num in range(1, 11):
    png  = PPTSLIDES / f"slide_{slide_num:02d}.png"
    vo_file, vo_text = VOS[slide_num]
    mp3  = OUT / vo_file
    seg  = OUT / f"seg_{slide_num:02d}.mp4"

    print(f"\nSlide {slide_num}:")
    make_voice(vo_text, mp3)
    make_segment_from_slide(png, mp3, seg)
    concat_lines.append(f"file '{seg}'")

    # After slide 9 — insert ACC Demo, then a bridge before slide 10
    if slide_num == 9:
        acc_seg = OUT / "seg_acc_demo.mp4"
        print("\nACC Demo:")
        make_video_segment(ACC_DEMO, acc_seg)
        concat_lines.append(f"file '{acc_seg}'")

        # Bridge narration after ACC demo — holds on slide 9 image
        bridge_mp3 = OUT / "vo_bridge_acc.mp3"
        bridge_seg = OUT / "seg_bridge_acc.mp4"
        bridge_text = (
            "That was the Advice Conversation Copilot — not a mockup, a working prototype. "
            "Currently in pilot with one hundred advisers, with clear plans to scale. "
            "This is proof of value. The industrialisation comes next. "
            "Now let me show you the bigger picture of where this is all headed."
        )
        print("\nBridge after ACC Demo:")
        make_voice(bridge_text, bridge_mp3)
        make_segment_from_slide(PPTSLIDES / "slide_09.png", bridge_mp3, bridge_seg)
        concat_lines.append(f"file '{bridge_seg}'")

    # After slide 10 — insert AI_Powered_Adviser
    if slide_num == 10:
        ai_seg = OUT / "seg_ai_clean.mp4"
        print("\nAI Powered Adviser vision:")
        make_video_segment(AI_CLEAN, ai_seg)
        concat_lines.append(f"file '{ai_seg}'")

# ── Closing TED Slide ─────────────────────────────────────────────────────────
print("\nClosing slide:")
close_png = OUT / "closing_slide.png"
close_mp3 = OUT / VOS["close"][0]
close_seg = OUT / "seg_closing.mp4"

if not close_png.exists():
    draw_closing_slide(close_png)
    print("   closing slide drawn")

make_voice(VOS["close"][1], close_mp3)
make_segment_from_slide(close_png, close_mp3, close_seg)
concat_lines.append(f"file '{close_seg}'")

# ── Final concat ──────────────────────────────────────────────────────────────
concat_f = OUT / "concat.txt"
with open(str(concat_f), "w") as f:
    f.write('\n'.join(concat_lines))

final = OUT / "SanlamConnect_TechEnablement_v2_FINAL.mp4"
print("\nConcatenating final video...")
subprocess.run([FFMPEG, "-y",
    "-f","concat","-safe","0","-i", str(concat_f),
    "-c:v","copy",
    "-c:a","aac","-b:a","192k","-ar","44100","-ac","2",
    str(final)
], check=True, capture_output=True)

size_mb = os.path.getsize(str(final)) / 1024 / 1024

# Get total duration
dur_info = subprocess.run([FFPROBE,"-v","quiet","-print_format","json",
    "-show_format", str(final)], capture_output=True, text=True)
total_dur = float(json.loads(dur_info.stdout)["format"]["duration"])
mins = int(total_dur // 60)
secs = int(total_dur % 60)

print(f"\nDONE")
print(f"File: {final}")
print(f"Duration: {mins}:{secs:02d}")
print(f"Size: {size_mb:.1f} MB")

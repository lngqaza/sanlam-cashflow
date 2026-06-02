"""
SanlamConnect Conference — Tech Enablement
Uses real PowerPoint slide exports + ElevenLabs voiceover
"""
import os, sys, pathlib, subprocess, json
sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from elevenlabs.client import ElevenLabs

FFMPEG  = (r"C:\Users\e1000836\AppData\Local\Microsoft\WinGet\Packages"
           r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
           r"\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe")
FFPROBE = FFMPEG.replace("ffmpeg.exe", "ffprobe.exe")

SLIDES_DIR = pathlib.Path("C:/Users/e1000836/Desktop/conference_video/slides")
OUT        = pathlib.Path("C:/Users/e1000836/Desktop/conference_video")

_key = subprocess.run(
    ["aws","secretsmanager","get-secret-value",
     "--secret-id","/sanlamconnect-lxp/backend/elevenlabs-api-key",
     "--region","eu-west-1","--query","SecretString","--output","text"],
    capture_output=True, text=True).stdout.strip()
el = ElevenLabs(api_key=_key)
VOICE = "hSH2fSzcOvC4AOZziVlo"
MODEL = "eleven_multilingual_v2"

# ── VOICEOVERS per slide (slide number -> script) ─────────────────────────────
VOICEOVERS = {
    1: (
        "Welcome. Today I want to take you through the Technology Enablement Workstream "
        "for SanlamConnect. This is about three things: modernising our IT estate, "
        "changing how we deliver, and embedding AI as a genuine strategic capability. "
        "Each pillar exists because our intermediaries told us something had to change — "
        "and we listened."
    ),
    2: (
        "We started by listening. Intermediaries were direct: too much admin, "
        "too many systems, too much duplication. One adviser told us she could only "
        "see one client per day because the rest of her time was spent on paperwork. "
        "Another asked why Sanlam couldn't be as seamless as Checkers Sixty60. "
        "These aren't fringe complaints — they are the mainstream experience. "
        "Our job is to fix that. And we are."
    ),
    3: (
        "Our response is structured across three pillars under the OneConnect IT mandate. "
        "First: technology modernisation — converging the intermediary experience, "
        "modernising our foundations, and building platforms once so they scale across the group. "
        "Second: a future-fit delivery model — moving from projects to permanent product teams, "
        "and shifting from building for intermediaries to building with them. "
        "Third: leading innovation — making AI a genuine strategic capability embedded in "
        "every team's work, not an isolated experiment."
    ),
    4: (
        "The constraints that shaped traditional IT delivery no longer apply. "
        "Multi-year programmes, product-led thinking, one-size-fits-all solutions — "
        "these are old world. The new world moves fast: continuous delivery, experience-led design, "
        "technology as a growth engine. "
        "AI is the most significant shift in our working lifetimes, "
        "and our ambition is to lead — not follow. "
        "We are taking the Checkers Sixty60 playbook: start small, learn fast, scale what works. "
        "That is the operating model we are committing to."
    ),
    5: (
        "iHUB is the centrepiece of our technology modernisation. "
        "It is more than a SanPort replacement — it is the connective tissue that "
        "orchestrates the entire intermediary experience into one coherent platform. "
        "Four capabilities define it. "
        "One front door: a converged, modular experience configurable to each intermediary's role. "
        "Connected journeys: data flows automatically — no re-keying, the system knows what Sanlam knows. "
        "It learns and personalises, like Netflix, adapting to how each adviser works. "
        "And an AI Concierge: a single conversational interface across every tool and content source — "
        "the new way to navigate Sanlam."
    ),
    6: (
        "Let me paint the vision. Here is what an adviser's day looks like with iHUB. "
        "At eight AM, iHUB surfaces who matters today and why — three clients flagged, "
        "with next best actions already prepared. "
        "By eight forty-five, the nine-thirty meeting is fully prepped before the adviser arrives. "
        "The advice conversation runs in real time — financial plan updates, compliance flagged in the moment, "
        "and a FAIS-compliant Record of Advice generated from the conversation itself. "
        "By ten-thirty, the plan flows through to quote to underwriting — no re-keying, same-day issuance. "
        "The client self-serves on the SanlamApp in the afternoon. "
        "A claim comes in at three PM — resolved without a single phone call. "
        "One experience. One data model. Compliance by design. AI as augmentation, not replacement."
    ),
    7: (
        "We are honest about the past. We built things and then asked intermediaries to adopt them. "
        "That has not worked well enough. "
        "We are committing to six fundamental shifts. "
        "From projects to permanent product teams. From product-led to experience-led. "
        "From design-then-deliver to co-designed from day one. "
        "From one-size-fits-all to personalised to each intermediary's recipe. "
        "From innovation as a side project to innovation embedded in every team. "
        "And most importantly: from built for delivery to built for adoption. "
        "Intermediaries will be involved in shaping what we build — from the very start."
    ),
    8: (
        "We serve two distinct intermediary segments, and we are designing for both. "
        "For tied advisers, we deliver a fully furnished house — "
        "the platform, the planning tool, the AI assistants, the practice management. End to end. "
        "For brokers, we are the electricity grid — "
        "digital identity, data and AI services, secure connections. "
        "Brokers choose their own appliances. Whatever they plug in, it works. "
        "Both routes share the same principles: experience first, journeys not apps, "
        "the financial plan as the spine, and insight and AI embedded in the flow."
    ),
    9: (
        "This is not a strategy document. We have proof points already in production. "
        "The Advice Conversation Copilot supports advisers in real time — "
        "flagging compliance, suggesting agenda items, and generating a FAIS-compliant "
        "Record of Advice automatically from the conversation. "
        "The Leads Management platform surfaces intelligent prioritisation for tied advisers — "
        "who to call, when, and why, based on life events and lapse risk signals. "
        "And the LXP — our AI-powered learning platform — is a working prototype, "
        "a proof of value demonstrating what is possible: VR simulation training, "
        "personalised development pathways, and CPD tracking. "
        "It is not yet industrialised, but it shows the direction of travel — "
        "and the art of the possible is already compelling. "
        "These were built with input from intermediaries and support staff."
    ),
    10: (
        "Let me close with the road ahead. "
        "Starting now: foundations are being put in place, first proof points are shipping, "
        "and intermediary co-design begins. "
        "Over the coming years, the connected experience takes shape — all three pillars converge, "
        "and iHUB becomes the operating standard across the intermediary base. "
        "By 2030, the ambition is a single AI-enabled intermediary experience, "
        "with the financial plan at the core, and eighty percent of adviser time spent with clients. "
        "The question is not whether we get there. "
        "The question is how fast. "
        "Technology is no longer a back-office function. It is the competitive edge. "
        "And we are building it — with you."
    ),
    # Slide 11 is typically blank/end — short hold
    11: None,
}

def audio_duration(path):
    r = subprocess.run([FFPROBE,"-v","quiet","-print_format","json",
                        "-show_format", str(path)], capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])

concat_lines = []

for slide_num in range(1, 12):
    png  = SLIDES_DIR / f"slide_{slide_num:02d}.png"
    mp3  = OUT / f"vo_{slide_num:02d}.mp3"
    seg  = OUT / f"seg_{slide_num:02d}.mp4"

    vo_text = VOICEOVERS.get(slide_num)

    if vo_text is None:
        # Blank/end slide — 3 second hold, silent
        if not seg.exists():
            print(f"Slide {slide_num}: end card (3s silent)")
            subprocess.run([FFMPEG, "-y",
                "-loop","1","-i", str(png),
                "-f","lavfi","-i","anullsrc=r=44100:cl=stereo",
                "-c:v","libx264","-preset","fast","-crf","18",
                "-c:a","aac","-b:a","128k",
                "-r","25","-t","3",
                "-vf","scale=1920:1080","-pix_fmt","yuv420p",
                str(seg)
            ], check=True, capture_output=True)
        concat_lines.append(f"file '{seg}'")
        continue

    # Generate voiceover if needed
    if not mp3.exists():
        print(f"Slide {slide_num}: generating voiceover...")
        audio = el.text_to_speech.convert(
            voice_id=VOICE, model_id=MODEL, text=vo_text,
            output_format="mp3_44100_128",
        )
        with open(str(mp3), "wb") as f:
            for chunk in audio:
                f.write(chunk)
    else:
        print(f"Slide {slide_num}: voice exists")

    dur = audio_duration(mp3) + 1.5  # 1.5s padding after voice ends

    # Render segment
    if not seg.exists():
        print(f"Slide {slide_num}: rendering {dur:.1f}s segment...")
        subprocess.run([FFMPEG, "-y",
            "-loop","1","-i", str(png),
            "-i", str(mp3),
            "-c:v","libx264","-preset","fast","-crf","18",
            "-c:a","aac","-b:a","192k",
            "-r","25","-t", str(dur),
            "-vf","scale=1920:1080",
            "-pix_fmt","yuv420p",
            str(seg)
        ], check=True, capture_output=True)
    else:
        print(f"Slide {slide_num}: segment exists")

    concat_lines.append(f"file '{seg}'")

# Concat
concat_f = OUT / "concat_pptx.txt"
with open(str(concat_f), "w") as f:
    f.write('\n'.join(concat_lines))

final = OUT / "SanlamConnect_TechEnablement_FINAL.mp4"
print("\nConcatenating...")
subprocess.run([FFMPEG, "-y",
    "-f","concat","-safe","0","-i", str(concat_f),
    "-c","copy", str(final)
], check=True, capture_output=True)

size_mb = os.path.getsize(str(final)) / 1024 / 1024
total_s = sum(audio_duration(OUT / f"vo_{n:02d}.mp3") for n in range(1,11) if (OUT/f"vo_{n:02d}.mp3").exists())
print(f"\nDONE -> {final}")
print(f"Size: {size_mb:.1f} MB")

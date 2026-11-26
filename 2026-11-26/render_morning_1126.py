#!/usr/bin/env python3
"""
Render morning reel 2026-11-26 → MP4 + JPEG cover
CRF 10, bitrate target >4 Mbps
"""
import subprocess, os, sys, json, pathlib, shutil

ROOT   = pathlib.Path(__file__).parent
HTML   = ROOT / "morning-sip-stoppage-reel.html"
MP4    = ROOT / "morning-sip-stoppage-reel.mp4"
COVER  = ROOT / "morning-sip-stoppage-reel-cover.jpg"
FRAMES = pathlib.Path("/tmp/claude-0/-home-claude-finpulse-reels/62c3497c-7e0a-5201-931f-0ea4bc618d34/scratchpad/frames_morning_1126")
MUSIC  = ROOT.parent / "music" / "atlasaudio-soft-corporate-613334.mp3"

W, H   = 1080, 1920
FPS    = 30
TOTAL  = 45.0
COVER_T = 0.5

print("[1/6] Preparing frame output dir …")
if FRAMES.exists():
    shutil.rmtree(FRAMES)
FRAMES.mkdir(parents=True)

print("[2/6] Launching Playwright to capture frames …")
capture_script = f"""
import asyncio, math
from playwright.async_api import async_playwright

async def capture():
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=['--no-sandbox','--disable-gpu'])
        ctx = await browser.new_context(viewport={{'width':{W},'height':{H}}}, device_scale_factor=1)
        page = await ctx.new_page()
        await page.goto('file://{HTML}', wait_until='networkidle')
        await page.wait_for_timeout(500)

        total = {TOTAL}
        fps   = {FPS}
        n     = int(total * fps)
        for i in range(n):
            T = i / fps
            await page.evaluate(f'window.setT({{T}})')
            await page.screenshot(path='{FRAMES}/f{{i:05d}}.png', full_page=False)
            if i % 60 == 0:
                print(f'  frame {{i}}/{{n}} T={{T:.2f}}s')

        # cover frame
        await page.evaluate(f'window.setT({COVER_T})')
        await page.screenshot(path='{FRAMES}/cover.png', full_page=False)
        print('  cover frame captured')
        await browser.close()

asyncio.run(capture())
"""

result = subprocess.run(
    [sys.executable, "-c", capture_script],
    capture_output=True, text=True
)
if result.returncode != 0:
    print("PLAYWRIGHT ERROR:", result.stderr[-3000:])
    sys.exit(1)
print(result.stdout)

print("[3/6] Converting cover PNG → JPEG …")
subprocess.run([
    "ffmpeg", "-y", "-i", str(FRAMES / "cover.png"),
    "-q:v", "2", str(COVER)
], check=True, capture_output=True)
print(f"  cover → {COVER}")

print("[4/6] Encoding MP4 (CRF 10, libx264 slow) …")
# Check if music file exists
music_exists = MUSIC.exists()
print(f"  Music file exists: {music_exists} → {MUSIC}")

ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-framerate", str(FPS),
    "-i", str(FRAMES / "f%05d.png"),
]
if music_exists:
    ffmpeg_cmd += [
        "-stream_loop", "-1",
        "-i", str(MUSIC),
        "-shortest",
        "-map", "0:v", "-map", "1:a",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
    ]
ffmpeg_cmd += [
    "-c:v", "libx264",
    "-preset", "slow",
    "-crf", "10",
    "-maxrate", "12M",
    "-bufsize", "24M",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    str(MP4)
]

result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
if result.returncode != 0:
    print("FFMPEG ERROR:", result.stderr[-3000:])
    sys.exit(1)
print(f"  MP4 encoded → {MP4}")

print("[5/6] Verifying bitrate with ffprobe …")
probe = subprocess.run([
    "ffprobe", "-v", "quiet", "-print_format", "json",
    "-show_format", "-show_streams", str(MP4)
], capture_output=True, text=True, check=True)
info = json.loads(probe.stdout)
bitrate_bps = int(info["format"]["bit_rate"])
bitrate_kbps = bitrate_bps // 1000
duration = float(info["format"]["duration"])
size_mb = int(info["format"]["size"]) / 1024 / 1024

print(f"  Duration : {duration:.1f}s")
print(f"  Bitrate  : {bitrate_kbps} kbps ({bitrate_kbps/1000:.2f} Mbps)")
print(f"  Size     : {size_mb:.1f} MB")

if bitrate_kbps < 4000:
    print(f"  !! BITRATE TOO LOW: {bitrate_kbps} kbps < 4000 kbps !!")
    sys.exit(1)
else:
    print(f"  ✓ Bitrate OK: {bitrate_kbps} kbps > 4000 kbps")

print("[6/6] Cleaning up frames …")
shutil.rmtree(FRAMES)

print(f"\nDONE")
print(f"  MP4   : {MP4}")
print(f"  Cover : {COVER}")
print(f"  Bitrate: {bitrate_kbps} kbps  Duration: {duration:.1f}s")

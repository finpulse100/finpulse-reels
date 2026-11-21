#!/usr/bin/env python3
"""Render evening reel: India Decouples from Nasdaq Crash — 1080x1920 30fps 45s CRF10"""
import asyncio, os, subprocess, shutil, json

REPO    = "/home/claude/finpulse-reels"
HTML    = f"{REPO}/2026-11-21/evening-nasdaq-crash-reel.html"
MUSIC   = f"{REPO}/music/apalonbeats-soft-background-music-576280.mp3"
FRAMES  = "/tmp/eve_nasdaq_frames"
OUT     = f"{REPO}/2026-11-21/evening-nasdaq-crash.mp4"
COVER   = f"{REPO}/2026-11-21/evening-nasdaq-crash-cover.jpg"
FPS     = 30
TOTAL   = 45
NFRAMES = FPS * TOTAL   # 1350
COVER_T = 0.5           # thumbnail pose

async def render():
    from playwright.async_api import async_playwright

    os.makedirs(FRAMES, exist_ok=True)
    for f in os.listdir(FRAMES):
        os.remove(os.path.join(FRAMES, f))

    async with async_playwright() as p:
        browser = await p.chromium.launch(args=['--disable-web-security'])
        ctx = await browser.new_context(
            viewport={'width': 1080, 'height': 1920},
            device_scale_factor=1
        )
        page = await ctx.new_page()
        await page.goto(f"file://{HTML}", wait_until='networkidle')
        await page.wait_for_timeout(600)

        # Cover at COVER_T
        print(f"Capturing cover at T={COVER_T}s …")
        await page.evaluate(f'window.setT({COVER_T:.5f})')
        await page.wait_for_timeout(80)
        await page.screenshot(
            path=COVER,
            clip={'x': 0, 'y': 0, 'width': 1080, 'height': 1920},
            type='jpeg', quality=92
        )
        print(f"Cover saved: {COVER}")

        print(f"Rendering {NFRAMES} frames …")
        for i in range(NFRAMES):
            t = i / FPS
            await page.evaluate(f'window.setT({t:.5f})')
            frame_path = os.path.join(FRAMES, f"f{i:05d}.png")
            await page.screenshot(
                path=frame_path,
                clip={'x': 0, 'y': 0, 'width': 1080, 'height': 1920}
            )
            if i % 150 == 0:
                print(f"  frame {i}/{NFRAMES}  T={t:.2f}s")

        await browser.close()
    print("Frames done.")

def encode():
    # Rule 4: libx264 -preset slow -crf 10 -maxrate 12M -bufsize 24M
    music_flag = ['-i', MUSIC] if os.path.exists(MUSIC) else []
    audio_flag = ['-c:a', 'aac', '-b:a', '192k', '-shortest'] if music_flag else ['-an']

    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(FPS),
        '-i', os.path.join(FRAMES, 'f%05d.png'),
        *music_flag,
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '10',
        '-maxrate', '12M', '-bufsize', '24M',
        '-pix_fmt', 'yuv420p',
        *audio_flag,
        '-movflags', '+faststart',
        OUT
    ]
    print("Encoding …")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFMPEG stderr:", result.stderr[-3000:])
        raise RuntimeError("ffmpeg encode failed")
    print(f"Encoded: {OUT}")

def verify():
    result = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json',
         '-show_format', '-show_streams', OUT],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    fmt      = data['format']
    duration = float(fmt['duration'])
    bitrate  = int(fmt['bit_rate'])
    size_mb  = int(fmt['size']) / 1e6
    print(f"\n──── VERIFY ────")
    print(f"Duration: {duration:.3f}s  (expected 45.0)")
    print(f"Bitrate:  {bitrate//1000} kbps  (must be >4000)")
    print(f"Size:     {size_mb:.1f} MB")
    for s in data.get('streams', []):
        if s['codec_type'] == 'video':
            print(f"Video:    {s['codec_name']} {s['width']}x{s['height']} @ {s.get('r_frame_rate','')} fps")
        elif s['codec_type'] == 'audio':
            print(f"Audio:    {s['codec_name']} {s.get('bit_rate','')} bps")
    if bitrate < 4_000_000:
        print("WARNING ⚠ bitrate below 4 Mbps floor!")
        return False
    print("Bitrate OK ✓")
    return True

if __name__ == '__main__':
    asyncio.run(render())
    encode()
    ok = verify()
    if not ok:
        raise SystemExit("FAIL: bitrate too low")
    print("\nDone! ✓")
    print(f"  MP4:   {OUT}")
    print(f"  Cover: {COVER}")

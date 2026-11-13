#!/usr/bin/env python3
"""Render evening Razorpay IPO reel — 1080x1920, 30fps, 45s, CRF 8"""
import asyncio, os, subprocess, shutil

REPO   = "/home/claude/finpulse-reels"
HTML   = f"{REPO}/2026-11-13/evening-razorpay-ipo-reel.html"
MUSIC  = f"{REPO}/music/atlasaudio-soft-corporate-613334.mp3"
FRAMES = "/tmp/eve_frames"
OUT    = f"{REPO}/2026-11-13/evening-razorpay-ipo.mp4"
FPS    = 30
TOTAL  = 45       # seconds
NFRAMES = FPS * TOTAL  # 1350

async def render():
    from playwright.async_api import async_playwright

    os.makedirs(FRAMES, exist_ok=True)
    # Remove old frames
    for f in os.listdir(FRAMES):
        os.remove(os.path.join(FRAMES, f))

    async with async_playwright() as p:
        browser = await p.chromium.launch(args=['--disable-web-security'])
        ctx = await browser.new_context(
            viewport={'width': 1080, 'height': 1920},
            device_scale_factor=1
        )
        page = await ctx.new_page()
        file_url = f"file://{HTML}"
        await page.goto(file_url, wait_until='networkidle')
        await page.wait_for_timeout(500)

        print(f"Rendering {NFRAMES} frames...")
        for i in range(NFRAMES):
            t = i / FPS
            await page.evaluate(f'window.setT({t:.5f})')
            frame_path = os.path.join(FRAMES, f"f{i:05d}.png")
            await page.screenshot(path=frame_path, clip={'x':0,'y':0,'width':1080,'height':1920})
            if i % 150 == 0:
                print(f"  frame {i}/{NFRAMES} (T={t:.2f}s)")

        await browser.close()
    print("Frames done.")

def encode():
    # Encode: libx264 -preset slow -crf 8 (CRF 12 gives ~3.2 Mbps on this content)
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(FPS),
        '-i', os.path.join(FRAMES, 'f%05d.png'),
        '-i', MUSIC,
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '8',
        '-maxrate', '10M', '-bufsize', '20M',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k',
        '-shortest',
        '-movflags', '+faststart',
        OUT
    ]
    print("Encoding...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFMPEG stderr:", result.stderr[-2000:])
        raise RuntimeError("ffmpeg failed")
    print(f"Encoded: {OUT}")

def verify():
    result = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', OUT],
        capture_output=True, text=True
    )
    import json
    data = json.loads(result.stdout)
    fmt = data['format']
    duration = float(fmt['duration'])
    bitrate  = int(fmt['bit_rate'])
    size_mb  = int(fmt['size']) / 1e6
    print(f"\n--- VERIFY ---")
    print(f"Duration: {duration:.3f}s (expected 45.0)")
    print(f"Bitrate:  {bitrate//1000} kbps (must be >4000)")
    print(f"Size:     {size_mb:.1f} MB")
    for s in data.get('streams', []):
        if s['codec_type'] == 'video':
            print(f"Video:    {s['codec_name']} {s['width']}x{s['height']} @ {s.get('r_frame_rate','')} fps")
        elif s['codec_type'] == 'audio':
            print(f"Audio:    {s['codec_name']} {s.get('bit_rate','')} bps")
    if bitrate < 4_000_000:
        print("WARNING: bitrate below 4 Mbps floor!")
    else:
        print("Bitrate OK ✓")

if __name__ == '__main__':
    asyncio.run(render())
    encode()
    verify()
    print("Done!")

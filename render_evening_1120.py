#!/usr/bin/env python3
"""Render evening Gold Crash reel — 2026-11-20 — 1080x1920, 30fps, 45s, CRF 10"""
import asyncio, os, subprocess, shutil, json

REPO   = "/home/claude/finpulse-reels"
HTML   = f"{REPO}/2026-11-20/evening-gold-crash-reel.html"
MUSIC  = f"{REPO}/music/nastelbom-soft-corporate-488309.mp3"
FRAMES = "/tmp/claude-0/-home-claude-finpulse-reels/673e76bb-73f8-5309-9a75-cdca27e28d27/scratchpad/eve_frames_1120"
OUT    = f"{REPO}/2026-11-20/evening-gold-crash.mp4"
FPS    = 30
TOTAL  = 45       # seconds
NFRAMES = FPS * TOTAL  # 1350

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
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(FPS),
        '-i', os.path.join(FRAMES, 'f%05d.png'),
        '-i', MUSIC,
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '10',
        '-maxrate', '12M', '-bufsize', '24M',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k',
        '-shortest',
        '-movflags', '+faststart',
        OUT
    ]
    print("Encoding...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFMPEG stderr:", result.stderr[-3000:])
        raise RuntimeError("ffmpeg failed")
    print(f"Encoded: {OUT}")

def verify():
    result = subprocess.run(
        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', OUT],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    fmt = data['format']
    duration = float(fmt['duration'])
    bitrate  = int(fmt['bit_rate'])
    size_mb  = int(fmt['size']) / 1e6
    print(f"\n--- VERIFY ---")
    print(f"Duration: {duration:.3f}s (expected ~45.0)")
    print(f"Bitrate:  {bitrate//1000} kbps (must be >4000)")
    print(f"Size:     {size_mb:.1f} MB")
    for s in data.get('streams', []):
        if s['codec_type'] == 'video':
            print(f"Video:    {s['codec_name']} {s['width']}x{s['height']} @ {s.get('r_frame_rate','')} fps")
        elif s['codec_type'] == 'audio':
            print(f"Audio:    {s['codec_name']} {s.get('bit_rate','?')} bps")
    if bitrate < 4_000_000:
        print("WARNING: bitrate below 4 Mbps floor!")
        return False
    else:
        print("Bitrate OK ✓")
        return True

if __name__ == '__main__':
    asyncio.run(render())
    encode()
    ok = verify()
    if not ok:
        raise SystemExit("RULE 4 FAIL: bitrate below 4 Mbps")
    print("Render complete ✓")

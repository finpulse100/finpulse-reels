#!/usr/bin/env python3
"""
Render evening reel 2026-11-14 — India Trade Deficit 12-month high
1080x1920, 30fps, 45s, CRF 12, nastelbom-soft-corporate-485896.mp3
Audio boost: volume=3.5, alimiter=0.95
"""
import asyncio, os, subprocess, shutil, json, sys

REPO    = "/home/claude/finpulse-reels"
HTML    = f"{REPO}/2026-11-14/evening-trade-deficit-reel.html"
MUSIC   = f"{REPO}/music/nastelbom-soft-corporate-485896.mp3"
FRAMES  = "/tmp/claude-0/-home-claude-finpulse-reels/905cefd5-4e73-576d-9fee-aaf8ae02fac5/scratchpad/eve1114_frames"
OUT     = f"{REPO}/2026-11-14/evening-trade-deficit-reel.mp4"
COVER_P = f"{REPO}/2026-11-14/evening-trade-deficit-cover-raw.png"
FPS     = 30
TOTAL   = 45
NFRAMES = FPS * TOTAL  # 1350
COVER_T = 1.5          # window.COVER_T


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
        await page.wait_for_timeout(500)

        # Cover frame
        await page.evaluate(f'window.setT({COVER_T})')
        await page.wait_for_timeout(100)
        await page.screenshot(
            path=COVER_P,
            clip={'x': 0, 'y': 0, 'width': 1080, 'height': 1920}
        )
        print(f"  cover saved: {COVER_P}")

        # All frames
        for i in range(NFRAMES):
            t = i / FPS
            await page.evaluate(f'window.setT({t:.5f})')
            frame_path = os.path.join(FRAMES, f"f{i:05d}.png")
            await page.screenshot(
                path=frame_path,
                clip={'x': 0, 'y': 0, 'width': 1080, 'height': 1920}
            )
            if i % 150 == 0:
                print(f"  frame {i}/{NFRAMES}  T={t:.2f}s", flush=True)

        await browser.close()
    print("  render complete")


def encode():
    # Audio boost: volume=3.5, alimiter=0.95 (from Nov 13 feedback)
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(FPS),
        '-i', os.path.join(FRAMES, 'f%05d.png'),
        '-i', MUSIC,
        '-c:v', 'libx264', '-preset', 'slow', '-crf', '12',
        '-maxrate', '10M', '-bufsize', '20M',
        '-pix_fmt', 'yuv420p',
        '-filter_complex', '[1:a]volume=3.5,alimiter=limit=0.95[a]',
        '-map', '0:v', '-map', '[a]',
        '-c:a', 'aac', '-b:a', '192k',
        '-shortest', '-movflags', '+faststart',
        OUT
    ]
    print("  encoding…", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("FFMPEG STDERR:", result.stderr[-3000:])
        raise RuntimeError("ffmpeg encode failed")
    print(f"  encoded → {OUT}")


def make_cover():
    """Convert raw PNG cover to JPG 1080×1920"""
    cover_jpg = OUT.replace('.mp4', '-cover.jpg')
    cmd = ['ffmpeg', '-y', '-i', COVER_P,
           '-vf', 'scale=1080:1920',
           '-q:v', '2', cover_jpg]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("cover JPG warning:", result.stderr[-800:])
    else:
        print(f"  cover JPG → {cover_jpg}")
    return cover_jpg


def verify():
    result = subprocess.run([
        'ffprobe', '-v', 'quiet',
        '-print_format', 'json',
        '-show_format', '-show_streams', OUT
    ], capture_output=True, text=True)
    data = json.loads(result.stdout)
    fmt = data['format']
    size_mb = int(fmt['size']) / 1_000_000
    bitrate = int(fmt['bit_rate'])
    dur = float(fmt['duration'])
    print(f"  verified: {size_mb:.1f} MB, {bitrate/1_000_000:.2f} Mbps, {dur:.1f}s")
    if bitrate < 4_000_000:
        print("  WARNING: bitrate below 4 Mbps floor!")
    if size_mb < 15 or size_mb > 35:
        print(f"  WARNING: size {size_mb:.1f} MB outside 15-35 MB target")
    return {'size_mb': round(size_mb, 1), 'bitrate_mbps': round(bitrate/1_000_000, 2), 'duration': round(dur, 1)}


if __name__ == '__main__':
    print("=== Fin Pulse evening render · 2026-11-14 ===")
    print("Step 1: Rendering frames…")
    asyncio.run(render())
    print("Step 2: Encoding video…")
    encode()
    print("Step 3: Cover JPEG…")
    cover_jpg = make_cover()
    print("Step 4: Verifying output…")
    stats = verify()
    print(f"Done. {stats}")

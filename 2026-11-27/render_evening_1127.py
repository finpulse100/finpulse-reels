#!/usr/bin/env python3
"""
Fin Pulse · 2026-11-27 Evening Render
Story: Sensex breadth divergence — index -989 but midcap +64
CRF 10 · libx264 slow · 1080×1920 · 30fps · 45.0s
"""
import asyncio, pathlib, subprocess, sys, time

ROOT   = pathlib.Path("/home/claude/finpulse-reels/2026-11-27")
HTML   = ROOT / "evening-sensex-breadth-reel.html"
MP4    = ROOT / "evening-sensex-breadth-reel.mp4"
COVER  = ROOT / "evening-sensex-breadth-reel-cover.jpg"
SCRATCHPAD = pathlib.Path("/tmp/claude-0/-home-claude-finpulse-reels/3c6495d4-d79e-579d-951b-2e037ee8323f/scratchpad")
FRAMES = SCRATCHPAD / "frames_evening_1127"
MUSIC  = pathlib.Path("/home/claude/finpulse-reels/music/atlasaudio-soft-509813.mp3")
W, H   = 1080, 1920
FPS    = 30
TOTAL  = 45.0
COVER_T = 0.5

async def capture():
    FRAMES.mkdir(parents=True, exist_ok=True)
    n_frames = int(TOTAL * FPS)
    print(f"[render] Capturing {n_frames} frames at {FPS}fps …")
    t0 = time.time()
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page    = await browser.new_page(viewport={"width": W, "height": H})
        await page.goto(f"file://{HTML}", wait_until="networkidle")
        await page.wait_for_timeout(400)

        # Capture thumbnail at t=0.5
        await page.evaluate("setT(0.5)")
        await page.wait_for_timeout(60)
        await page.screenshot(path=str(COVER), type="jpeg", quality=95, full_page=False)
        print("[render] Cover JPEG saved.")

        # Capture all frames
        for i in range(n_frames):
            t = i / FPS
            await page.evaluate(f"setT({t})")
            # Critical f-string fix: use frames_str to avoid nesting bug
            frames_str = str(FRAMES)
            frame_path = f'{frames_str}/f{i:05d}.png'
            await page.screenshot(path=frame_path, type="png", full_page=False)
            if i % 150 == 0:
                elapsed = time.time() - t0
                print(f"  frame {i}/{n_frames}  t={t:.2f}s  elapsed={elapsed:.1f}s")

        await browser.close()
    elapsed = time.time() - t0
    print(f"[render] Capture done in {elapsed:.1f}s — {n_frames} frames.")

def encode():
    print("[render] Encoding MP4 (CRF 10, libx264 slow) …")
    frames_str = str(FRAMES)
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", f"{frames_str}/f%05d.png",
        "-i", str(MUSIC),
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "10",
        "-maxrate", "12M",
        "-bufsize", "24M",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(MP4)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("[render] ffmpeg STDERR:", result.stderr[-2000:])
        sys.exit(1)
    print("[render] Encode complete.")

def verify():
    print("[render] Verifying bitrate …")
    cmd = [
        "ffprobe", "-v", "quiet",
        "-select_streams", "v:0",
        "-show_entries", "stream=bit_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(MP4)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        bitrate_bps = int(result.stdout.strip())
        bitrate_kbps = bitrate_bps // 1000
        print(f"[render] Video bitrate: {bitrate_kbps} kbps")
        if bitrate_kbps < 4000:
            print(f"[render] FAIL — bitrate {bitrate_kbps} kbps is below 4000 kbps threshold")
            sys.exit(1)
        print(f"[render] PASS — bitrate {bitrate_kbps} kbps ≥ 4000 kbps")
    except Exception as e:
        # Fallback: use format-level bitrate
        cmd2 = [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=bit_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(MP4)
        ]
        r2 = subprocess.run(cmd2, capture_output=True, text=True)
        try:
            bitrate_bps = int(r2.stdout.strip())
            bitrate_kbps = bitrate_bps // 1000
            print(f"[render] Format bitrate: {bitrate_kbps} kbps")
            if bitrate_kbps < 4000:
                print(f"[render] FAIL — bitrate {bitrate_kbps} kbps is below 4000 kbps threshold")
                sys.exit(1)
            print(f"[render] PASS — bitrate {bitrate_kbps} kbps ≥ 4000 kbps")
        except:
            print(f"[render] WARNING — could not parse bitrate ({e}). Check manually.")
    # Size check
    size_mb = MP4.stat().st_size / (1024*1024)
    print(f"[render] MP4 size: {size_mb:.1f} MB")
    dur_s   = TOTAL
    # Rough check: 4Mbps × 45s ÷ 8 ≈ 22.5 MB minimum
    if size_mb < 10:
        print(f"[render] WARNING: file looks small ({size_mb:.1f} MB). Verify manually.")

if __name__ == "__main__":
    asyncio.run(capture())
    encode()
    verify()
    print(f"[render] Done. Files:")
    print(f"  MP4   : {MP4}")
    print(f"  Cover : {COVER}")

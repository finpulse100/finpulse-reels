"""
Fin Pulse · 2026-11-28 Evening Render
Story  : IT Sector Rotation — TCS +8.26%, Nifty IT +4.58% vs Nifty -0.75%
Hook   : "The Nifty lost its 4-week winning streak. TCS gained 8%. If you track the index, you're watching the wrong scoreboard."
Palette: Midnight Gold #0d0900
Music  : nastelbom-soft-corporate-485896.mp3  (Electronic, not used in last 4 runs)
Encode : libx264 -preset slow -crf 10 -maxrate 12M -bufsize 24M  (RULE 4 ≥ 4 Mbps)
"""
import asyncio, subprocess, os, sys, shutil, json
from pathlib import Path
from playwright.async_api import async_playwright

REPO   = "/home/claude/finpulse-reels"
HTML   = f"{REPO}/2026-11-28/evening-it-rotation-reel.html"
MUSIC  = f"{REPO}/music/nastelbom-soft-corporate-485896.mp3"
frames_str = "/tmp/eve_1128_frames"
OUT    = f"{REPO}/2026-11-28/evening-it-rotation-reel.mp4"
COVER  = f"{REPO}/2026-11-28/evening-it-rotation-reel-cover.jpg"

FPS     = 30
TOTAL   = 45
NFRAMES = FPS * TOTAL   # 1350

os.makedirs(frames_str, exist_ok=True)

# ── 1. Render frames ──────────────────────────────────────
async def render():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1080, "height": 1920},
            device_scale_factor=1
        )
        page = await ctx.new_page()
        await page.goto(f"file://{HTML}", wait_until="networkidle")
        await page.evaluate("setT(0.5)")  # thumbnail / cover

        # ── cover frame ──
        await page.screenshot(path=COVER, type="jpeg", quality=92,
                               clip={"x":0,"y":0,"width":1080,"height":1920})
        print(f"Cover saved: {COVER}")

        # ── all frames ──
        for f in range(NFRAMES):
            T = f / FPS
            await page.evaluate(f"setT({T})")
            frame_path = f"{frames_str}/frame_{f:05d}.png"
            await page.screenshot(
                path=frame_path,
                clip={"x": 0, "y": 0, "width": 1080, "height": 1920}
            )
            if f % 150 == 0:
                print(f"  frame {f}/{NFRAMES}  T={T:.2f}s")

        await browser.close()
    print("Frame capture done.")

asyncio.run(render())

# ── 2. Encode video + mux audio ───────────────────────────
cmd = [
    "ffmpeg", "-y",
    "-framerate", str(FPS),
    "-i", f"{frames_str}/frame_%05d.png",
    "-i", MUSIC,
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
    OUT
]
print("Encoding …")
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode != 0:
    print("FFMPEG STDERR:", result.stderr[-2000:])
    sys.exit(1)
print(f"Encoded: {OUT}")

# ── 3. Verify bitrate (RULE 4: must exceed 4 Mbps) ────────
probe = subprocess.run(
    ["ffprobe", "-v", "quiet", "-print_format", "json",
     "-show_format", OUT],
    capture_output=True, text=True
)
info = json.loads(probe.stdout)
bitrate_bps = int(info["format"]["bit_rate"])
size_mb = os.path.getsize(OUT) / (1024*1024)
print(f"Bitrate: {bitrate_bps//1000:,} kbps  |  Size: {size_mb:.1f} MB")
if bitrate_bps < 4_000_000:
    print(f"ERROR: bitrate {bitrate_bps//1000} kbps < 4,000 kbps  — RULE 4 violated!")
    sys.exit(1)
print("RULE 4 passed ✓")

# ── 4. Cleanup frames ─────────────────────────────────────
shutil.rmtree(frames_str, ignore_errors=True)
print("Done.")

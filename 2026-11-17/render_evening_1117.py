#!/usr/bin/env python3
"""
Fin Pulse — Evening reel render script
2026-11-17 · Story: Nifty Bank All-Time High 62,324.55
Resolution: 1080×1920, 30fps, 45s = 1350 frames
Encode: libx264 -preset slow -crf 8 -maxrate 10M -bufsize 20M
"""

import asyncio, os, subprocess, sys, json

FRAMES_DIR  = "/tmp/claude-0/-home-claude-finpulse-reels/6a39632b-1106-5823-937a-c43001484702/scratchpad/eve_frames_1117"
HTML_SRC    = "/home/claude/finpulse-reels/2026-11-17/evening-niftybank-reel.html"
MUSIC_FILE  = "/home/claude/finpulse-reels/music/nastelbom-soft-corporate-485896.mp3"
OUTPUT_MP4  = "/home/claude/finpulse-reels/2026-11-17/evening-niftybank.mp4"
COVER_PNG   = "/tmp/claude-0/-home-claude-finpulse-reels/6a39632b-1106-5823-937a-c43001484702/scratchpad/eve_cover_1117.png"
COVER_JPG   = "/home/claude/finpulse-reels/2026-11-17/evening-niftybank-cover.jpg"

FPS       = 30
DURATION  = 45
N_FRAMES  = FPS * DURATION   # 1350
W, H      = 1080, 1920
COVER_T   = 3.5              # S1 after flip: shows 62,324 ALL-TIME HIGH

os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(os.path.dirname(COVER_PNG), exist_ok=True)

async def render_frames():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--disable-web-security"])
        ctx     = await browser.new_context(viewport={"width": W, "height": H},
                                             device_scale_factor=1)
        page    = await ctx.new_page()
        file_url = "file://" + HTML_SRC
        await page.goto(file_url, wait_until="networkidle")
        await page.wait_for_timeout(400)

        total = N_FRAMES
        for fi in range(total):
            t    = fi / FPS
            await page.evaluate(f"setT({t:.4f})")
            path = os.path.join(FRAMES_DIR, f"f{fi:05d}.png")
            await page.screenshot(path=path, type="png",
                                   clip={"x":0,"y":0,"width":W,"height":H})
            if fi % 150 == 0:
                print(f"  frame {fi}/{total}  t={t:.2f}s", flush=True)

        # cover frame
        await page.evaluate(f"setT({COVER_T:.4f})")
        await page.screenshot(path=COVER_PNG, type="png",
                               clip={"x":0,"y":0,"width":W,"height":H})
        await browser.close()
    print("✓ Frames rendered", flush=True)


def encode(two_pass=False):
    pat  = os.path.join(FRAMES_DIR, "f%05d.png")
    if two_pass:
        cmd1 = ["ffmpeg","-y",
                "-framerate",str(FPS),"-i",pat,
                "-i",MUSIC_FILE,
                "-c:v","libx264","-preset","slow","-b:v","6M",
                "-maxrate","10M","-bufsize","20M",
                "-pix_fmt","yuv420p",
                "-pass","1","-an","-f","null","/dev/null"]
        cmd2 = ["ffmpeg","-y",
                "-framerate",str(FPS),"-i",pat,
                "-i",MUSIC_FILE,
                "-c:v","libx264","-preset","slow","-b:v","6M",
                "-maxrate","10M","-bufsize","20M",
                "-pix_fmt","yuv420p",
                "-pass","2",
                "-c:a","aac","-b:a","192k","-shortest",
                "-movflags","+faststart",
                OUTPUT_MP4]
        print("2-pass encoding …", flush=True)
        subprocess.run(cmd1, check=True)
        subprocess.run(cmd2, check=True)
    else:
        cmd = ["ffmpeg","-y",
               "-framerate",str(FPS),"-i",pat,
               "-i",MUSIC_FILE,
               "-c:v","libx264","-preset","slow","-crf","8",
               "-maxrate","10M","-bufsize","20M",
               "-pix_fmt","yuv420p",
               "-c:a","aac","-b:a","192k","-shortest",
               "-movflags","+faststart",
               OUTPUT_MP4]
        print("Single-pass CRF=8 encoding …", flush=True)
        subprocess.run(cmd, check=True)
    print("✓ Video encoded", flush=True)


def make_cover():
    subprocess.run(["ffmpeg","-y","-i",COVER_PNG,
                    "-vf","scale=1080:1920",
                    "-q:v","2",COVER_JPG], check=True)
    print("✓ Cover JPEG created", flush=True)


def verify():
    r = subprocess.run(
        ["ffprobe","-v","quiet","-print_format","json",
         "-show_streams","-show_format",OUTPUT_MP4],
        capture_output=True, text=True, check=True)
    info = json.loads(r.stdout)
    fmt  = info["format"]
    bps  = int(fmt.get("bit_rate","0"))
    dur  = float(fmt.get("duration","0"))
    vs   = next(s for s in info["streams"] if s["codec_type"]=="video")
    w,h  = int(vs["width"]), int(vs["height"])
    print(f"  bitrate: {bps/1e6:.2f} Mbps  dur: {dur:.1f}s  res: {w}×{h}", flush=True)
    if bps < 4_000_000:
        raise RuntimeError(f"Bitrate {bps/1e6:.2f} Mbps < 4 Mbps threshold")
    if abs(dur-45) > 1.5:
        raise RuntimeError(f"Duration {dur:.1f}s outside expected range")
    if w != 1080 or h != 1920:
        raise RuntimeError(f"Resolution {w}×{h} != 1080×1920")
    print("✓ Quality check passed", flush=True)
    return bps


async def main():
    print("=== Fin Pulse Evening Reel Render 2026-11-17 ===", flush=True)
    # 1) render frames
    await render_frames()
    # 2) encode (CRF first; fall back to 2-pass if bitrate check fails)
    try:
        encode(two_pass=False)
        bps = verify()
    except RuntimeError as e:
        print(f"CRF pass failed ({e}), retrying 2-pass …", flush=True)
        encode(two_pass=True)
        bps = verify()
    # 3) cover
    make_cover()
    print(f"\n=== DONE  bitrate={bps/1e6:.2f}Mbps ===", flush=True)


if __name__ == "__main__":
    asyncio.run(main())

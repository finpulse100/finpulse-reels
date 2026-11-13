#!/usr/bin/env python3
"""Capture cover JPEG at T=2.0s for evening reel"""
import asyncio, subprocess, os

REPO  = "/home/claude/finpulse-reels"
HTML  = f"{REPO}/2026-11-13/evening-razorpay-ipo-reel.html"
COVER_PNG = f"{REPO}/2026-11-13/evening-razorpay-ipo-cover.png"
COVER_JPG = f"{REPO}/2026-11-13/evening-razorpay-ipo-cover.jpg"

async def capture():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=['--disable-web-security'])
        ctx = await browser.new_context(
            viewport={'width': 1080, 'height': 1920},
            device_scale_factor=2   # 2x for cover quality
        )
        page = await ctx.new_page()
        await page.goto(f"file://{HTML}", wait_until='networkidle')
        await page.wait_for_timeout(500)
        await page.evaluate('window.setT(2.0)')
        await page.wait_for_timeout(100)
        await page.screenshot(path=COVER_PNG,
                              clip={'x':0,'y':0,'width':1080,'height':1920})
        await browser.close()
    print(f"PNG saved: {COVER_PNG}")
    # Convert to JPEG
    result = subprocess.run(
        ['ffmpeg', '-y', '-i', COVER_PNG,
         '-vf', 'scale=1080:1920',
         '-q:v', '2',
         COVER_JPG],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("ffmpeg err:", result.stderr[-500:])
    else:
        size = os.path.getsize(COVER_JPG)
        print(f"JPEG saved: {COVER_JPG} ({size//1024}KB)")

asyncio.run(capture())

# Fin Pulse: daily automation playbook

## Schedule (IST, every day)
08:00 News 1 | 10:00 News 2 | 12:00 News 3 | 14:00 News 4 | 16:00 News 5 | 18:00 News 6

## Each run
1. Read https://pulse.zerodha.com/ (top stories). Only items from the last ~2 hours that were not already used today.
2. Score each item 1-5 on market impact, investor relevance, virality, public interest. Pick the top total. Weekends/holidays: favour RBI/SEBI policy, global events, IPO calendar, explainers.
3. Open the source article, confirm facts. Never invent figures. Skip rumours, single-source claims, anything contradictory.
4. Build the standard Fin Pulse reel (6 slides, 45 s, rules in fin-pulse-instructions.md).
5. Maker-checker: a second pass verifies every number against the source, layout/safe zone, audio levels, disclaimer, no copied headlines. Any fail = fix or skip the post and log why.
6. Publish with caption below. Log: time, headline, source, post id.

## Caption template
Line 1: hook (max 125 chars, shows before "more").
2-3 short lines of the key facts, own words.
"Source: <outlet>. Educational content, not investment advice."
5-8 hashtags: 3 broad (#StockMarket #Nifty50 #IndianStockMarket), 3-5 specific to the story.
Title (YouTube Shorts): <=60 chars, keyword first, add #Shorts.

## Posting time
Publish about 10-15 minutes after each pick (video build time). Fixed slots are driven by the news cycle; review analytics after 2 weeks and adjust.

## Blockers
- Public video URL needed for Instagram publishing.
- YouTube not yet connected.
- Music MP3s and reel template must be available to scheduled runs.

## Lessons from the first live demo (10 Nov 2026)

- **Instagram crop (must do every time):** on the Crop step click the crop icon bottom-left and choose **9:16** (default is 1:1 and cuts the top and bottom). After sharing, open the reel and check the video is 720x1280 (javascript: `document.querySelector('video').videoWidth/videoHeight`). The user will not check this, so the run must.
- Read pulse.zerodha.com in the user's Chrome (get_page_text). The page-fetch tool returned a stale copy from two weeks earlier.
- Pick the story that links to Indian investors. Confirm numbers in the source article before building.
- Rendering takes about 6 minutes (6 scenes, 2 workers) plus about 1 minute for audio. Do NOT shrink the video for the cloud route: deliver the full HD master (1080x1920, crf 12, maxrate 10M, 15 to 35 MB). The old crf 24 / 2300k / 720p copy was only for the browser upload tool and caused blurry text.
- Instagram: Create > Post > upload file > choose cover (upload the hook frame) > caption > Share. Takes about 20 s to share.
- YouTube: upload in Studio, set title, description, "not made for kids", visibility Public. Wait for "Checks complete" (about 5 min) before Publish; do not publish over the warning.
- Sound effects: whoosh 2.3, swish 1.1, pop 1.4, land 0.9, tick 1.3, chime 1.5 gains gave 5.4 dB or more over the music.
- Posted: Instagram reel and YouTube Short (https://youtube.com/shorts/3Z-ncOJbM90).

## Cloud posting route (no computer needed) — set up 10 Nov 2026
- GitHub repo `finpulse100/finpulse-reels` (public) holds each day's video and cover. Claude GitHub App is installed on it, so a cloud session can push.
- Each run: FIRST load the tools with ToolSearch `select:mcp__claude-code-remote__add_repo,mcp__claude-code-remote__register_repo_root` (they are deferred; the 10 Nov 8:00 run failed with a 403 push because it never called add_repo), then `add_repo` (owner finpulse100, repo finpulse-reels, access push) -> `git clone --depth 1 https://github.com/finpulse100/finpulse-reels /home/claude/finpulse-reels` (generous timeout) -> copy the HD video (9:16, 1080x1920, crf 12, under 60 MB) as `YYYY-MM-DD/slot-N-<topic>.mp4` plus a JPEG cover (`...-cover.jpg`) -> `git add`, commit, `git fetch origin main`, push to main.
- Public URL: `https://raw.githubusercontent.com/finpulse100/finpulse-reels/main/<path>` (the cloud shell cannot fetch it itself — 403 from the proxy — but Instagram can).
- Instagram: Windsor MCP `execute_action` connector `instagram`, action `create_video_post`, account `17841478153972348`, params `video_url`, `cover_url`, `caption`. Windsor posts the file as-is (no crop step), so a 9:16 file gives a full-frame reel. Verified 10 Nov 2026 with a 720x1280 test file; use the 1080x1920 HD file from now on and confirm the Instagram reel stays full-frame. No Chrome needed.
- YouTube: Windsor has no YouTube upload action. Upload through Chrome (computer on) if reachable; otherwise save the title/description/tags in the posting package and say YouTube is pending.
- Do not delete old files from the repo; it is the public storage.

## YouTube route (no computer needed) — set up 10 Nov 2026
- Channels: the NEW Fin Pulse channel (handle @Finpulsemarket, id UC7YVs8onoPnPlbfr2sIs0YQ) is owned by the Google account fin.pulse100@gmail.com. The OLD channel (renamed "Fin Pulse Old", @finpulseold, with the earlier MelodyUntold videos) is on another Google account. @finpulsemarkets is held for 14 days after the rename, so the new channel uses @Finpulsemarket for now; switch the handle after the hold ends if wanted (name can be changed twice per 14 days).
- Windsor has no YouTube upload action, so a Make.com scenario does it: "Publish Latest Reels to YouTube" (scenario 6969426, us2.make.com, free plan, active). It runs at 08:30, 10:30, 12:30, 14:30, 16:30, 18:30 IST daily and reads `youtube/latest.json` from the repo (raw URL), parses it, and if `posted_at` is under 119 minutes old downloads `video_url` and uploads it to the new Fin Pulse channel as Public, category News & Politics, not made for kids.
- Each daily run must, as its LAST step (after mp4 push and Instagram post), overwrite `youtube/latest.json` with: `{"posted_at": "YYYY-MM-DDTHH:MM:SSZ" (UTC from date -u), "video_url": raw URL of the mp4, "title": "<100 chars, ends #Shorts, no < or >", "description": "plain text, hashtags, Not financial advice", "tags": "comma,separated"}`, then fetch, commit and push to main. Never leave a stale posted_at (it would re-upload an old video).
- Make connection used now: 12241356 ("Finance's YouTube connection", Google account fin.pulse100@gmail.com = owner of the new channel). The other connection 12241317 (Raj.Dineshsharma2020 account) posts to the old channel. If uploads fail with 401/403, redo the YouTube connection in Make with all permission boxes ticked.
- Tested 10 Nov 2026 on the new channel with a ~10 MB reel (uploaded Unlisted, test video can be deleted by the user). Make free plan: 1000 operations a month; each poll costs 2-4 operations, about 700 a month.

## Repo storage rule (HD files are large)
- Each HD reel is roughly 15 to 35 MB, so six a day adds up fast on GitHub (soft limit about 1 GB). On the 8:00 AM run only (slot 1): `git rm -r` every day folder older than 2 days and push in a normal commit (no force-push: unattended force-push is blocked). The history squash is done manually by the owner's interactive session about once a week. Never delete `youtube/latest.json` or today's folder.
- Make downloads the file at its poll time; Instagram fetches it at post time. Both finish within about 2 hours, so 2 days of files is plenty.
- OPEN CHECK: confirm Make's free plan can download a 20 to 35 MB file (9.9 MB worked). If an HD upload fails in Make, tell the user; do not shrink the Instagram copy. A smaller YouTube-only copy (`...-yt.mp4`, still 1080x1920, crf 20, maxrate 5M) is the fallback for `video_url`.

## Music tracks (cloud runs)
The 7 supplied Pixabay MP3s are stored in the GitHub repo finpulse100/finpulse-reels under `music/` (pushed 2026-11-10). Cloud runs clone the repo and pick a track from `music/` (use only these 7; vary the track by slot). Never delete the `music/` folder in the cleanup step,.

# Video Studio on your own Mac (setup for a friend)

You get your own copy of Video Studio, on **your** Mac, with **your** login, **your** web address
(`https://video-studio.<your-tailnet>.ts.net`), **your** GitHub repository and **your** presenter character.
Your renders use your Mac, never Varun's. Cost: Rs 0.

**You need:** a MacBook with Apple Silicon (M1 or newer, 16 GB RAM recommended; tested on an M5 Air 16 GB),
macOS up to date, about **20 GB free disk**, a GitHub account, about 1 hour for setup (mostly downloads), and
later about 2-2.5 hours (unattended, plugged in) to build your character.

What is NOT in the code, and what you make yourself:
- **Music and sound effects** (`assets/audio/`): licensed, so you download your own (step 7).
- **Character packs** (`assets/characters/<name>/` images, ~140 MB each): you generate your own (step 8).
  Only each pack's `pack.json` and `contact_sheet.jpg` are in git.
- Your `.env`, your logins (`data/`), your videos (`output/`). These stay on your Mac.

---

## 1. Get access to the code (5 min)
Make a free GitHub account at https://github.com if you don't have one (step 4 puts your own copy there).
The code is public (github.com/varunreddy033/video-studio), so anyone can clone it; no invite needed.

## 2. Install the basic tools (15 min)
Open the **Terminal** app (Cmd+Space, type "Terminal") and run these one at a time.

Homebrew (the Mac package installer). It asks for your Mac password once; nothing shows while you type:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
At the end it prints two "Next steps" lines starting with `echo` and `eval`. Copy and run them, then:
```bash
brew install git gh python@3.11 tailscale
```

## 3. Download Video Studio (2 min)
```bash
gh auth login --hostname github.com --git-protocol https --web
```
Press Enter at each question, then open the link it shows, paste the code, and click **Authorize**. Then:
```bash
git clone https://github.com/varunreddy033/video-studio ~/youtube-pipeline
```

## 4. Make it YOUR repository (5 min, do this before anything else)
Right now the copy points at Varun's public repository. Point it at your own, so you never push to his:
```bash
cd ~/youtube-pipeline
git remote rename origin upstream
git remote set-url --push upstream DISABLED
gh repo create youtube-pipeline --private --source=. --remote=origin
git push -u origin main
git remote -v
```
`git remote -v` must now show **origin** = `github.com/<your-username>/youtube-pipeline` (fetch and push) and
**upstream** = Varun's repo with push `DISABLED` (a push to it fails instead of reaching his code).

Then change the git rule at the top of `CLAUDE.md` (Claude Code reads it and pushes after every change), so it
points at your repo. Replace `YOUR-USERNAME` with your GitHub username:
```bash
cd ~/youtube-pipeline
sed -i '' "s#github.com/varunreddy033/youtube-pipeline#github.com/YOUR-USERNAME/youtube-pipeline#" CLAUDE.md
grep -n "YOUR-USERNAME\|github.com/" CLAUDE.md
```
The `grep` must show your username in the "Git (DECIDED ...)" line. That rule also tells Claude Code to run
`tools/publish_public.py`, which publishes to Varun's public repo: open `CLAUDE.md` and delete the sentences from
"Then run `bin/python tools/publish_public.py`" to the end of the line that mentions .publicignore (you only have
one repo; the script can't push to Varun's repo anyway). Then:
```bash
git commit -am "My own repo in the git rule" && git push
``` The rest of `CLAUDE.md` describes Varun's
Mac and accounts: the first time you open Claude Code in this folder, ask it to update the "Machine",
"Accounts / keys" and "Current status" sections for you.

## 5. Install everything Video Studio needs (30-45 min, mostly downloading)
```bash
bash ~/youtube-pipeline/setup.sh
```
This makes the Python environment and installs FFmpeg (full version), espeak-ng, whisper.cpp, the voice model,
the caption model (~470 MB), the image model (FLUX.2 klein 4B, ~4.6 GB, Apache-2.0 licence), and the presenter
libraries: rembg (cuts your character out of each pose) and transformers + OpenCV (Depth Anything V2 Small, the
2.5D camera moves). It is safe to run again if your internet drops. The last check lists each library with
`ok:`, then **SETUP DONE**. (The first pack build downloads rembg's u2net model, ~170 MB, and the first final
downloads Depth Anything V2 Small, ~100 MB.)

## 6. Keep the Mac awake (2 min, important)
Long jobs (a character pack, a 10-minute final) stop completely if the Mac sleeps. On battery with the lid
closed it sleeps, and that cost Varun 6 hours once.
- **Always plugged in, lid open** for packs and finals.
- System Settings -> Battery -> Options -> turn ON **"Prevent automatic sleeping on power adapter when the
  display is off"**.
- Step 10's auto-start runs Video Studio under `caffeinate -is`, which keeps the Mac awake while it's plugged in.
- Running a long command by hand? Put `caffeinate -is` in front of it (as in step 8).

## 7. Add music and sound effects (10 min)
Not in the code (licensed). Download them yourself, free, from the **YouTube Audio Library**
(YouTube Studio -> Audio Library). Put:
- music tracks (at least 60 seconds long) in `~/youtube-pipeline/assets/audio/bgm/`
- short sound effects in `~/youtube-pipeline/assets/audio/sfx/` with the sound in the file name
  (for example `whoosh-fast.mp3`, `typing-on-keyboard.mp3`, `riser-tension.mp3`)

A script's `music:` line matches words in these file names, so use a track's name (e.g. `music: soaring`).

## 8. Pick and build your presenter character (~2-2.5 h, unattended)
Videos are presented by a cartoon character who talks to camera (lip-synced) and acts out the story.
**Sterling (the grey cat in a navy blazer) is Varun's channel brand: don't use him.** Pick one of these, or
write your own:

| File | Character | Voice | Sets | Extra |
|---|---|---|---|---|
| `docs/characters/miso.md` | Miso, a smart ginger kitten with gold glasses and a mustard sweater vest | bm_fable | den, stage | calm money/tech explainer |
| `docs/characters/biscuit.md` | Biscuit, a golden retriever puppy in a red hoodie | am_puck | studio, stage | pose "excited"; funny, energetic |
| `docs/characters/nova.md` | Nova, a cartoon brain in a lab coat | af_heart | lab, stage | pose "lightbulb"; science/AI |

**Your own character:** copy one of the files (e.g. `cp docs/characters/miso.md docs/characters/pixel.md`;
the file name is the character's id) and change:
- `CHARACTER = "..."`: what it looks like (species, colours, eyes, outfit). Give it 2-3 memorable details.
- `STYLE = "..."`, `SEED = <any number>`: the seed fixes the look; change it if you don't like the result.
- the body words `NOUN`, `LIMBS` (paws / hands), `FUR` (fur / skin...), `OUTFIT`, `EARS` (yes / no). The pose
  prompts use them ("one paw on its chin").
- `Voice: <kokoro voice>, speed <x>`, the `Poses:` line, and `Sets:` (`"name" (description)`). Don't put a
  person or the character's name in a set description (the model draws them into the empty set).

**Build the pack**, plugged in with the lid open:
```bash
cd ~/youtube-pipeline && caffeinate -is bin/python tools/make_character_pack.py miso
```
What it makes, and how long it takes on an M5 Air:
- master reference + 2 candidates per pose: ~15 min
- 6 mouth shapes + blink per pose, 2 tries each (~85-100 edits, 55-75 s each): ~1.5-2 h
- cut-outs (~1 min) and 2 candidates per set (~3 min)

It is **resumable**: every image is cached, so if it stops, run the same command again and it continues.
When it's done, open `assets/characters/miso/contact_sheet.jpg` and check every pose and mouth. To swap a pose
for its other candidate, write `assets/characters/miso/overrides.json`, e.g. `{"neutral": "master", "shrug": "A"}`,
and run the command again (only the changed parts are redone). If the master itself looks wrong, change `SEED`
and rebuild.

Then use it in scripts with `character: miso`. The script prompt (step 11) is written for Sterling: tell Claude
to use your character's name, lines (opening, sign-off), poses and set names from your character file instead.

## 9. Start it and create your login (2 min)
```bash
~/youtube-pipeline/bin/python ~/youtube-pipeline/render_server.py
```
It prints a line `FIRST RUN: create your login at http://localhost:8765/setup?code=...`.
Open that link in Safari or Chrome **on this Mac**, choose a username and a password (at least 10 characters),
and click **Create login**. Leave the Terminal window open.

## 10. Put it on the internet and start automatically (10 min, free)
In a **new** Terminal window (Cmd+T):
```bash
mkdir -p "$HOME/Library/Application Support/vs-tailscale"
tailscaled --tun=userspace-networking --statedir="$HOME/Library/Application Support/vs-tailscale" --socket="$HOME/Library/Application Support/vs-tailscale/tailscaled.sock" --port=0 &
tailscale --socket="$HOME/Library/Application Support/vs-tailscale/tailscaled.sock" up --hostname=video-studio --accept-dns=false
```
Open the link it prints and sign in (Google is easiest; this makes **your own** free Tailscale account). Then:
```bash
tailscale --socket="$HOME/Library/Application Support/vs-tailscale/tailscaled.sock" funnel --bg 8765
```
The first time, it prints a link: open it and click **Enable Funnel** (and enable HTTPS if asked). Run the same
command again; it prints your address, like `https://video-studio.tailXXXX.ts.net`.
A brand-new address can take up to 10 minutes to work. Open it on your phone to test.

So you don't have to repeat steps 9 and 10 after every restart (and so the Mac stays awake while plugged in):
```bash
bash ~/youtube-pipeline/tools/install_autostart.sh
```
Video Studio and the tunnel then start whenever you log in and restart if they crash.
To undo: `bash ~/youtube-pipeline/tools/install_autostart.sh remove`.

## 11. Make videos: two types
Open your address and log in. The page has two buttons:

**Make full video**: 16:9 1920×1080, 10-14 min, chapters, music that changes per chapter
(`music: soaring, misdirection, elysian`), 3 thumbnails.
Write the script with Claude using **Prompt to give Claude** on the page (prompt A = presenter, B = no presenter),
paste it, **Check**, **Save & make draft** (about a minute), then **Make final**. A 10-minute final takes about
20-40 minutes on an M5 Air (each new AI image ~25 s; re-renders reuse cached images).

**Make Short**: 9:16 1080×1920, 15 s to 2:00, one cover image, `#Shorts` in the description. Two ways:
- **From scratch**: paste a short script (prompt C). Mostly your character talking + graphics, so a 30-40 s
  Short takes about a minute.
- **From a video I already made**: pick a finished full video, set the start and end (chapter buttons,
  "Set to now", ▶ Preview), **Make Short**. It reuses that video's voice and images, re-frames it vertical with
  the character centred and re-makes the captions. No new AI images, about 40 s.

Every video is saved in `~/youtube-pipeline/output/jobs/<id>/` (final.mp4, thumbnails, metadata.txt,
upload_pack.zip). That folder isn't in git, so back up what you keep. Upload by hand in YouTube Studio.

## Getting updates from Varun
```bash
cd ~/youtube-pipeline && git pull upstream main && bash setup.sh && git push
```
then restart Video Studio: `launchctl kickstart -k gui/$(id -u)/com.videostudio.server` (or log out and in).
If git reports a conflict in `CLAUDE.md`, keep **your** git rule line (your repo URL); Claude Code can resolve
it for you if you ask.

## If something goes wrong
| Problem | Fix |
|---|---|
| `setup.sh` stops with an error | Run it again; it continues where it stopped. |
| `git push` says "DISABLED" | You tried to push to Varun's repo. Use `git push` (origin = yours); check `git remote -v`. |
| Final says "waiting for <name>'s character pack" | Build the pack (step 8); the final starts by itself when it's done. |
| Pack build stopped overnight | The Mac slept (step 6). Plug in, lid open, run the same command again; it resumes. |
| Address doesn't open | Is the Mac awake and online? Is Video Studio running (step 9 or 10)? |
| "Funnel is not enabled" | Open the link it prints and click Enable Funnel, then run the funnel command again. |
| Forgot your password | Delete `~/youtube-pipeline/data/users.json`, restart Video Studio, use the new FIRST RUN link (`output/server.log`). |
| Mac very hot / slow | Normal for AI images on a fanless Air; close other big apps, keep it plugged in. |

**Keep private:** your `.env`, the `data/` folder (logins), and never share your Video Studio password.

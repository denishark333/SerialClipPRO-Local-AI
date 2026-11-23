# Serial ClipPRO

**English** | [Português](README.pt-BR.md)

<img width="1920" height="1045" alt="image" src="https://github.com/user-attachments/assets/4de74f11-5c49-43de-a4cd-ec6592ea3d06" />

**Your stream lives on in every clip.**

Long streams and no time to edit? Serial ClipPRO analyzes your VODs and prepares vertical clips while you are away from your PC. Then you review them and choose what to post.

This repository holds the source code, the installer packages and the public releases of the Windows app.

## Download

Go to **Releases** in this repository and download the installer attached to the version you want (`Serial-ClipPRO-3.0.1-Setup-x64.exe` for version 3.0.1). From 3.0.1 on, new versions can also be installed from inside the app (see [Updating](#updating)).

> Download the **Serial ClipPRO** installer. The automatic "Source code (zip)" and "Source code (tar.gz)" files contain the source code, not the ready-to-use app.

## What the app does

- Processes VODs from Twitch, YouTube and Kick, as well as local videos.
- Finds the best moments across the whole VOD with local AI, quoting the line that justifies each clip.
- Works with streams in many languages and of any genre; the **What to look for** field tells it which moments to prioritize.
- Creates vertical 9:16 clips with animated subtitles: the word being spoken is highlighted.
- Lets you adjust the webcam framing, choose which part of the content goes into the vertical clip, and add your channel's logo as a PNG.
- Offers a gallery to review, download, export and delete clips.
- Lets you review and fix the subtitles and the framing of each clip.
- Gathers shortcuts to the platforms so you can post manually.
- Interface in English or Portuguese, and updates from inside the app whenever you choose.

The AI helps with the selection. Review the clips and subtitles before posting.

## What's new in version 3.0.1

- **Update from inside the app:** the **Check for updates** button next to the version shows whether a new version exists and what changed, and installs it in one click. The app only checks when you ask and only updates if you want to. Each installer is verified by its digital signature before it runs, and videos, settings and your AI model are kept.
- **English interface:** a **PT | EN** switcher below the header translates the whole interface, including the processing messages. On first run, the language follows Windows.
- **Off-center vertical crop:** drag the frame to choose which part of the content appears in the clip, great for HUDs, chats or action away from the center.
- **Framing per clip:** in **Subtitle review**, fix the webcam or the crop of a single clip when the camera moved or changed size during the stream, without reprocessing the VOD and without changing the other clips.
- **AMD and Intel GPUs:** rendering now uses AMD AMF (tested on a Radeon GPU) and Intel QuickSync, besides NVIDIA NVENC, and falls back to the CPU when none is available. The model selector now also reads the video memory of AMD cards.
- **Clearer progress:** on long VODs, the progress bar moves while the audio is mapped and shows the point being read (e.g. "04:12:30 of 11:31:59"). The stream language is always visible next to **Advanced settings**, and the **AI Engine** card shows the AI model in use.

## What's new in version 3.0

- **Rebuilt curation:** clips that start and end on complete sentences, short moments expanded with the surrounding context, and the key line of each clip checked against the transcript.
- **Your choice of AI model:** Gemma 4 12B (recommended), Llama 3.1 8B (lightweight) and others; pick during installation and switch any time in the app.
- **Stream language** and **What to look for**, with ready-made presets for MMORPG, FPS, Just Chatting and Podcast.
- **Highlighted subtitles:** the word being spoken grows; the classic style is still available in the Channel branding tab.
- **Kick:** VODs with the new identifier work, and live stream links are refused with a hint to use the VOD instead.
- **Faster:** transcription on NVIDIA GPUs (optional during installation), and steps already done are reused when the same VOD is processed again.
- **Customizable installer:** you choose the models and NVIDIA acceleration, and setup runs inside the wizard with a progress bar.

## Installation and first run

1. Download the installer from **Releases** and run it.
2. On the **Components** page, choose:
   - **AI models:** select one or more. **Gemma 4 12B** is recommended (needs ~10 GB of video memory); **Llama 3.1 8B** is the lightest. If none is selected, Llama 3.1 is installed.
   - **NVIDIA acceleration (CUDA):** ~4x faster transcription on NVIDIA cards (528 MB download). Selected by default when an NVIDIA card is present.
   - The essential components (app, FFmpeg, Ollama, Whisper, WebView2 and curl_cffi) are always installed.
3. Wait for setup to finish: the bar shows each download and check.
4. If the **Ollama** welcome window appears, continue with **local use**. Cloud models are not needed.
5. When it finishes, open Serial ClipPRO from the installer or from the shortcut it created.

After that, just open the **Serial ClipPRO** shortcut. Other models can be installed later with `ollama pull model-name` and selected in **Getting Started**.

### During setup

- An internet connection is required.
- The models are several GB to download and need free disk space.
- Windows may ask for permission to install components.
- If the network fails, retry in the installer or use **Prepare or repair Serial ClipPRO** in the Start menu.
- If a restart is requested, restart the computer and use that same shortcut to finish.
- Setting up Whisper may take a few minutes.

Python and Node.js do not need to be installed on the target computer.

## First test

Start with a short video before processing a long VOD:

1. Enter a VOD link (Twitch, Kick or YouTube) or select a local file. Streams that are still live are not accepted.
2. Choose the analysis mode and, under **Advanced settings**, the stream language.
3. Adjust the framing and branding if you want.
4. Start processing.
5. Review the videos in the gallery and export your favorites.

Keep the computer on and prevent it from sleeping while processing.

## Analysis modes

| Mode | How it works |
|---|---|
| **Hybrid** | Combines audio peaks with samples spread across the whole VOD. Recommended for long streams. |
| **Audio peaks** | Evaluates every one of the most intense moments of the VOD and keeps the highest-scoring ones. |
| **Full context** | Transcribes and analyzes the entire source, which takes longer to process. |

In all three modes, clips are picked by score across the whole VOD, not by the order in which they appear. No mode is guaranteed to find every interesting moment. Processing time depends on the VOD length, the connection, the hardware and the chosen settings.

## Local processing and hardware

Transcription and AI analysis use **Whisper and Ollama on your computer**.

- With **NVIDIA acceleration** installed, Whisper transcribes on the GPU; without it, or without an NVIDIA card, it uses the CPU.
- The curation AI model runs in Ollama; Gemma 4 12B needs ~10 GB of video memory to run fully on the card.
- Rendering tries NVIDIA NVENC, then AMD AMF, then Intel QuickSync and, if none is available, the CPU.
- The model selector in **Getting Started** checks the video memory of NVIDIA and AMD cards to recommend a model.

Local processing still needs the internet to download models, access VODs and open the social platforms.

## Where are the files?

The program is installed in `%LOCALAPPDATA%\Programs\Serial ClipPRO\`. Your data is kept separately in:

`%LOCALAPPDATA%\Serial ClipPRO\`

Paste this path into the File Explorer address bar.

| Folder | Contents |
|---|---|
| `Cortes_Prontos` | Videos shown in the gallery. |
| `Cortes_Exportados` | Copies of clips exported in bulk. |
| `transcricoes` | Cache of transcripts, samples, audio maps and curation. |
| `relatorios_curadoria` | Analysis reports. |
| `cache_revisao` | Source files for reviewing clip subtitles. |
| `marca` | Channel logo image and its settings. |
| `logs` | Diagnostic logs. |
| `tools` | FFmpeg and, if installed, NVIDIA acceleration. |
| `atualizacao` | Installer downloaded by the in-app updater; deleted automatically after the update. |

Deleting a clip from the gallery does not delete copies already exported. The **Download** button lets you choose where to save a single video.

## Social media

The Social tab gathers shortcuts to Instagram, TikTok, YouTube, Twitch and Kick. BiliBili shows up as **Coming soon**.

Logging in and posting are done manually on the platforms' websites. The app does not post automatically.

If a platform refuses to log in inside the built-in window, use **Open in browser**.

## Updating

**From inside the app (3.0.1 and later):**

1. Click **Check for updates**, next to the version at the top of the app.
2. If there is a new version, read what changed and click **Download update**.
3. When the download is verified, click **Install now**. The app closes, the installer shows its progress and Serial ClipPRO reopens on its own.

Nothing is checked or installed without your click. Installing is blocked while a clip is being processed, reviewed or previewed.

**Manually (needed once to go from 3.0.0 to 3.0.1):**

1. Wait for processing to finish and close the app.
2. Download the new version's installer from **Releases**.
3. Run the installer.

Updates replace the previous version in place (one installation, one shortcut) and keep your videos, settings and models. Check the Release notes for any version-specific instructions.

## Issues and suggestions

The project is under development. To report a problem, open an **Issue** in this repository and include:

- Serial ClipPRO version.
- Windows version, processor, RAM and GPU.
- Video source and analysis mode used.
- The step where the problem happened.
- The error message and, if possible, a screenshot.

For installation problems, check:

`%LOCALAPPDATA%\Serial ClipPRO\instalacao.log`

For problems updating from inside the app, also check `%LOCALAPPDATA%\Serial ClipPRO\logs\atualizacao.log`.

Review logs before posting them and remove personal information, tokens or private URLs.

## Support the project

If Serial ClipPRO helps your routine, you can support its development:

- [Support via PayPal](https://www.paypal.com/donate/?business=6KXEQHVYHLLQ8&no_recurring=0&item_name=Host%2FVPS&currency_code=BRL)
- [Support via Pix — LivePix](https://livepix.gg/serialhealer) (Brazil)

Support is voluntary.

---

# Development

A local app that turns files and VODs from Twitch, YouTube and Kick into vertical clips. React interface, FastAPI API, yt-dlp, FFmpeg, faster-whisper and Ollama.

## Running from source

Development requires Python and Node; processing requires FFmpeg/ffprobe on the PATH and Ollama with at least one model (`llama3.1` by default; `gemma4:12b` recommended). With an NVIDIA card, install `nvidia-cublas-cu12` in the environment to transcribe on the GPU.

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
venv\Scripts\python.exe main.py
```

Open http://127.0.0.1:8765. For development with hot reload, keep the backend running and run `npm run dev` in `frontend`; open the URL Vite shows. Under **File**, click **Choose video** to open the Windows file picker (also in local browser mode); the video is used in place, with no upload or copy. Under **Link**, paste the URL into the text field.

Closing the browser tab does not stop the server. To stop it, press **Ctrl+C in the terminal running `main.py`** and wait for the prompt to return before starting again. Shutdown asks the pipeline to cancel and waits for tasks to finish; model calls may take a while to respond. If the port is busy, startup reports the conflict without opening another tab. On desktop, close the window after processing finishes or is cancelled; reviews and previews also block closing while they are running. Force-quitting from Task Manager does not guarantee that subprocesses and temporary files are cleaned up.

## Installer - Windows x64

Distribution uses a single `Serial-ClipPRO-3.0.1-Setup-x64.exe` (Inno Setup). The components page shows the essential components (fixed) and the options: AI models and NVIDIA acceleration. After copying the files, the wizard runs `bootstrap.ps1` without a console, with `-Modelos` and `-Gpu`; the script emits `@@PROGRESSO|pct|message` lines, which the wizard uses for its progress bar.

- Models are downloaded through the Ollama API; if Ollama is too old for a model, it is updated and the download is retried. The strongest of the chosen models becomes the curation model (`config_ia.json`).
- NVIDIA acceleration downloads the official `nvidia-cublas-cu12` package from PyPI (pinned SHA256) and extracts only `cublas64_12.dll` and `cublasLt64_12.dll` into `tools/cuda`; CTranslate2 already ships cuDNN.
- The **Prepare or repair** shortcut runs the same setup; with no choice made, it keeps the model already configured.

The program lives in `%LOCALAPPDATA%/Programs/Serial ClipPRO/`, separate from the data in `%LOCALAPPDATA%/Serial ClipPRO/`. Updates and uninstalling keep videos, settings and models. Close the app after operations finish or are cancelled before updating.

To build, prepare a stable x64 Python environment named `build-env`, install `requirements-build.lock.txt`, install Inno Setup and run `scripts/build_installer.ps1`. The output, its SHA256 and its signature (`.sig`) go to `dist/installer/`. Each public release needs to be validated on a clean Windows install first.

### In-app updates

The **Check for updates** button queries the latest GitHub Release (`/api/atualizacao/*`, `core/atualizacao.py`) only when the user clicks it. The installer is downloaded to `atualizacao/` in the data folder and accepted only with a valid Ed25519 signature over its version, file name and SHA-256; the public key is embedded in the app. After the download, a hidden PowerShell waits for the app process to exit and runs the installer with `/SILENT /ATUALIZACAO=1`. In that mode the installer reopens the app at the end and runs `bootstrap.ps1` as a repair (without `-Modelos`), so the model chosen in the app is kept. Every installation deletes `_internal` before copying, so no libraries from the previous version are left behind. The new version deletes the downloaded installer when it opens.

Each Release (tag `vX.Y.Z`) must attach the installer **and** its `.sig`; without the signature, the app sends the user to the Release page. `build_installer.ps1` signs with the private key from `CLIPPRO_CHAVE_ATUALIZACAO` or `%USERPROFILE%\.serialclippro\chave-atualizacao.pem`, which never goes into the repository (`scripts/chave_atualizacao.py gerar` creates the key pair; `-SemAssinatura` skips signing for local tests only).

The installer verifies the signatures of the Microsoft/Ollama installers and the SHA256 of FFmpeg and the NVIDIA package. It does not change Defender exclusions or turn Defender off. It writes diagnostics to `instalacao.log`, `self-test.json` and `models-setup.json` in the data folder.

The desktop app blocks closing while the pipeline is running: cancel and wait before closing. A second desktop instance using the same data folder is refused. `CLIPPRO_DATA_DIR` lets you choose a different data directory; in development, data lives in the project root.

## Modes and cost

- **Hybrid:** scans the audio and combines peaks with time coverage. Up to 40 samples of 90 seconds by default (60 minutes of audio to transcribe). It can miss events outside the samples. The sample limit is separate from the limit on generated clips.
- **Peaks:** one sample per audio peak; all of them are evaluated and clips are picked by score.
- **Full context:** prepares and transcribes the whole source in chunks; costs more CPU and media reading.

The scan covers the whole source, even without saving the full VOD; ffmpeg writes its position with `-progress`, and the bar moves from 15% to 25% while the scan runs. On Twitch, analysis uses the audio-only variant; on Kick, the lowest video quality (same audio). The audio map, transcribed samples and evaluated chunks are cached: running the same VOD again only redoes what changed (the map is rebuilt if the VOD grew).

Curation sends each chunk to the configured model along with the stream language and the priorities from the **What to look for** field. The response follows a JSON schema; each moment's key line is checked against the transcript, short moments are expanded with the neighboring speech, adjacent candidates are merged and boundaries are snapped to complete sentences and pauses. If the AI approves nothing, the app suggests segments for review based on neutral signals (provided terms and focus, exclamations, questions, repetition, fast speech).

Final rendering and subtitle review try NVIDIA NVENC, then AMD AMF (`h264_amf`), then Intel QuickSync (`h264_qsv`) and, if all of them fail, the CPU with libx264; an encoder that fails is not retried during the session. Audio is normalized in two passes to -14 LUFS. The Ollama/Whisper steps check for cancellation at the available points; not every call is interrupted instantly.

Before preparing the media, the pipeline checks that Ollama responds and that the configured model is installed. Technical failures are not presented as editorial rejection; only chunks that were never evaluated make the curation partial.

## Studio and branding

The studio preview is taken from the **middle of the VOD** (10 seconds), where the stream is usually in progress with the webcam visible. When the duration is unknown, it uses 30:00 on Twitch and minute 1 for other sources.

Framing uses percentages of the original image. The preview follows the source's aspect ratio, the magnifier follows the selected area, and older presets are not rewritten automatically. Resizing keeps 16:9; an old preset may have a different aspect ratio.

In the **Channel branding** tab, upload a PNG (up to 5 MB, 4096 pixels per side), adjust size/position and save. It can be a logo or transparent text with the channel address. Automatic positioning follows the webcam/content split; without a webcam, the configured vertical position applies. The simulation shows a 16:9 webcam, not the actual rendered video. Each new run gets a stable copy of the logo; videos already generated are not changed.

Uploading a PNG turns branding on automatically. For an image that is already saved but turned off, check **Apply branding to clips** and save. Unchecking and saving turns it off. The terminal reports the branding state at the start of each run.

With studio mode on, the webcam takes an area above the content without covering it. The content fills the whole area below, keeping the aspect ratio and cutting the sides when needed, with no padding bars. Without a webcam, the content fills the whole vertical clip. In both cases, **Content position** (or dragging the **Vertical clip** frame over the preview) chooses which part of the image is kept, from left (0%) to right (100%); the default is the center (50%).

Subtitles use Bangers in yellow, in groups of up to 5 words, breaking on pauses and sentence endings. In the **Highlight** style (default), the word being spoken is 22% larger; in **Classic**, the whole phrase appears at once. The style is chosen in the Channel branding tab and also applies to the review. Timings come from the transcript; this presentation does not fix recognition or sync errors.

## Optional subtitle review (beta)

The gallery and the review use the same ordering: most recent runs first, and the clip's original number in ascending order within each run. Edits do not change this order and deletions do not renumber the rest. The review opens on the list of saved clips; files that exist only in Exports are in a separate filter (**Only in Exports**). The cards show the run identifier to tell apart equal numbers from different sessions.

The **Subtitle review** tab and the card below **Hardware & Folders** let you open clips that have a review source available. The modal shows the horizontal original so you can hear the speech and edit the groups by start/end in seconds. You can fix text and add or delete groups; timings must be in order with no overlap. The overlay on the player is only an editing preview.

**Framing for this clip**, below the player, opens the same framing editor as Studio Mode over that clip's original: turn the webcam on or off, move or resize it, and change the content position. The change applies only to that clip and is saved in its review source after a successful render; the Studio Mode default does not change.

**Apply and generate corrected clip** redoes only the vertical composition, branding and subtitles, using the settings saved for that run (or the clip's new framing). Once the video is validated, it replaces the saved clip. Exported copies are left untouched: export again to update them. If rendering fails, the previous video stays available.

Review sources live in `cache_revisao/<unique id>/`: the horizontal original, the run's logo and a JSON file with the session, final video, framing and subtitles. New pipelines only use their own temporary files and do not remove these sources. Clips created before this change show up without a review source.

**Clear cache**, on the right side of the tabs, shows the space and number of sources before you confirm. It removes only the review sources, keeping transcripts, final clips and exports. The pipeline, applying a review and clearing the cache cannot run at the same time. The cache stays until you clear it manually and takes up extra space.

When a review is applied, unedited phrases keep each word's real timing; in edited phrases and older sources, timing is estimated from each word's length.

Whisper **Small** is used in all three modes, on the NVIDIA GPU when available and on the CPU otherwise. The first run may download the model.

## Gallery and desktop

In the gallery, deleting releases the players before removing the files. The result separates clips that were deleted, missing and locked; copies in `Cortes_Exportados` are kept.

On desktop, **Download** opens the native "Save as" dialog and copies the clip to the chosen location. Bulk export still uses `Cortes_Exportados` and shows that folder in the result dialog. The Pix and PayPal support buttons are in the header and open their pages in the default browser.

On desktop, "Open site" in the Social tab opens a separate WebView2 window of the same app; in the browser, it opens another tab. Sessions are stored in the local WebView2 profile, and these windows do not get the Python bridge of the main interface.

## Folders and API

- `core/`: analysis, transcription, selection, composition, branding and execution.
- `api/`: routes, validation, branding and dependency diagnostics.
- `frontend/src/`: React interface.
- `desktop.py`: WebView2 window; `main.py`: server for the browser.
- `Cortes_Prontos/`, `Cortes_Exportados/`: videos; exporting copies the MP4 files.
- `temp_clip_cache/`: previews and temporary files; `transcricoes/`: full cache.
- `relatorios_curadoria/`: decisions and timings; `marca/`: PNG/settings.
- `logs/`: desktop diagnostics. Old clips are not deleted when a new run starts.
- `atualizacao/`: installer downloaded by the updater, removed after the update.

Interface texts live in `frontend/src/i18n/` (`pt.js`, `en.js`); backend messages shown on screen live in `core/textos.py` and follow the interface language.

Main routes: `POST /api/iniciar-pipeline`, `POST /api/stop-pipeline`, `GET /api/status`, `GET /api/clips`, `POST /api/gerar-preview`, `GET/POST /api/studio-config`, `POST /api/exportar-selecionados`, `POST /api/deletar-selecionados`, `GET /api/relatorios-curadoria/{nome}`, `GET/PUT/DELETE /api/marca`, `GET/PUT /api/marca/imagem`, `GET /api/ambiente`, `GET/PUT /api/social`, `GET/PUT /api/ia`, `GET/PUT /api/interface`, `GET /api/atualizacao/verificar`, `GET /api/atualizacao/status`, `POST /api/atualizacao/{baixar,cancelar,instalar}`.

Pipeline parameters: `entrada`, `max_cortes`, `ignorar_inicio_segundos`, `modo_curadoria`, `termos_jogo`, `limite_amostras`, `idioma`, `foco`.

## Diagnostics

The executable accepts `--self-test`: it checks imports, the frontend, the WebView2 runtime, access to Kick (curl_cffi) and the updater's signature check without opening a window or downloading models, and writes `self-test.json` to the data folder. It does not validate window rendering or the full pipeline.

---

## License

Code under the [MIT](LICENSE) license: free to use, modify and redistribute, including commercially, as long as the copyright notice is kept. Third-party components remain under their own licenses; see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md). Parts of the curation and transcription were adapted from [AutoClip](https://github.com/artbyjazi/autoclip) by Jad Ghazi (MIT). The Bangers font is under the [SIL Open Font License](assets/fonts/Bangers/OFL.txt).

Developed by **SerialHealer**.

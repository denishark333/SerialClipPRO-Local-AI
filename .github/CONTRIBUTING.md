# Contributing to Serial ClipPRO

**English** | [Português](CONTRIBUTING.pt-BR.md)

Thank you for your interest in Serial ClipPRO! It is a free, open-source, local app, and contributions of every size are welcome: bug reports, ideas, translations, hardware tests and code.

By taking part, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

You can write in **English or Portuguese**. Both are welcome in Issues, Pull Requests and reviews.

## Ways to help

- **Report bugs** with enough detail to reproduce them (see below).
- **Suggest improvements** by explaining the problem you want solved, not only the solution.
- **Test on different hardware**, especially AMD and Intel GPUs, and report the results.
- **Try VODs from other platforms, languages and content types**, and tell us how curation and subtitles behaved.
- **Improve translations** of the interface (`frontend/src/i18n/`).
- **Send code**: fixes, performance work or features discussed in an Issue.

## Reporting a bug

Open an Issue using the **Bug report** form. It asks for:

- Serial ClipPRO version, Windows version, processor, RAM and GPU.
- The AI model used in Ollama.
- The video source (Twitch, YouTube, Kick or local file) and the analysis mode.
- The step where the problem happened and the error message, with a screenshot if possible.
- Relevant logs:
  - Installation: `%LOCALAPPDATA%\Serial ClipPRO\instalacao.log`
  - In-app updates: `%LOCALAPPDATA%\Serial ClipPRO\logs\atualizacao.log`

**Review logs before posting them** and remove personal information, tokens and private URLs.

Found a security problem? Please **do not** open a public Issue. Follow the [Security Policy](SECURITY.md) instead.

## Setting up the development environment

Requirements: Windows, Python, Node, FFmpeg/ffprobe on the PATH and [Ollama](https://ollama.com) with at least one model (`gemma4:12b` recommended). With an NVIDIA card, install `nvidia-cublas-cu12` in the environment to transcribe on the GPU.

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
venv\Scripts\python.exe main.py
```

Open http://127.0.0.1:8765. For hot reload, keep the backend running and run `npm run dev` in `frontend`. Restart `main.py` after changing backend code.

You can build your own installer with `scripts/build_installer.ps1 -SemAssinatura` (see the README's Development section). Official releases are signed by the maintainer, and the in-app updater only accepts installers with that signature.

## Pull Requests

1. **Open an Issue first** for anything bigger than a small fix, so we can agree on the approach before you spend time on it.
2. Fork the repository and create a branch from `main`.
3. **Keep each PR to one subject.** Small, focused PRs are reviewed faster.
4. Test your change in the running app with real media.
5. Before opening the PR, run in `frontend/`:
   ```powershell
   npm run lint
   npm run check:i18n
   npm run build
   ```
6. Fill in the Pull Request template.

The maintainer runs the project's internal test suite and tests the change in the app before merging. A PR may be accepted, sent back with requested changes, or declined with an explanation.

## Project rules

- **Interface text goes in both languages.** Never hardcode text in components: add the key to `frontend/src/i18n/pt.js` **and** `frontend/src/i18n/en.js`. `npm run check:i18n` checks that both match. User-facing backend messages go through `core/textos.py`.
- **No real third-party data.** Do not commit real VOD links, channel names, transcripts, user logs or footage you do not own. Use fictitious examples.
- **No local files.** Settings (`config_*.json`), generated clips, caches, logs and personal branding stay out of git. The `.gitignore` already covers them.
- **No secrets.** Never commit keys, tokens or `.env` files.
- **Keep it local.** Serial ClipPRO processes everything on the user's machine. Changes that send user data to external services will not be accepted.

## License

Serial ClipPRO is distributed under the [MIT License](../LICENSE). By contributing, you agree that your contributions will be licensed under the same license.

# project-fahm

A companion for reading and understanding the Quran — faithful Arabic text, English translations, tafsir commentary with AI-generated summaries, and cross-references between related verses.

## Core principles

- **Zero hallucination in Arabic text and translations.** These are bundled verbatim from authoritative sources and never generated, paraphrased, or touched by an AI model.
- **Tafsir summaries cite their source.** The AI only summarizes the provided tafsir text — it never adds facts from outside knowledge. Every summary shows the source and a toggle to view the verbatim original.
- **Fully open-source, no backend, no budget required.** Runs entirely in the browser. AI summarization uses an open model via WebGPU (no API keys needed).
- **Open-source, non-commercial distribution.**

## Tech stack

| Layer | Technology |
|-------|-----------|
| App | React + Vite + TypeScript |
| In-browser data | SQLite via sql.js (WASM) |
| AI summarization | WebLLM (open model, WebGPU, fully in-browser) |
| Arabic fonts | OFL (KFGQPC HAFS / Amiri) |
| Hosting | Cloudflare Pages (free) |

## Data sources

See [ATTRIBUTIONS.md](ATTRIBUTIONS.md) for full licensing details for all bundled data.

## Development

```bash
npm install
npm run dev
```

## Deployment

The app is hosted on [Cloudflare Pages](https://pages.cloudflare.com/). Pushes to `main` trigger an automatic build and deploy.

### One-time dashboard setup (manual)
1. Create a Cloudflare Pages project connected to `shosyed/project-fahm`
2. Set **build command**: `npm run build`
3. Set **output directory**: `dist`
4. Node version is read from `.nvmrc` automatically — no extra config needed

The `public/_headers` file is copied to `dist/_headers` by Vite, activating the required `Cross-Origin-Opener-Policy`, `Cross-Origin-Embedder-Policy`, and `Cross-Origin-Resource-Policy` headers (needed for WebGPU/SharedArrayBuffer used by the in-browser AI).

### What Cloudflare Pages builds
- `npm install` — installs all dependencies including `sql.js` and `@mlc-ai/web-llm`
- `npm run build` — TypeScript compile + Vite build; `viteStaticCopy` copies `sql-wasm.wasm` from `node_modules/sql.js/dist/` to `dist/`
- `quran.db` is committed to the repo and copied to `dist/` by Vite automatically

## Building the data assets

`quran.db` is committed to the repository at `public/quran.db` and does not need to be regenerated for a standard deploy.

Only re-run the pipeline if you want to update the Quranic data (e.g., after a new dataset version is available):

```bash
cd scripts
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python build_db.py        # rebuilds ayahs, translations, tafsirs
python build_crossrefs.py # rebuilds similar_ayahs, topics, themes
python verify_fidelity.py # spot-checks fidelity
# Then commit the updated public/quran.db
```

See `scripts/README.md` for full pipeline documentation.

## License

Source code: MIT — see [LICENSE](LICENSE).
Data assets: see [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

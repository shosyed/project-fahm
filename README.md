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

## Building the data assets

Data assets (quran.db, embeddings.bin) are generated offline and not committed to this repo. See `scripts/README.md` for instructions.

## License

Source code: MIT — see [LICENSE](LICENSE).
Data assets: see [ATTRIBUTIONS.md](ATTRIBUTIONS.md).

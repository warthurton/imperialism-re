# OCR of the manual and the quick reference card

The game folder has two PDFs: `Imperialism - manual.pdf` (120 pages, **has a text layer**, 38 embedded screenshots/art) and `Imperialism - quick reference card.pdf`
(6 pages, **image only**: each page is one 900x1035 picture, so it needs real OCR). `tools/ocr_pdf.py` turns them into Markdown with a vision model served by Ollama.

* **Set up once**: `python -m pip install --user pymupdf` (run the script with plain `python`, not `-I`, so the user site is found), and tell the script where Ollama is:
  `set OLLAMA_HOST=http://your-server:11434` (PowerShell: `$env:OLLAMA_HOST=...`) **or** create `tools/ocr.local.json` containing `{"host": "http://your-server:11434"}`.
  That file and the whole output folder `docs/manual/` are git-ignored: the server's address and the manual's text/pictures must never be committed.
* **The manual does not need OCR for 118 of its 120 pages.** Its text layer has the right letters but bogus spaces inside words ("dange rous", on 116 of 118 pages). The PDF stores every
  character's position, and a bogus space is one where the next letter starts about 2 pt *before* the space ends, so `text` drops those; bold short lines become headings. Result: median 0.0% stray letters.
  `python tools/ocr_pdf.py text "<manual.pdf>" --out docs/manual/text` writes `pNNN.md` and `needs_ocr.txt` (pages with no layer, still broken, or mostly a picture: the cover and back cover here);
  `python tools/ocr_pdf.py chapters docs/manual/text --out docs/manual/chapters` joins them into one file per chapter (16 files) and `all.md`. The quick reference card has no text layer at all: OCR it with `pages`.
* `python tools/ocr_pdf.py models`: the server's models that can read images.
* `python tools/ocr_pdf.py images "<pdf>" --out docs/manual/images/manual`: every embedded picture plus `index.txt` (file, page, size).
* `python tools/ocr_pdf.py pages "<pdf>" --out docs/manual/qrc --model <model> [--pages 1-6] [--hint-text]`: `pNNN.md` per page (resumable) and `all.md`.
  `--hint-text` hands the model the PDF's own text layer so it only fixes structure (headings, lists, tables); use it for the manual, not for the card (no layer).
* `python tools/ocr_pdf.py bench "<pdf>" --models a,b,c --pages 12,40,73 --out docs/manual/bench`: time per page for each model (load, unload, load again first; not counted) and, where the page has a
  text layer, a word-level similarity against it, written to `bench.md`.

## Model benchmark (2026-10-31, an Ollama server on the local network; load, unload, load again before timing; seconds exclude model load)

Pages: manual 12 (screenshot page), 40 (text), 73 (mixed) with the repaired text layer as ground truth (letters-only similarity); quick reference card pages 1 (terrain table) and 4 (flow chart), no ground truth.

| Model | s/page, manual | similarity | s/page, card | Card result |
|---|---|---|---|---|
| gemma4:e2b | 5.3 | 0.90 | 3.1 | fast, but dropped the Mountain row's coal/iron/gold/gems split |
| **gemma4:e4b** (default) | 7.0 | 0.91 | 5.5 | kept those rows; table cells approximate |
| qwen3.5:4b | 18.2 | 0.91 | 13 | similar to e4b, slower |
| gemma4:12b | 20.1 | 0.88 | 12-27 | best table (all levels and units), still no flow-chart arrows |
| gemma4:27b, 31b | 44 | 0.83-0.86 | not run | errored on 2 of 3 manual pages; not worth the time |
| qwen3-vl 4b, 8b | n/a | n/a | n/a | always reason (`think:false` ignored); empty answers inside 2500 tokens |

Decision: the manual is rebuilt from its text layer (no model); e4b for other text-heavy pages; **no model reads diagram arrows correctly** (page 4 got invented edges from the small models and labels only from 12b), so
diagrams and dense tables on the card are transcribed by looking at the image.


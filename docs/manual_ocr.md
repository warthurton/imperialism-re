# OCR of the manual and the quick reference card

The game folder has two PDFs: `Imperialism - manual.pdf` (120 pages, **has a text layer**, 38 embedded screenshots/art) and `Imperialism - quick reference card.pdf`
(6 pages, **image only**: each page is one 900x1035 picture, so it needs real OCR). `tools/ocr_pdf.py` turns them into Markdown with a vision model served by Ollama.

* **Set up once**: `python -m pip install --user pymupdf` (run the script with plain `python`, not `-I`, so the user site is found), and tell the script where Ollama is:
  `set OLLAMA_HOST=http://your-server:11434` (PowerShell: `$env:OLLAMA_HOST=...`) **or** create `tools/ocr.local.json` containing `{"host": "http://your-server:11434"}`.
  That file and the whole output folder `docs/manual/` are git-ignored: the server's address and the manual's text/pictures must never be committed.
* `python tools/ocr_pdf.py models`: the server's models that can read images.
* `python tools/ocr_pdf.py images "<pdf>" --out docs/manual/images/manual`: every embedded picture plus `index.txt` (file, page, size).
* `python tools/ocr_pdf.py pages "<pdf>" --out docs/manual/qrc --model <model> [--pages 1-6] [--hint-text]`: `pNNN.md` per page (resumable) and `all.md`.
  `--hint-text` hands the model the PDF's own text layer so it only fixes structure (headings, lists, tables); use it for the manual, not for the card (no layer).
* `python tools/ocr_pdf.py bench "<pdf>" --models a,b,c --pages 12,40,73 --out docs/manual/bench`: time per page for each model (warm-up not counted) and, where the page has a
  text layer, a word-level similarity against it, written to `bench.md`.

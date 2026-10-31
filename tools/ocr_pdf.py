"""OCR + Markdown formatting of the game's PDFs (manual, quick reference card) with a vision model served by Ollama.

Needs PyMuPDF (pip install --user pymupdf; run this script with plain `python`, not `-I`, so the user site is found).
The Ollama server is NOT in the repo: set OLLAMA_HOST (for example http://myserver:11434) or put {"host": "http://..."} in
tools/ocr.local.json (git-ignored). Output goes to docs/manual/ (git-ignored: the manual is copyrighted, never commit it).

  python tools/ocr_pdf.py models                                  list the server's models that can read images
  python tools/ocr_pdf.py images "<pdf>" --out docs/manual/images extract embedded pictures (screens, art) and write a page index
  python tools/ocr_pdf.py text   "<pdf>" --out docs/manual/text      rebuild pages from the PDF's own text layer (fixes bogus spaces), list pages that need OCR
  python tools/ocr_pdf.py chapters docs/manual/text --out docs/manual/chapters   join pages into one file per chapter
  python tools/ocr_pdf.py pages  "<pdf>" --out docs/manual/qrc --model qwen3-vl:4b [--pages 1-6] [--hint-text]
  python tools/ocr_pdf.py bench  "<pdf>" --models a,b,c --pages 5,40,70 --out docs/manual/bench

`pages` writes pNNN.md per page (resumable: existing files are kept unless --force) and all.md. --hint-text gives the model the PDF's own
text layer as a hint (pages that have one): it then fixes structure (headings, lists, tables) instead of guessing letters.
`bench` times each model on the same pages (load, unload, load again first: the first load after a while is slow because of the server's model cache, none of it counted) and, for pages that have a text layer, scores the OCR against it
(word-level similarity), so speed is compared only between models that are accurate enough. Nothing here prints the host address."""
import argparse, base64, difflib, json, os, re, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
PROMPT = ("Transcribe this page of a printed game manual into clean Markdown. Keep the reading order. Use # / ## / ### for headings, "
          "- for bullet lists, 1. for numbered lists, Markdown tables for tables, **bold** and *italic* where the print has them. "
          "Join lines of one paragraph. Do not summarize, translate, correct or add anything. For a picture, screenshot or diagram "
          "write one line: [Figure: what it shows] and transcribe any labels in it. Output only the Markdown.")
HINT = ("\n\nThe page's own embedded text layer (may have wrong line breaks, order or missing structure, but its letters are right) is:\n"
        "<<<\n{text}\n>>>\nUse it to get the wording exactly right, and the image to get the structure and order right.")


def host():
    h = os.environ.get('OLLAMA_HOST')
    if not h:
        p = os.path.join(HERE, 'ocr.local.json')
        if os.path.exists(p):
            h = json.load(open(p, encoding='utf-8')).get('host')
    if not h:
        sys.exit('no Ollama host: set OLLAMA_HOST or create tools/ocr.local.json {"host": "http://server:11434"}')
    return h if h.startswith('http') else 'http://' + h


def api(path, body=None, timeout=900):
    req = urllib.request.Request(host().rstrip('/') + path, None if body is None else json.dumps(body).encode(), {'Content-Type': 'application/json'})
    try:
        return json.load(urllib.request.urlopen(req, timeout=timeout))
    except urllib.error.URLError as e:
        sys.exit('Ollama request failed (%s): %s' % (path, getattr(e, 'reason', e)))


def vision_models():
    out = []
    for m in api('/api/tags', timeout=20)['models']:
        caps = api('/api/show', {'model': m['name']}, 30).get('capabilities') or []
        if 'vision' in caps and 'embedding' not in caps:
            out.append((m['name'], round(m['size'] / 1e9, 1)))
    return out


def load(model):
    api('/api/chat', {'model': model, 'stream': False, 'think': False, 'keep_alive': '30m', 'options': {'num_predict': 1},
                      'messages': [{'role': 'user', 'content': 'hi'}]})


def unload(model):
    api('/api/generate', {'model': model, 'keep_alive': 0, 'stream': False}, 120)


def warm(model):
    """Load, unload, load again: the first load after a while is slow because of the server's model cache, the second is representative."""
    load(model)
    unload(model)
    time.sleep(2)
    load(model)


def pdf_pages(path):
    try:
        import pymupdf as fitz
    except ImportError:
        import fitz
    return fitz.open(path)


def parse_pages(spec, n):
    if not spec:
        return list(range(n))
    out = []
    for part in spec.split(','):
        a, _, b = part.partition('-')
        out += list(range(int(a) - 1, int(b or a)))
    return [p for p in out if 0 <= p < n]


def render(doc, i, dpi, outdir):
    os.makedirs(outdir, exist_ok=True)
    f = os.path.join(outdir, 'p%03d.png' % (i + 1))
    if not os.path.exists(f):
        doc[i].get_pixmap(dpi=dpi).save(f)
    return f


def ocr_page(model, png, text_hint=None, num_predict=4096):
    prompt = PROMPT + (HINT.format(text=text_hint) if text_hint else '')
    t = time.time()
    r = api('/api/chat', {'model': model, 'stream': False, 'think': False, 'keep_alive': '30m',
                          'options': {'temperature': 0, 'num_predict': num_predict},
                          'messages': [{'role': 'user', 'content': prompt, 'images': [base64.b64encode(open(png, 'rb').read()).decode()]}]})
    work = (r.get('total_duration', 0) - r.get('load_duration', 0)) / 1e9 or time.time() - t     # model load time (server memory swaps) is not counted
    return r['message']['content'].strip(), work, r.get('eval_count', 0), len(r['message'].get('thinking') or '')


def clean(md):
    md = re.sub(r'^```(?:markdown)?\n|\n```$', '', md.strip())
    return md


def squash(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())      # the PDF's text layer has stray spaces inside words ("dange rous"), so compare letters only


def similarity(a, b):
    sa, sb = squash(a), squash(b)
    return difflib.SequenceMatcher(None, sa, sb, autojunk=False).ratio() if sa and sb else 0.0


def page_markdown(page):
    """Rebuild one page from the PDF's own text layer. The layer's letters are right but it is full of bogus spaces inside words ("dange rous"):
    a bogus space is one whose next character starts well before the space ends (negative gap, about -2 pt), so those are dropped. Bold lines that
    are short become headings, a block becomes a paragraph, hyphenated line ends are joined, bullet lines stay bullets."""
    out = []
    for b in page.get_text('rawdict')['blocks']:
        lines = []
        for l in b.get('lines', []):
            text, bold, size, space = '', True, 0.0, None
            for s in l['spans']:
                bold = bold and ('Bold' in s['font'] or 'Medi' in s['font'])
                size = max(size, s['size'])
                for c in s['chars']:
                    if c['c'] == ' ':
                        space = c
                        text += ' '
                        continue
                    if space is not None and text.endswith(' ') and c['bbox'][0] - space['bbox'][2] < -1.0:
                        text = text[:-1]                       # bogus space: the next letter overlaps it
                    space = None
                    text += c['c']
            if text.strip():
                lines.append((text.strip(), bold, size))
        if not lines:
            continue
        if all(bl for _, bl, _ in lines) and sum(len(x) for x, _, _ in lines) < 90:
            out.append(('##' if max(s for _, _, s in lines) >= 10 else '###') + ' ' + ' '.join(x for x, _, _ in lines))
            continue
        para = ''
        for x, _, _ in lines:
            if re.match(r'^[•·*-]\s', x):
                if para:
                    out.append(para)
                    para = ''
                out.append('- ' + x[2:].strip())
                continue
            para = para[:-1] + x if para.endswith('-') and x[:1].islower() else (para + ' ' + x if para else x)
        if para:
            out.append(para)
    return '\n\n'.join(out)


def fragment_ratio(s):
    toks = re.findall(r"[A-Za-z']+", s)
    return sum(1 for w in toks if len(w) == 1 and w not in 'aAI') / len(toks) if toks else 1.0


def cmd_text(a):
    doc = pdf_pages(a.pdf)
    os.makedirs(a.out, exist_ok=True)
    need, rows = [], []
    for i in parse_pages(a.pages, len(doc)):
        page = doc[i]
        md = page_markdown(page)
        ratio = fragment_ratio(md)
        why = ''
        if len(squash(md)) < 40:
            why = 'no text layer'
        elif ratio > a.max_fragments:
            why = 'still broken (%.1f%% stray letters)' % (100 * ratio)
        elif len(squash(md)) < a.min_chars and page.get_images():
            why = 'mostly a picture'
        open(os.path.join(a.out, 'p%03d.md' % (i + 1)), 'w', encoding='utf-8').write(md + '\n')
        rows.append((i + 1, ratio, len(md)))
        if why:
            need.append('%d  %s' % (i + 1, why))
    open(os.path.join(a.out, 'needs_ocr.txt'), 'w').write('\n'.join(need) + '\n')
    print('%d pages written to %s; %d need OCR (listed in needs_ocr.txt); median stray-letter ratio %.1f%%' % (
        len(rows), a.out, len(need), 100 * sorted(r for _, r, _ in rows)[len(rows) // 2]))


def cmd_chapters(a):
    """Join the pNNN.md pages in a folder into one Markdown file per chapter (a chapter starts on a page whose first line is an ALL-CAPS ## heading),
    plus all.md. Pages are marked with <!-- page N --> comments (PDF page numbers, not the printed ones)."""
    files = sorted(f for f in os.listdir(a.src) if re.match(r'p\d{3}\.md$', f))
    chapters, cur = [], None
    for f in files:
        n = int(f[1:4])
        body = open(os.path.join(a.src, f), encoding='utf-8').read().strip()
        m = re.match(r'## ([A-Z][A-Z0-9 ,&\'-]+)\s*$', body.split('\n')[0]) if body else None
        if m or cur is None:
            cur = [m.group(1).title() if m else 'Front matter', []]
            chapters.append(cur)
        cur[1].append('<!-- page %d -->\n\n%s' % (n, body))
    os.makedirs(a.out, exist_ok=True)
    allmd = []
    for k, (title, parts) in enumerate(chapters):
        name = '%02d_%s.md' % (k, re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_'))
        text = '\n\n'.join(parts) + '\n'
        open(os.path.join(a.out, name), 'w', encoding='utf-8').write(text)
        allmd.append(text)
        print('%-40s %3d pages  %6d chars' % (name, len(parts), len(text)))
    open(os.path.join(a.out, 'all.md'), 'w', encoding='utf-8').write('\n'.join(allmd))


def cmd_models(a):
    for n, g in vision_models():
        print('%-28s %5.1f GB' % (n, g))


def cmd_images(a):
    doc = pdf_pages(a.pdf)
    os.makedirs(a.out, exist_ok=True)
    index, seen = [], set()
    for i, page in enumerate(doc):
        for k, im in enumerate(page.get_images(full=True)):
            xref = im[0]
            if xref in seen:
                continue
            seen.add(xref)
            info = doc.extract_image(xref)
            name = 'p%03d_%02d.%s' % (i + 1, k + 1, info['ext'])
            open(os.path.join(a.out, name), 'wb').write(info['image'])
            index.append('%s  page %d  %dx%d  %d bytes' % (name, i + 1, info['width'], info['height'], len(info['image'])))
    open(os.path.join(a.out, 'index.txt'), 'w').write('\n'.join(index) + '\n')
    print('%d unique images from %d pages -> %s' % (len(index), len(doc), a.out))


def cmd_pages(a):
    doc = pdf_pages(a.pdf)
    os.makedirs(a.out, exist_ok=True)
    pages = parse_pages(a.pages, len(doc))
    for i in pages:
        md = os.path.join(a.out, 'p%03d.md' % (i + 1))
        if os.path.exists(md) and not a.force:
            continue
        png = render(doc, i, a.dpi, os.path.join(a.out, 'png'))
        hint = doc[i].get_text().strip() if a.hint_text else None
        text, secs, toks, _ = ocr_page(a.model, png, hint or None)
        open(md, 'w', encoding='utf-8').write(clean(text) + '\n')
        print('page %d: %.1f s, %d tokens' % (i + 1, secs, toks), flush=True)
    parts = []
    for i in range(len(doc)):
        f = os.path.join(a.out, 'p%03d.md' % (i + 1))
        if os.path.exists(f):
            parts.append('<!-- page %d -->\n\n%s' % (i + 1, open(f, encoding='utf-8').read().strip()))
    open(os.path.join(a.out, 'all.md'), 'w', encoding='utf-8').write('\n\n'.join(parts) + '\n')


def cmd_bench(a):
    doc = pdf_pages(a.pdf)
    pages = parse_pages(a.pages, len(doc))
    os.makedirs(a.out, exist_ok=True)
    pngs = {i: render(doc, i, a.dpi, os.path.join(a.out, 'png')) for i in pages}
    truth = {i: doc[i].get_text().strip() for i in pages}
    rows = []
    for model in a.models.split(','):
        warm(model)                                                                    # load, unload, load again: none of this is timed
        for i in pages:
            try:
                text, secs, toks, think = ocr_page(model, pngs[i], truth[i] if a.hint_text else None, a.num_predict)
            except SystemExit as e:
                rows.append((model, i + 1, None, None, None, str(e))); continue
            if not text and think:        # a model that reasons and never answers inside the budget: not usable, do not burn the other pages
                rows.append((model, i + 1, None, None, None, 'empty answer: all %d tokens went to hidden reasoning' % toks))
                print('%-24s p%-3d EMPTY (hidden reasoning, %d tok); skipping the model' % (model, i + 1, toks), flush=True)
                break
            open(os.path.join(a.out, '%s_p%03d.md' % (re.sub(r'[^A-Za-z0-9.]+', '_', model), i + 1)), 'w', encoding='utf-8').write(clean(text) + '\n')
            sim = similarity(text, truth[i]) if truth[i] else None
            rows.append((model, i + 1, secs, toks, sim, ''))
            print('%-24s p%-3d %6.1f s %5d tok  %s' % (model, i + 1, secs, toks, '' if sim is None else 'sim %.2f' % sim), flush=True)
    summ = {}
    for m, p, s, t, sim, err in rows:
        d = summ.setdefault(m, {'secs': [], 'sim': [], 'err': 0})
        d['err'] += bool(err)
        if s is not None:
            d['secs'].append(s)
        if sim is not None:
            d['sim'].append(sim)
    lines = ['| model | pages | mean s/page | mean text-layer similarity | errors |', '|---|---|---|---|---|']
    for m, d in sorted(summ.items(), key=lambda kv: sum(kv[1]['secs']) / max(1, len(kv[1]['secs']))):
        lines.append('| %s | %d | %.1f | %s | %d |' % (m, len(d['secs']), sum(d['secs']) / max(1, len(d['secs'])),
                     '%.2f' % (sum(d['sim']) / len(d['sim'])) if d['sim'] else 'n/a (image-only pages)', d['err']))
    open(os.path.join(a.out, 'bench.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('models').set_defaults(f=cmd_models)
    c = sub.add_parser('chapters'); c.set_defaults(f=cmd_chapters); c.add_argument('src'); c.add_argument('--out', required=True)
    for name, f in (('images', cmd_images), ('text', cmd_text), ('pages', cmd_pages), ('bench', cmd_bench)):
        p = sub.add_parser(name); p.set_defaults(f=f)
        p.add_argument('pdf'); p.add_argument('--out', required=True)
        if name == 'text':
            p.add_argument('--pages'); p.add_argument('--max-fragments', type=float, default=0.05); p.add_argument('--min-chars', type=int, default=400)
        if name not in ('images', 'text'):
            p.add_argument('--pages'); p.add_argument('--dpi', type=int, default=150); p.add_argument('--hint-text', action='store_true')
        if name == 'pages':
            p.add_argument('--model', required=True); p.add_argument('--force', action='store_true')
        if name == 'bench':
            p.add_argument('--models', required=True); p.add_argument('--num-predict', type=int, default=3000)
    a = ap.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()

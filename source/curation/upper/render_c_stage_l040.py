"""Render only this batch's source pages; graph database stays read-only."""
import json, sqlite3, sys
from pathlib import Path
import pymupdf as fitz
from PIL import Image, ImageDraw
sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8')
BASE = Path(__file__).resolve().parent
KB = Path(r'C:\Users\13240\Desktop\RAG\shared-knowledge\v0.1.0')
OUT = BASE / 'c_stage_l040.visual'
OUT.mkdir(exist_ok=True)
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
db.row_factory = sqlite3.Row
pdf = fitz.open(KB / 'sources' / 'volume_1.pdf')
pages = list(range(291, 302))
for number in pages:
    pix = pdf[number - 1].get_pixmap(matrix=fitz.Matrix(1.8, 1.8), alpha=False)
    im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    im.save(OUT / f'p{number:04d}.png')
    for row in db.execute("SELECT * FROM figures WHERE document_id='volume_1-a53e99c37ca5' AND pdf_page=?", (number,)):
        x0, y0, x1, y1 = json.loads(row['bbox'])
        im.crop(tuple(round(v * 1.8) for v in (x0, y0, x1, y1))).save(OUT / (row['id'].split('a53e99c37ca5-')[1] + '.png'))
for first in range(0, len(pages), 4):
    sheet = Image.new('RGB', (1200, 1730), 'white')
    draw = ImageDraw.Draw(sheet)
    for i, number in enumerate(pages[first:first+4]):
        im = Image.open(OUT / f'p{number:04d}.png')
        im.thumbnail((590, 835))
        x, y = i % 2 * 600, i // 2 * 865
        sheet.paste(im, (x, y + 25))
        draw.text((x + 8, y + 5), f'volume_1.pdf actual PDF page {number}', fill='black')
    sheet.save(OUT / f'sheet_{first//4+1:02d}.png')
print(json.dumps({'pages': pages, 'output': str(OUT)}, ensure_ascii=False))

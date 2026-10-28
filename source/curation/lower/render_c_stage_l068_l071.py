"""Read-only PDF rendering for the stage C lessons 68-71 review.

Only writes review images beside this script; does not touch the KB.
"""
from pathlib import Path
import json, sqlite3, sys
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')
BASE = Path(__file__).resolve().parent
KB = Path(r'C:\Users\13240\Desktop\RAG\shared-knowledge\v0.1.0')
OUT = BASE / 'c_stage_l068_l071_visual'
OUT.mkdir(exist_ok=True)
db = sqlite3.connect((KB / 'graph.sqlite').as_uri() + '?mode=ro', uri=True)
pages = [r[0] for r in db.execute("SELECT DISTINCT pdf_page FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 59 AND 102 ORDER BY pdf_page")]
pdf = pdfium.PdfDocument(str(KB / 'sources' / 'volume_2.pdf'))
for number in pages:
    pil = pdf[number - 1].render(scale=1.5).to_pil().convert('RGB')
    pil.save(OUT / f'p{number:04d}.png')
for batch in range(0, len(pages), 4):
    selected = pages[batch:batch+4]
    sheet = Image.new('RGB', (1200, 1730), 'white')
    draw = ImageDraw.Draw(sheet)
    for index, number in enumerate(selected):
        im = Image.open(OUT / f'p{number:04d}.png')
        im.thumbnail((590, 835))
        x, y = (index % 2) * 600, (index // 2) * 865
        sheet.paste(im, (x, y+25))
        draw.text((x+8, y+5), f'volume_2.pdf / actual PDF page {number}', fill='black')
    sheet.save(OUT / f'sheet_{batch//4+1:02d}.png')
print(json.dumps({'pages': pages, 'sheets': (len(pages)+3)//4, 'output': str(OUT)}, ensure_ascii=False))

"""Render only the fixed PDF pages used by batch 06; no source writes."""
from pathlib import Path
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_name('06-l001-l008-complete.visual')
OUT.mkdir(exist_ok=True)
pdf = pdfium.PdfDocument(str(ROOT / 'shared-knowledge/v0.1.0/sources/volume_1.pdf'))
for n in range(8, 23):
    image = pdf[n - 1].render(scale=1.8).to_pil()
    image.save(OUT / f'page-{n:04d}.png')
for start in (8, 11, 14, 17, 20):
    images = [Image.open(OUT / f'page-{n:04d}.png') for n in range(start, start + 3)]
    thumbs = []
    for n, im in zip(range(start, start + 3), images):
        im.thumbnail((600, 850))
        thumb = Image.new('RGB', (620, 885), 'white')
        thumb.paste(im, ((620-im.width)//2, 25))
        ImageDraw.Draw(thumb).text((10, 5), f'PDF {n}', fill='black')
        thumbs.append(thumb)
    sheet = Image.new('RGB', (1860, 885), '#dddddd')
    for x, im in enumerate(thumbs):
        sheet.paste(im, (620*x, 0))
    sheet.save(OUT / f'pages-{start:02d}-{start+2:02d}.png')
print(OUT)

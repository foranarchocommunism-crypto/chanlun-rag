"""Render the current fixed PDF pages for this batch only; no KB writes."""
from pathlib import Path
import hashlib
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'shared-knowledge/v0.1.0/sources/volume_1.pdf'
OUT = Path(__file__).resolve().parent / '05-l021-l024-complete.visual'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == 'a53e99c37ca500917ee5edf1d21efcb58f1b8e4363af2b4978dbdff920d18d4b'
OUT.mkdir(exist_ok=True)
pdf = pdfium.PdfDocument(SOURCE)
assert len(pdf) == 475
for number in range(104,145):
    page = pdf[number-1]
    bitmap = page.render(scale=1.5)
    bitmap.to_pil().convert('RGB').save(OUT / f'page-{number:03d}.png')
    bitmap.close()
    page.close()
for start in range(104,145,2):
    numbers = list(range(start,min(start+2,145)))
    images = [Image.open(OUT/f'page-{n:03d}.png') for n in numbers]
    canvas = Image.new('RGB',(sum(i.width for i in images),max(i.height for i in images)+30),'white')
    draw = ImageDraw.Draw(canvas)
    x=0
    for n,im in zip(numbers,images):
        draw.text((x+10,5),f'Actual PDF page {n}',fill='black')
        canvas.paste(im,(x,30)); x+=im.width
    canvas.save(OUT/f'spread-{start:03d}.jpg',quality=94)
print(str(OUT))

from pathlib import Path
import json, sqlite3, sys
import pypdfium2 as pdfium
from PIL import Image, ImageDraw
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
BASE=Path(__file__).resolve().parent
KB=Path(r'C:\Users\13240\Desktop\RAG\shared-knowledge\v0.1.0')
OUT=BASE/'c_stage_l081_visual';OUT.mkdir(exist_ok=True)
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True)
pages=sorted({r[0] for r in db.execute("SELECT pdf_page FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page BETWEEN 173 AND 188")}|{94,174,177,179,183})
pdf=pdfium.PdfDocument(str(KB/'sources'/'volume_2.pdf'))
for n in pages:pdf[n-1].render(scale=1.8).to_pil().convert('RGB').save(OUT/f'p{n:04d}.png')
for first in range(0,len(pages),4):
    sheet=Image.new('RGB',(1200,1730),'white');draw=ImageDraw.Draw(sheet)
    for i,n in enumerate(pages[first:first+4]):
        im=Image.open(OUT/f'p{n:04d}.png');im.thumbnail((590,835));x=i%2*600;y=i//2*865
        sheet.paste(im,(x,y+25));draw.text((x+8,y+5),f'volume_2.pdf actual PDF page {n}',fill='black')
    sheet.save(OUT/f'sheet_{first//4+1:02d}.png')
print(json.dumps({'pages':pages,'output':str(OUT)},ensure_ascii=False))

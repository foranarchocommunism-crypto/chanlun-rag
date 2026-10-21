"""Render 64's fixed source pages and five figure regions, without graph writes."""
import json,sqlite3,sys
from pathlib import Path
import pymupdf as fitz
from PIL import Image,ImageDraw
sys.stdout.reconfigure(encoding='utf-8')
KB=Path(r'C:\Users\13240\Desktop\RAG\shared-knowledge\v0.1.0')
OUT=Path(__file__).resolve().parent/'c_stage_l064.visual';OUT.mkdir(exist_ok=True)
db=sqlite3.connect((KB/'graph.sqlite').as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
pdf=fitz.open(KB/'sources/volume_2.pdf');pages=list(range(12,33))
for n in pages:
 pix=pdf[n-1].get_pixmap(matrix=fitz.Matrix(1.8,1.8),alpha=False);im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples);im.save(OUT/f'p{n:04d}.png')
 for f in db.execute("SELECT * FROM figures WHERE document_id='volume_2-5332cd1b6038' AND pdf_page=?",(n,)):
  im.crop(tuple(round(x*1.8) for x in json.loads(f['bbox']))).save(OUT/(f['id'].split('5332cd1b6038-')[1]+'.png'))
for start in range(0,len(pages),4):
 sheet=Image.new('RGB',(1200,1730),'white');draw=ImageDraw.Draw(sheet)
 for i,n in enumerate(pages[start:start+4]):
  im=Image.open(OUT/f'p{n:04d}.png');im.thumbnail((590,835));x,y=i%2*600,i//2*865;sheet.paste(im,(x,y+25));draw.text((x+8,y+5),f'volume2 actual PDF page {n}',fill='black')
 sheet.save(OUT/f'sheet_{start//4+1:02d}.png')
db.close();pdf.close();print(json.dumps(dict(pages=pages,figures=5,output=str(OUT))))

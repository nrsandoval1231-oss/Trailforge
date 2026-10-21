from pathlib import Path
import json, re, hashlib, xml.etree.ElementTree as ET
from html.parser import HTMLParser
from PIL import Image
from pypdf import PdfReader

root=Path(__file__).resolve().parents[3]
kit=root/'brand/trailforge-v1'
mark='M12 16H88L74 30H46V44H76L62 58H46V88H30V30H12Z'
svgs=list((kit/'exports/svg').glob('*.svg'))
for p in svgs:
    tree=ET.parse(p)
    assert all(not n.tag.endswith(('text','image','script')) for n in tree.iter()),p
    assert 'http' not in p.read_text().replace('http://www.w3.org/2000/svg',''),p
    if p.stem.startswith(('horizontal-','stacked-','icon-')) or p.stem in ('app-icon','trailforge-social-card','report-header','slide-cover'):
        assert any(n.attrib.get('d')==mark for n in tree.iter()),p
for color in ('jade','dark','white'):
    for size in (16,32,192,512,1024):
        im=Image.open(kit/f'exports/png/icon-{color}-{size}.png')
        assert im.size==(size,size)
        assert im.mode=='RGBA' and im.getextrema()[3][0]==0
pngs=list((kit/'exports/png').glob('*.png'))
assert Image.open(kit/'exports/favicon.ico').ico.sizes()=={(16,16),(32,32),(48,48)}
assert Image.open(kit/'exports/png/proof-board-white-1200x420.png').getpixel((0,0))[:3]==(255,255,255)
class Links(HTMLParser):
    def __init__(self):super().__init__();self.values=[]
    def handle_starttag(self,tag,attrs):
        for k,v in attrs:
            if k in ('src','href') and v and not v.startswith(('#','http','mailto:')):self.values.append(v.split('#')[0])
l=Links();l.feed((kit/'brandbook.html').read_text(encoding='utf-8'))
for value in l.values:assert (kit/value).is_file(),value
t=json.loads((kit/'tokens.json').read_text())
def all_leaves(value):
    if isinstance(value,dict):
        for v in value.values():yield from all_leaves(v)
    elif isinstance(value,list):
        for v in value:yield from all_leaves(v)
    else:yield value
for value in all_leaves(t):
    if isinstance(value,str) and value.startswith('{') and value.endswith('}'):
        cursor=t
        for name in value[1:-1].split('.'):cursor=cursor[name]
def luminance(h):
    rgb=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    return sum((v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4)*w for v,w in zip(rgb,[.2126,.7152,.0722]))
ratios=t.get('contrastPairs',t.get('contrast',[]))
if isinstance(ratios,dict):ratios=list(ratios.values())
for pair in ratios:
    a,b=sorted([luminance(pair['foreground']),luminance(pair['background'])])
    ratio=(b+.05)/(a+.05)
    assert abs(ratio-pair['ratio'])<.02,pair
reader=PdfReader(root/'output/pdf/trailforge-brand-guide.pdf')
assert len(reader.pages)==9
assert all(page.extract_text().strip() for page in reader.pages)
review=json.loads((root/'.agent/artifacts/jade-app-054/REVIEW-R1.json').read_text())
for name,h in review['candidate']['sha256'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest().lower()==h.lower(),name
result={'result':'PASS','svg_count':len(svgs),'png_count':len(pngs),'font_outline_external_dependency_checks':'PASS','canonical_mark_reuse':'PASS','favicon_sizes':[16,32,48],'local_asset_links':len(l.values),'token_aliases_and_measured_pairs':'PASS','pdf_pages':9,'existing_app_reviewed_hashes':'UNCHANGED'}
(root/'.agent/artifacts/brand-055/VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

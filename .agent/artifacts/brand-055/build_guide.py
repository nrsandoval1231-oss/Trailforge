from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from fontTools.ttLib import TTFont as Font
from fontTools.varLib.instancer import instantiateVariableFont
import json
import re
import xml.etree.ElementTree as ET
from fontTools.pens.reportLabPen import ReportLabPen
from fontTools.pens.transformPen import TransformPen
from fontTools.svgLib.path import parse_path
from fontTools.misc.transform import Transform
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

ROOT = Path(__file__).resolve().parents[3]
KIT = ROOT / 'brand/trailforge-v1'
OUT = ROOT / 'output/pdf/trailforge-brand-guide.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
TMP = ROOT / '.agent/artifacts/brand-055/pdf-render'
TMP.mkdir(exist_ok=True)
for name, weight in [('Regular', 400), ('Bold', 800)]:
    f = Font(KIT / 'fonts/Manrope.ttf')
    instantiateVariableFont(f, {'wght': weight}, inplace=True)
    for nid, value in [(1, f'TrailforgeManrope{name}'), (4, f'Trailforge Manrope {name}'), (6, f'TrailforgeManrope-{name}')]:
        f['name'].setName(value,nid,3,1,0x409)
        f['name'].setName(value,nid,1,0,0)
    f.save(TMP / f'Manrope-{name}.ttf')
    pdfmetrics.registerFont(TTFont(name, str(TMP / f'Manrope-{name}.ttf')))
pdfmetrics.registerFont(TTFont('Mono', str(KIT / 'fonts/IBMPlexMono-Regular.ttf')))
P = {'jade':'#126653','graphite':'#232B26','paper':'#F5F4EE','mist':'#EEF4EF','mint':'#70D1AE','brass':'#B49A60','muted':'#59645D','white':'#FFFFFF'}
W,H = 842,595
c = canvas.Canvas(str(OUT), pagesize=(W,H))
c.setTitle('Trailforge | Brand system v1')
c.setAuthor('Trailforge')
page = 0
def rect(x,y,w,h,color,r=0):
    c.setFillColor(HexColor(P.get(color,color)))
    if r: c.roundRect(x,y,w,h,r,fill=1,stroke=0)
    else: c.rect(x,y,w,h,fill=1,stroke=0)
def text(x,y,s,size=12,font='Regular',color='graphite'):
    c.setFillColor(HexColor(P.get(color,color))); c.setFont(font,size); c.drawString(x,y,s)
def para(x,top,s,width=340,size=12,color='muted',font='Regular'):
    p=Paragraph(s,ParagraphStyle('p',fontName=font,fontSize=size,leading=size*1.55,textColor=HexColor(P.get(color,color))))
    _,height=p.wrap(width,H); p.drawOn(c,x,top-height); return top-height
def label(x,y,s,color='muted'): text(x,y,s.upper(),9,'Mono',color)
def mark(x,y,size=60,color='jade'):
    # Canonical solid T/F Trailmark. PDF coordinates reverse SVG y-axis.
    points=[(12,16),(88,16),(74,30),(46,30),(46,44),(76,44),(62,58),(46,58),(46,88),(30,88),(30,30),(12,30)]
    p=c.beginPath()
    p.moveTo(x+points[0][0]*size/100,y+(100-points[0][1])*size/100)
    for a,b in points[1:]: p.lineTo(x+a*size/100,y+(100-b)*size/100)
    p.close(); c.setFillColor(HexColor(P[color])); c.drawPath(p,fill=1,stroke=0)
def lockup(x,y,size=60,color='jade',maxwidth=570):
    master=KIT / 'exports/svg' / f'horizontal-{"dark" if color=="graphite" else color}.svg'
    if master.exists():
        svg=ET.parse(master).getroot(); _,_,width,height=map(float,svg.attrib['viewBox'].split())
        drawing=Drawing(width,height)
        def walk(node,matrix=Transform(),fill=P[color]):
            local=Transform()
            for kind,params in re.findall(r'(translate|scale|matrix)\(([^)]+)\)',node.attrib.get('transform','')):
                vals=[float(v) for v in re.split(r'[,\s]+',params.strip())]
                if kind=='translate':local=local.translate(vals[0],vals[1] if len(vals)>1 else 0)
                elif kind=='scale':local=local.scale(vals[0],vals[1] if len(vals)>1 else vals[0])
                else:local=local.transform(vals)
            matrix=matrix.transform(local);fill=node.attrib.get('fill',fill)
            if node.tag.endswith('path'):
                pen=ReportLabPen(None); parse_path(node.attrib['d'],TransformPen(pen,matrix))
                pen.path.fillColor=HexColor(fill);pen.path.strokeColor=None;pen.path.fillMode=1;drawing.add(pen.path)
            for child in node:walk(child,matrix,fill)
        walk(svg); scale=min(size/height,maxwidth/width)
        c.saveState();c.translate(x,y+height*scale);c.scale(scale,-scale);renderPDF.draw(drawing,c,0,0);c.restoreState()
        return
    mark(x,y,size,color)
    t=c.beginText(x+size+size*.12,y+size*.31);t.setFont('Bold',size*.46);t.setCharSpace(size*.017);t.setFillColor(HexColor(P[color]));t.textOut('TRAILFORGE');c.drawText(t)
def start(title,kicker,dark=False):
    global page
    page+=1; rect(0,0,W,H,'graphite' if dark else 'paper')
    label(42,H-36,'TRAILFORGE / BRAND SYSTEM / V1', 'mint' if dark else 'jade')
    text(42,H-91,title,32,'Bold','white' if dark else 'graphite')
    label(42,H-120,kicker,'mint' if dark else 'muted')
def end(dark=False):
    color='mint' if dark else 'muted'
    label(42,25,'PROJECT-FIRST POWER INTELLIGENCE',color)
    label(W-85,25,f'{page:02} / 09',color); c.showPage()
def contrast(a,b):
    def lum(v):
        z=[int(v[i:i+2],16)/255 for i in (1,3,5)]
        z=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in z]
        return sum(x*y for x,y in zip(z,[.2126,.7152,.0722]))
    x,y=sorted([lum(P[a]),lum(P[b])]); return (y+.05)/(x+.05)

start('Find the project. Forge the path.','THE JADE IDENTITY',True)
lockup(42,280,115,'white')
para(42,220,'A clear identity for work that begins before the requirements are fully known. Source facts, buyer paths and human judgment move together.',500,17,'white')
rect(650,80,150,310,'jade',12);mark(660,245,130,'mint')
label(671,145,'TRAILMARK','white');para(671,125,'A route taking shape.',112,12,'white')
end(True)

start('Evidence before action.','01 / POSITIONING')
text(42,407,'The fieldwork desk',23,'Bold')
para(42,380,'Trailforge helps commercial-power teams organize early project signals, review the evidence, map the buyer chain and prepare a customer conversation.',350,15)
text(450,407,'Who it serves',18,'Bold')
para(450,380,'Business development, commercial-power operators and infrastructure researchers who need a clear record of what is known and what comes next.',345,13)
text(450,285,'What it stands for',18,'Bold')
para(450,259,'Clarity. Traceability. Practical momentum. The identity feels industrial and capable, with enough warmth for a working customer relationship.',345,13)
rect(42,78,758,92,'jade',10)
label(61,144,'THE CUSTOMER-FIRST SEQUENCE','mint')
text(61,114,'Discover > Review need > Map buyers > Talk > Coordinate',17,'Bold','white')
end()

start('One mark. A consistent signature.','02 / LOGO SYSTEM')
rect(42,290,470,135,'white',10);lockup(63,326,74,maxwidth=425)
rect(540,290,260,135,'graphite',10);mark(625,311,96,'white')
label(61,309,'PRIMARY / JADE');label(558,309,'REVERSED / WHITE','mint')
lockup(48,211,50,'graphite');label(47,196,'MONOCHROME')
text(42,155,'Clear space',15,'Bold');para(42,135,'Keep at least one quarter of the mark height clear on every side. Preserve the supplied lockup proportions.',350,12)
text(450,155,'Minimum sizes',15,'Bold');para(450,135,'Horizontal: 120 px / 35 mm. Icon: 24 px / 10 mm. The 16 px export is reserved for browser favicons.',345,12)
label(42,64,'KEEP IT FLAT. DO NOT STRETCH, ROTATE, RECOLOR, OUTLINE OR ADD EFFECTS.')
end()

start('Jade carries the identity.','03 / COLOR')
names=[('jade','Jade / Primary'),('graphite','Graphite / Structure'),('paper','Paper / Canvas'),('mist','Mist / Surface'),('mint','Mint / Highlight'),('brass','Brass / Detail')]
for i,(key,name) in enumerate(names):
    x=42+(i%3)*260;y=330-(i//3)*145
    rect(x,y,238,96,key,8);fg='white' if key in ('jade','graphite') else 'graphite'
    text(x+15,y+65,name,12,'Bold',fg);text(x+15,y+19,P[key],11,'Mono',fg)
ratios={f'{a} on {b}':round(contrast(a,b),2) for a,b in [('white','jade'),('graphite','paper'),('muted','paper'),('mint','graphite'),('graphite','brass')]}
label(42,147,'APPROVED TEXT PAIRINGS / CONTRAST RATIO')
for i,(name,ratio) in enumerate(ratios.items()): text(42+(i%3)*260,116-(i//3)*28,f'{name}: {ratio}:1',11,'Mono')
end()

start('Confident headings. Useful detail.','04 / TYPOGRAPHY')
text(42,395,'Manrope',52,'Bold');para(42,342,'Primary family for headings, body copy and interface labels. Use weight 800 for the wordmark, 700-800 for headings and 400-500 for body text.',400,13)
text(42,249,'Projects worth pursuing.',29,'Bold')
text(42,211,'Keep source facts and open questions together.',15)
text(42,169,'SOURCE / OBSERVED / REVIEWED',13,'Mono','jade')
rect(500,144,300,281,'white',10)
label(520,394,'TYPE SCALE')
for i,s in enumerate(['Display 48-72 / 1.05','H1 40 / 1.1','H2 28 / 1.2','H3 20 / 1.3','Body 16 / 1.6','Metadata 12 / 1.4']):text(520,362-i*31,s,12,'Mono')
para(42,105,'IBM Plex Mono is reserved for dates, source IDs and short technical annotations. Sentence case for prose; uppercase only for the wordmark and short section labels.',758,12)
end()

start('A route, a grid, a clear next step.','05 / GRAPHIC LANGUAGE & INTERFACE')
rect(42,260,758,163,'jade',12)
c.saveState();c.setStrokeColor(Color(1,1,1,.12));c.setLineWidth(.7)
for x in range(42,810,48):c.line(x,260,min(x+74,800),423)
c.restoreState()
text(64,384,'Projects worth pursuing.',25,'Bold','white')
para(64,357,'Use route lines as quiet depth. A glass panel belongs in a contained scene; its text always needs a stable surface.',340,13,'white')
rect(450,282,326,117,'graphite',10);label(469,373,'THE NEXT RIGHT STEP','mint');text(469,343,'Review the source.',19,'Bold','white')
rect(469,300,175,27,'mint',5);text(480,309,'Open project file',11,'Bold','graphite')
text(42,217,'Structure',16,'Bold');para(42,194,'4 px spacing grid. Comfortable 16 px body text. 8-12 px panel corners. 44 px minimum interaction targets. Visible focus ring and text labels for every state.',350,12)
text(450,217,'Motion & glass',16,'Bold');para(450,194,'Feedback: 140-200 ms. Page entry: 240-320 ms. Ambient motion: slow and subtle with a pause control. Respect reduced motion; replace glass with a solid surface when transparency is reduced.',345,12)
end()

start('Clear facts. Practical next steps.','06 / VOICE & MESSAGING')
text(42,407,'Direct / Grounded / Curious / Capable',22,'Bold')
para(42,377,'Lead with the project. Name the source. Keep uncertainty explicit. Give the operator a useful action without implying that evidence is customer confirmation.',758,14)
examples=[('Power need is unknown. Add a reviewed source.','A high-confidence opportunity is ready.'),('Buyer role recorded. Decision authority remains unknown.','We found the decision maker.'),('Prepare a conversation brief.','Automatically close the customer.'),('Two sources checked. Review the candidate signals.','Every project in the market, found first.')]
label(42,292,'USE');label(450,292,'AVOID')
for i,(a,b) in enumerate(examples):
    y=265-i*43
    para(42,y,a,350,12,'jade');para(450,y,b,345,12)
para(42,69,'Tagline: Find the project. Forge the path. Descriptor: Project-first power intelligence. Never promise market lead time, forecast accuracy or verified intent without supporting evidence.',758,10)
end()

start('Ready for the places it works.','07 / APPLICATIONS')
rect(42,258,340,165,'graphite',10);lockup(58,338,41,'white',maxwidth=306);text(64,296,'Project-first power intelligence',14,'Regular','white');label(64,280,'IDENTITY CARD / NO CONTACT DETAILS','mint')
rect(414,258,386,165,'jade',10);mark(700,278,70,'mint');text(436,380,'Find the project.',25,'Bold','white');text(436,344,'Forge the path.',25,'Bold','white');label(436,289,'SOCIAL / CAMPAIGN TITLE','mint')
rect(42,71,486,156,'white',8);lockup(60,171,39);label(61,145,'PROJECT FIELD NOTES');text(61,114,'A source. A question. A next step.',18,'Bold');label(61,91,'REPORT HEADER / DOCUMENT COVER')
rect(560,71,240,156,'mist',8);rect(629,123,100,83,'jade',19);mark(642,126,74,'white');label(586,93,'APP ICON / SOLID FIELD')
end()

start('Use the masters. Keep the meaning.','08 / HANDOFF')
text(42,405,'The kit',20,'Bold')
para(42,377,'Outlined SVG logo masters, transparent PNG exports, app icons and favicon, route-pattern artwork, social and document templates, an offline brandbook, brand guidelines and CSS/JSON design tokens.',350,14)
text(450,405,'Implementation',20,'Bold')
para(450,377,'Use semantic tokens for actions, surfaces, text and feedback. Preserve UNKNOWN, reviewed evidence and recorded conversation as separate meanings. Use text labels and icons in addition to color.',345,14)
text(42,228,'Type licensing',18,'Bold')
para(42,201,'Manrope and IBM Plex Mono are distributed with their SIL Open Font License files in the kit. The logo wordmark is supplied as outlines, so recipients do not need the font installed.',758,12)
para(42,127,'Font sources:<br/>https://github.com/google/fonts/tree/main/ofl/manrope<br/>https://github.com/IBM/plex/blob/master/LICENSE.txt',758,10,'muted','Mono')
label(42,62,'DESIGN V1 / OCTOBER 2026 / LOCAL BRAND ASSETS; WORKING APP NOT MODIFIED')
end()
c.save()
(TMP/'contrast.json').write_text(json.dumps(ratios,indent=2))
print(OUT)

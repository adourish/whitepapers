"""Build the Word copy of the white paper: pandoc for the content, python-docx for the page and table style."""
import os, re, subprocess, sys
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'README.md')
OUT = os.path.join(HERE, 'exports', 'printing-hang-fixes-compared-v1.7.docx')
TMP = os.path.join(os.environ['TEMP'], 'wp-java21.docx')

md = open(SRC, encoding='utf-8').read()
# Relative links to lab files do not work inside a Word file: keep the text, drop the link target
md = re.sub(r'(?<!!)\[([^\]]+)\]\(((?:lab|assets)/[^)]+)\)',
            lambda m: m.group(1) if m.group(2).rstrip('/') in m.group(1) else '%s (%s)' % (m.group(1), m.group(2)), md)
# The header block is one line per field: give each its own paragraph in Word
md = re.sub(r'^(\*\*[^*\n]+:\*\* .*)\n(?=\*\*[^*\n]+:\*\* )', lambda m: m.group(1) + '\n\n', md, flags=re.M)
mdtmp = os.path.join(HERE, '_word_build.md')
open(mdtmp, 'w', encoding='utf-8').write(md)
try:
    subprocess.run(['pandoc', mdtmp, '-f', 'gfm', '-t', 'docx', '-o', TMP, '--resource-path', HERE], check=True)
finally:
    os.remove(mdtmp)

d = Document(TMP)
FONT = 'Calibri'
for st in d.styles:
    try:
        if st.font is not None:
            mono = st.name.endswith('Tok') or st.name in ('Verbatim Char', 'Source Code')
            f = 'Consolas' if mono else FONT
            st.font.name = f
            rpr = st.element.get_or_add_rPr()
            rf = rpr.find(qn('w:rFonts'))
            if rf is None:
                rf = OxmlElement('w:rFonts'); rpr.append(rf)
            for k in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'):
                rf.set(qn(k), f)
            for k in ('w:asciiTheme', 'w:hAnsiTheme', 'w:cstheme', 'w:eastAsiaTheme'):
                if rf.get(qn(k)) is not None:
                    del rf.attrib[qn(k)]
    except Exception:
        pass
for name, size in (('Normal', 10.5), ('Body Text', 10.5), ('First Paragraph', 10.5), ('Compact', 10.5),
                   ('Title', 22), ('Heading 1', 16), ('Heading 2', 13), ('Heading 3', 11.5)):
    if name in d.styles:
        d.styles[name].font.size = Pt(size)
        if name.startswith('Heading') or name == 'Title':
            d.styles[name].font.color.rgb = RGBColor(0x0B, 0x3D, 0x4F)   # dark teal, not red or green
            d.styles[name].font.bold = True
if 'Source Code' in d.styles:
    d.styles['Source Code'].font.size = Pt(8.5)
if 'Verbatim Char' in d.styles:
    d.styles['Verbatim Char'].font.size = Pt(9)
for st in ('Verbatim Char', 'Source Code'):
    if st in d.styles:
        d.styles[st].font.name = 'Consolas'
        rf = d.styles[st].element.get_or_add_rPr().find(qn('w:rFonts'))
        for k in ('w:ascii', 'w:hAnsi', 'w:cs'):
            rf.set(qn(k), 'Consolas')

# US Letter, 0.7 inch margins
for sec in d.sections:
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.left_margin = sec.right_margin = Inches(0.7)
    sec.top_margin = sec.bottom_margin = Inches(0.7)
TEXT_W = Inches(8.5 - 1.4)

def border(tbl):
    tblPr = tbl._tbl.tblPr
    b = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        e = OxmlElement('w:' + edge)
        e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '4'); e.set(qn('w:color'), '9AA5AD')
        b.append(e)
    old = tblPr.find(qn('w:tblBorders'))
    if old is not None:
        tblPr.remove(old)
    tblPr.append(b)
    w = tblPr.find(qn('w:tblW'))
    if w is None:
        w = OxmlElement('w:tblW'); tblPr.append(w)
    w.set(qn('w:type'), 'pct'); w.set(qn('w:w'), '5000')

def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    s = OxmlElement('w:shd'); s.set(qn('w:val'), 'clear'); s.set(qn('w:color'), 'auto'); s.set(qn('w:fill'), fill)
    tcPr.append(s)

for tbl in d.tables:
    border(tbl)
    ncols = len(tbl.columns)
    size = Pt(9) if ncols <= 4 else Pt(8)
    for i, row in enumerate(tbl.rows):
        trPr = row._tr.get_or_add_trPr()
        cs = OxmlElement('w:cantSplit'); trPr.append(cs)
        if i == 0:
            th = OxmlElement('w:tblHeader'); trPr.append(th)
        for cell in row.cells:
            if i == 0:
                shade(cell, 'D6EEF2')   # light cyan header
            for par in cell.paragraphs:
                # keep a table on one page where it fits, and never leave its header row alone
                if i < len(tbl.rows) - 1:
                    par.paragraph_format.keep_with_next = True
                par.paragraph_format.space_after = Pt(1)
                par.paragraph_format.space_before = Pt(1)
                for run in par.runs:
                    run.font.size = size
                    if i == 0:
                        run.font.bold = True

# Team picks table: each pick is a list to choose from, the rationale a box to type in
PICKS = ["a. Java 17, no changes", "b. Java 17, time limits", "c. Java 21, no changes", "d. Java 21, time limits",
         "e. Java 21 virtual threads, time limits, breaker", "f. Java 17, time limits, breaker",
         "g. Java 17, time limits, breaker, bulkhead"]

def control(par, alias, items=None, prompt='Choose an option'):
    for r in list(par.runs):
        r._r.getparent().remove(r._r)
    sdt = OxmlElement('w:sdt')
    pr = OxmlElement('w:sdtPr')
    al = OxmlElement('w:alias'); al.set(qn('w:val'), alias); pr.append(al)
    tg = OxmlElement('w:tag'); tg.set(qn('w:val'), alias.lower().replace(' ', '-')); pr.append(tg)
    pr.append(OxmlElement('w:showingPlcHdr'))
    if items:
        dd = OxmlElement('w:dropDownList')
        for text in [prompt] + items:
            li = OxmlElement('w:listItem'); li.set(qn('w:displayText'), text); li.set(qn('w:value'), '' if text == prompt else text)
            dd.append(li)
        pr.append(dd)
    else:
        tx = OxmlElement('w:text'); tx.set(qn('w:multiLine'), '1'); pr.append(tx)
    sdt.append(pr)
    content = OxmlElement('w:sdtContent')
    r = OxmlElement('w:r'); rpr = OxmlElement('w:rPr')
    c = OxmlElement('w:color'); c.set(qn('w:val'), '6B7780'); rpr.append(c)
    sz = OxmlElement('w:sz'); sz.set(qn('w:val'), '16'); rpr.append(sz)
    r.append(rpr)
    t = OxmlElement('w:t'); t.text = prompt; r.append(t)
    content.append(r); sdt.append(content)
    par._p.append(sdt)

for tbl in d.tables:
    head = [c.text.strip() for c in tbl.rows[0].cells]
    if head[:5] != ['Member', 'First pick', 'Second pick', 'Third pick', 'Rationale']:
        continue
    widths = [Inches(1.0), Inches(1.35), Inches(1.35), Inches(1.35), Inches(2.05)]
    for row in tbl.rows:
        for cell, w in zip(row.cells, widths):
            cell.width = w
    for gc, w in zip(tbl._tbl.tblGrid.findall(qn('w:gridCol')), widths):
        gc.set(qn('w:w'), str(int(w.inches * 1440)))
    lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); tbl._tbl.tblPr.append(lay)
    tw = tbl._tbl.tblPr.find(qn('w:tblW'))
    tw.set(qn('w:type'), 'dxa'); tw.set(qn('w:w'), str(int(sum(w.inches for w in widths) * 1440)))
    for row in tbl.rows[1:]:
        member = row.cells[0].text.strip()
        for col, alias in ((1, 'First pick'), (2, 'Second pick'), (3, 'Third pick')):
            control(row.cells[col].paragraphs[0], '%s, %s' % (member, alias), PICKS)
        control(row.cells[4].paragraphs[0], '%s, rationale' % member, prompt='Type the reason for your order')
        row.height = Inches(0.55)

# Pictures: fit to the text width
for shape in d.inline_shapes:
    ratio = shape.height / shape.width
    w = min(TEXT_W, int(Inches(9.2) / ratio))   # a tall picture is scaled to fit one page
    shape.width = w
    shape.height = int(w * ratio)

d.core_properties.author = 'The engineering team'
d.core_properties.title = 'Stopping the Kitchen Ticket Hang: Java 21, Time Limits, Circuit Breakers and Bulkheads Compared'
d.save(OUT)
os.remove(TMP)
print(OUT)

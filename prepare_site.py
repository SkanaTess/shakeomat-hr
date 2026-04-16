import sys, io, os, shutil, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SRC  = r"C:\Users\korisnik\Desktop\Claude_Code_Projects\protein_vending\shake-o-mat.html"
DEST = r"C:\Users\korisnik\Desktop\Claude_Code_Projects\shakeomat-hr"

# ── Read source ──────────────────────────────────────────────────────────────
with open(SRC, encoding='utf-8') as f:
    html = f.read()

# ── URL / domain substitutions ───────────────────────────────────────────────
html = html.replace('https://shake-o-mat.hr/', 'https://shakeomat.hr/')
html = html.replace('https://shake-o-mat.hr',  'https://shakeomat.hr')
html = html.replace('shake-o-mat.hr',           'shakeomat.hr')

# ── Write index.html ─────────────────────────────────────────────────────────
out = os.path.join(DEST, 'index.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Written: index.html ({len(html)//1024} KB)")

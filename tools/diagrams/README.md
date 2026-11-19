# Diagram toolkit

The picture scripts in each paper's `assets/` folder use these files. Add this folder to
`sys.path` with a relative path from the script:

```python
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "tools", "diagrams")))
from slide_kit import Slide
```

| File | What it does |
|---|---|
| `slide_kit.py` | Lays out a picture: title, zones, cards, arrows, key and footer |
| `diagram_style.py` | Colours (cyan, yellow, magenta), fonts and text wrapping |
| `layout_layers.py` | Places boxes in rows without overlaps |
| `write_alt_text.py` | Writes the `.png.alt.md` description beside a picture |
| `check_colour_blind.py` | Checks colours stay apart for colour-blind readers |
| `check_contrast.py` | Checks text contrast |
| `check_arrows.py` | Checks arrows don't cross boxes |

Needs Python 3.8+ and Pillow (`pip install pillow`). Fonts are Segoe UI on Windows, with Arial as
the fallback.

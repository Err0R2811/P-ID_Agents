import json
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

ITEMS_JSON = "entities.json"          # flattened json
TILES_JSON = "llm_outputs.json"          # recursive tile json

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------
# Load JSON
# ---------------------------------------------------------

with open(ITEMS_JSON) as f:
    items = json.load(f)

with open(TILES_JSON) as f:
    tiles = json.load(f)

tile_lookup = {t["tile_id"]: t for t in tiles}

# ---------------------------------------------------------
# Merge tile metadata
# ---------------------------------------------------------

for item in items:

    tile = tile_lookup[item["tile_id"]]

    item["tile_bbox"] = tile["bbox"]
    item["status"] = tile["status"]
    item["reason"] = tile["reason"]
    item["missing"] = tile["estimated_missing_items"]
    item["process_safety_observation"] = tile.get("process_safety_observation", "")

    # Use global_bbox for spatial calculations if available, otherwise fall back to tile_bbox
    if "global_bbox" in item and item["global_bbox"]:
        x1, y1, x2, y2 = item["global_bbox"]
    else:
        x1, y1, x2, y2 = tile["bbox"]

    item["bbox"] = [x1, y1, x2, y2]
    item["cx"] = (x1 + x2) / 2
    item["cy"] = (y1 + y2) / 2

# ---------------------------------------------------------
# Sort in page reading order
# ---------------------------------------------------------

items.sort(key=lambda x: (x["cy"], x["cx"]))

# ---------------------------------------------------------
# Markdown Layout
# ---------------------------------------------------------

tiles_sorted = sorted(tiles, key=lambda t: t["tile_id"])

layout_md = []

layout_md.append("# P&ID Layout\n")

for tile in tiles_sorted:

    x1, y1, x2, y2 = tile["bbox"]

    layout_md.append(f"## Tile {tile['tile_id']}")
    layout_md.append("")
    layout_md.append(f"**Depth:** {tile['depth']}")
    layout_md.append(f"**BBox:** `{tile['bbox']}`")
    layout_md.append(f"**Status:** {tile['status']}")
    layout_md.append(f"**Reason:** {tile['reason']}")
    if tile.get("process_safety_observation"):
        layout_md.append(f"**Process Safety Observation:** {tile['process_safety_observation']}")
    layout_md.append("")

    grouped = defaultdict(list)

    for obj in tile["items"]:
        grouped[obj["type"].title()].append(obj)

    for typ in sorted(grouped):

        layout_md.append(f"### {typ}")

        for obj in grouped[typ]:

            tag = obj.get("tag", "")
            desc = obj.get("description", "")
            service = obj.get("service", "")

            text = f"- **{tag}** : {desc}"

            if service:
                text += f" *(Service: {service})*"

            layout_md.append(text)

        layout_md.append("")

    layout_md.append("---\n")

(OUTPUT_DIR / "layout.md").write_text("\n".join(layout_md))

# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

summary = []

summary.append("# Equipment Summary\n")

groups = defaultdict(list)

for item in items:
    groups[item["type"].title()].append(item)

for typ in sorted(groups):

    summary.append(f"## {typ}")

    for obj in groups[typ]:

        tag = obj.get("tag", "")
        desc = obj.get("description", "")
        service = obj.get("service", "")
        obs = obj.get("process_safety_observation", "")

        line = f"- **{tag}** : {desc}"

        if service:
            line += f" ({service})"

        summary.append(line)
        
        if obs:
            summary.append(f"  - *Process Safety: {obs}*")

    summary.append("")

(OUTPUT_DIR / "summary.md").write_text("\n".join(summary))

# ---------------------------------------------------------
# HTML Layout
# ---------------------------------------------------------

page_width = max(t["bbox"][2] for t in tiles)
page_height = max(t["bbox"][3] for t in tiles)

html = []

html.append("""
<!DOCTYPE html>
<html>
<head>

<meta charset="utf-8">

<style>

body{
font-family:Arial;
background:#fafafa;
}

.canvas{
position:relative;
width:1400px;
height:auto;
border:1px solid #999;
background:white;
}

.tile{

position:absolute;

border:2px solid #2c7be5;

background:rgba(44,123,229,0.08);

overflow:hidden;

font-size:12px;

padding:4px;

box-sizing:border-box;
}

.tile h4{

margin:0 0 6px 0;

font-size:13px;

color:#2c7be5;
}

.item{

margin-left:8px;
margin-bottom:3px;
}

.meta{

color:#888;
font-size:10px;
margin-bottom:6px;

}

</style>

</head>

<body>

<h2>P&ID Layout Reconstruction</h2>

<div class="canvas">
""")

scale = 1400 / page_width

for tile in tiles:

    x1, y1, x2, y2 = tile["bbox"]

    left = x1 * scale
    top = y1 * scale
    width = (x2 - x1) * scale
    height = (y2 - y1) * scale

    html.append(
        f"""
<div class="tile"

style="
left:{left}px;
top:{top}px;
width:{width}px;
height:{height}px;
">

<h4>Tile {tile['tile_id']}</h4>

<div class="meta">

Depth {tile['depth']}<br>

{tile['status']}<br>

{tile['reason']}<br>

{tile.get('process_safety_observation', '')}

</div>
"""
    )

    grouped = defaultdict(list)

    for obj in tile["items"]:
        grouped[obj["type"].title()].append(obj)

    for typ in sorted(grouped):

        html.append(f"<b>{typ}</b><br>")

        for obj in grouped[typ]:

            tag = obj.get("tag", "")
            desc = obj.get("description", "")

            html.append(
                f'<div class="item">• <b>{tag}</b> {desc}</div>'
            )

    html.append("</div>")

html.append("""
</div>

</body>
</html>
""")

(OUTPUT_DIR / "layout.html").write_text("\n".join(html))

print("=" * 60)
print("Generated:")
print("  outputs/layout.md")
print("  outputs/summary.md")
print("  outputs/layout.html")
print("=" * 60)
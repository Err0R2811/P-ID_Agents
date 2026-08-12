"""
Adaptive P&ID recursive extractor.

Key ideas
---------
1. The model NEVER chooses the split size.
2. The model only reports:
      - status = complete / incomplete
      - extracted items
      - estimated_missing_items
3. The algorithm decides whether to split.
4. Split size is deterministic from tile size.

Additionally:
-------------
- Stores every raw LLM response with tile metadata in llm_outputs.json
- Stores final deduplicated entities in entities.json
- Every extracted entity contains:
    * tile_bbox
    * depth
    * tile_id
"""

from PIL import Image
from dataclasses import dataclass

@dataclass
class ImageTile:
    image: Image.Image
    bbox: tuple[int, int, int, int]  # (x0, y0, x1, y1) in original image coords

_GRID_LAYOUTS = {
    2: (1, 2),  # rows, cols
    4: (2, 2),
    8: (2, 4),
}

def split_image(image: Image.Image, split: int, overlap: float = 0.0) -> list[ImageTile]:
    """
    Split an image into `split` tiles (2, 4, or 8) arranged in a grid,
    with optional fractional overlap between adjacent tiles.

    Args:
        image: source PIL image
        split: number of tiles — must be 2, 4, or 8
        overlap: fraction of tile width/height to overlap with neighbors (0.0–0.4)

    Returns:
        List of ImageTile, each with the crop and its bbox in original coords.
    """
    if split not in _GRID_LAYOUTS:
        raise ValueError(f"split must be one of {list(_GRID_LAYOUTS)}, got {split}")
    if not (0.0 <= overlap < 0.5):
        raise ValueError("overlap must be in [0, 0.5)")

    rows, cols = _GRID_LAYOUTS[split]
    W, H = image.size
    base_tile_w = W / cols
    base_tile_h = H / rows

    tiles = []
    for r in range(rows):
        for c in range(cols):
            # nominal (non-overlapping) tile bounds
            x0 = c * base_tile_w
            y0 = r * base_tile_h
            x1 = x0 + base_tile_w
            y1 = y0 + base_tile_h

            # expand by overlap, clamped to image bounds
            ox = base_tile_w * overlap
            oy = base_tile_h * overlap
            ex0 = max(0, x0 - ox)
            ey0 = max(0, y0 - oy)
            ex1 = min(W, x1 + ox)
            ey1 = min(H, y1 + oy)

            bbox = (int(ex0), int(ey0), int(ex1), int(ey1))
            crop = image.crop(bbox)
            tiles.append(ImageTile(image=crop, bbox=bbox))

    return tiles

import asyncio
import base64
import io
import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["AGNES_API_KEY"]
BASE_URL = "https://apihub.agnes-ai.com/v1/chat/completions"
MODEL = "agnes-2.0-flash"

MAX_DEPTH = 3
MIN_TILE = 220

LLM_OUTPUTS = []
TILE_COUNTER = 0

# Semaphore for rate limiting concurrent API calls
SEMAPHORE = asyncio.Semaphore(5)

RESPONSE_SCHEMA = {
    "status": "complete or incomplete",
    "estimated_missing_items": "integer",
    "reason": "string (required - explain why status is incomplete)",
    "process_safety_observation": "string (detailed Process Safety Engineer perspective on what you see in this tile)",
    "items": [
        {
            "tag": "string (use canonical TYPE-NNN format, e.g., K-01, PSV-005)",
            "type": "string",
            "description": "string (optional)",
            "line_number": "string (optional)",
            "service": "string (optional)",
            "local_bbox": "[x0, y0, x1, y1] - bounding box of this item within the tile image (0-1 range)"
        }
    ]
}


def img_b64(img):
    b = io.BytesIO()
    img.save(b, format="PNG")
    return base64.b64encode(b.getvalue()).decode()


def has_incomplete_items(items):
    """Check if any item has missing critical fields."""
    return any(not item.get("tag", "").strip() for item in items)


async def call_model(tile):
    """Call the model with rate limiting."""
    async with SEMAPHORE:
        return await _call_model_unsafe(tile)


async def _call_model_unsafe(tile):

    prompt = """
You are reading a Process & Instrumentation Diagram as a Process Safety Engineer.

Extract every readable:
- equipment
- valves
- instruments
- line numbers
- services
- tags

Do NOT guess unreadable text.

Tag format: Use canonical TYPE-NNN format (e.g., K-01, PSV-005, L-004).
Normalize spaces to hyphens and ensure consistent formatting.

For each extracted item, provide its local_bbox as [x0, y0, x1, y1]
where coordinates are in the range [0, 1] representing the item's
position within this tile image.

If you believe additional zoom would reveal NEW entities,
return status="incomplete" and explain why in the reason field.
Otherwise return status="complete".

estimated_missing_items should estimate how many additional
entities deeper zoom could recover.

The reason field is REQUIRED when status is "incomplete".

Process Safety Observation:
Provide a detailed observation from a Process Safety Engineer's perspective.
Describe what you see in this tile, including:
- Process flow and connections
- Safety-critical equipment (relief valves, emergency shutdowns, etc.)
- Potential hazards or safety concerns
- Process conditions (pressure, temperature, level)
- Any unusual or noteworthy arrangements
This should be detailed enough to be converted to markdown format
and explained to other systems or engineers.

Respond ONLY with valid JSON in this format:
{
  "status": "complete" or "incomplete",
  "estimated_missing_items": integer,
  "reason": "string (required when incomplete)",
  "process_safety_observation": "string (detailed Process Safety Engineer perspective)",
  "items": [
    {
      "tag": "string (canonical TYPE-NNN format)",
      "type": "string",
      "description": "string (optional)",
      "line_number": "string (optional)",
      "service": "string (optional)",
      "local_bbox": [x0, y0, x1, y1]
    }
  ]
}
"""

    payload = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64," + img_b64(tile.image)
                    }
                }
            ]
        }]
    }

    timeout = httpx.Timeout(connect=30, read=300, write=30, pool=30)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    for i in range(5):
        try:
            async with httpx.AsyncClient(timeout=timeout) as c:
                r = await c.post(BASE_URL, headers=headers, json=payload)

            if r.status_code == 429:
                await asyncio.sleep(2 ** i)
                continue

            r.raise_for_status()
            return r.json()

        except httpx.ReadTimeout:
            await asyncio.sleep(2 ** i)

    raise RuntimeError("Request failed")


def choose_split(tile):
    longest = max(tile.image.size)

    if longest > 1500:
        return 4
    if longest > 700:
        return 2
    return None


def bboxes_overlap(b1, b2, tolerance=0.1):
    """
    Check if two bounding boxes overlap or are close to each other.
    
    Args:
        b1, b2: Bounding boxes as [x0, y0, x1, y1]
        tolerance: Fraction of bbox size to allow as proximity margin
    
    Returns:
        True if boxes overlap or are within tolerance distance
    """
    x1a, y1a, x2a, y2a = b1
    x1b, y1b, x2b, y2b = b2
    
    # Calculate margin based on bbox size
    width_a = x2a - x1a
    height_a = y2a - y1a
    margin_x = width_a * tolerance
    margin_y = height_a * tolerance
    
    # Check for overlap with margin
    return not (x2a + margin_x < x1b or x2b + margin_x < x1a or 
                y2a + margin_y < y1b or y2b + margin_y < y1a)


def dedupe(items):
    """
    Deduplicate items using spatial overlap-based matching.
    
    Only merges entries whose tags match AND whose global_bboxes are
    spatially close or overlapping. This prevents false merges of
    generic tags (e.g., "HEATER", "MANWAY") that appear in different
    parts of the diagram.
    """
    seen = []
    for x in items:
        # Normalize key: case-insensitive tag and type
        key = (x.get("tag", "").strip().upper(), x.get("type", "").strip().lower())
        
        # Find existing item with same key and spatial overlap
        match = next((s for s in seen if 
                      s["_key"] == key and bboxes_overlap(s["global_bbox"], x["global_bbox"])), None)
        
        if match is None:
            # No spatial match found, keep this item
            x["_key"] = key
            seen.append(x)
        # else: spatial match found, skip this item (deduped)
    
    # Clean up temporary _key field
    for s in seen:
        s.pop("_key", None)
    
    return seen


async def process_tile(tile, depth):

    global TILE_COUNTER

    tile_id = TILE_COUNTER
    TILE_COUNTER += 1

    print(f"Depth={depth} bbox={tile.bbox}")

    response = await call_model(tile)

    message = response["choices"][0]["message"]
    content = message.get("content", "")
    
    if not content:
        print(f"ERROR: Empty response content. Response: {json.dumps(response, indent=2)}")
        raise ValueError("Model returned empty content")
    
    # Try to extract JSON from content (might be wrapped in markdown code blocks)
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    try:
        result = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON from response. Content: {content}")
        print(f"Full response: {json.dumps(response, indent=2)}")
        raise ValueError(f"Invalid JSON in model response: {e}")

    items = []

    for item in result["items"]:
        obj = dict(item)
        obj["tile_bbox"] = list(tile.bbox)
        obj["depth"] = depth
        obj["tile_id"] = tile_id
        
        # Compose local_bbox with tile origin to get global bbox
        if "local_bbox" in item and item["local_bbox"]:
            local_bbox = item["local_bbox"]
            tile_x0, tile_y0, tile_x1, tile_y1 = tile.bbox
            tile_w = tile_x1 - tile_x0
            tile_h = tile_y1 - tile_y0
            
            # Convert from [0,1] to global coordinates
            global_x0 = tile_x0 + local_bbox[0] * tile_w
            global_y0 = tile_y0 + local_bbox[1] * tile_h
            global_x1 = tile_x0 + local_bbox[2] * tile_w
            global_y1 = tile_y0 + local_bbox[3] * tile_h
            obj["global_bbox"] = [global_x0, global_y0, global_x1, global_y1]
        else:
            # Fallback to tile bbox if local_bbox not provided
            obj["global_bbox"] = list(tile.bbox)
        
        items.append(obj)

    LLM_OUTPUTS.append({
        "tile_id": tile_id,
        "depth": depth,
        "bbox": list(tile.bbox),
        "status": result["status"],
        "estimated_missing_items": result["estimated_missing_items"],
        "reason": result.get("reason", ""),
        "process_safety_observation": result.get("process_safety_observation", ""),
        "items": items
    })

    if depth >= MAX_DEPTH:
        return items

    if min(tile.image.size) < MIN_TILE:
        return items

    # Deterministic override: force split if items are obviously incomplete
    force_incomplete = has_incomplete_items(result["items"]) or result["estimated_missing_items"] > 0
    should_split = (result["status"] == "incomplete") or force_incomplete
    
    if not should_split:
        return items

    split = choose_split(tile)

    if split is None:
        return items

    print(
        f"Splitting -> {split}x{split} "
        f"(missing≈{result['estimated_missing_items']})"
    )

    parent_count = len(items)

    merged = list(items)

    children = split_image(
        tile.image,
        split=split,
        overlap=0.10
    )

    print(f"Processing {len(children)} child tiles in parallel...")
    child_results = await asyncio.gather(*[process_tile(child, depth + 1) for child in children])
    for child_items in child_results:
        merged.extend(child_items)

    merged = dedupe(merged)

    gain = len(merged) - parent_count

    print(f"Depth {depth}: gain={gain}")

    return merged


async def run_on_image(image):

    global LLM_OUTPUTS, TILE_COUNTER

    LLM_OUTPUTS = []
    TILE_COUNTER = 0

    tiles = split_image(
        image,
        split=4,
        overlap=0.10
    )

    final = []

    print(f"Processing {len(tiles)} top-level tiles in parallel...")
    results = await asyncio.gather(*[process_tile(t, 0) for t in tiles])
    final = [item for r in results for item in r]

    entities = dedupe(final)

    with open("entities.json", "w") as f:
        json.dump(entities, f, indent=2)

    with open("llm_outputs.json", "w") as f:
        json.dump(LLM_OUTPUTS, f, indent=2)

    return {
        "entities": entities,
        "llm_outputs": LLM_OUTPUTS
    }

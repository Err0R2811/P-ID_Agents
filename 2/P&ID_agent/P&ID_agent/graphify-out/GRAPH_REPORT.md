# Graph Report - P&ID_agent  (2026-07-18)

## Corpus Check
- 2 files · ~49,414 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 19 nodes · 29 edges · 5 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]

## God Nodes (most connected - your core abstractions)
1. `process_tile()` - 7 edges
2. `split_image()` - 5 edges
3. `dedupe()` - 5 edges
4. `call_model()` - 4 edges
5. `run_on_image()` - 4 edges
6. `has_incomplete_items()` - 3 edges
7. `_call_model_unsafe()` - 3 edges
8. `bboxes_overlap()` - 3 edges
9. `ImageTile` - 2 edges
10. `img_b64()` - 2 edges

## Surprising Connections (you probably didn't know these)
- `process_tile()` --calls--> `split_image()`  [EXTRACTED]
  adaptive_pid_recursive_extractor.py → adaptive_pid_recursive_extractor.py  _Bridges community 2 → community 1_
- `process_tile()` --calls--> `has_incomplete_items()`  [EXTRACTED]
  adaptive_pid_recursive_extractor.py → adaptive_pid_recursive_extractor.py  _Bridges community 4 → community 1_
- `process_tile()` --calls--> `call_model()`  [EXTRACTED]
  adaptive_pid_recursive_extractor.py → adaptive_pid_recursive_extractor.py  _Bridges community 0 → community 1_
- `dedupe()` --calls--> `bboxes_overlap()`  [EXTRACTED]
  adaptive_pid_recursive_extractor.py → adaptive_pid_recursive_extractor.py  _Bridges community 3 → community 1_

## Communities

### Community 0 - "Community 0"
Cohesion: 0.47
Nodes (5): call_model(), _call_model_unsafe(), img_b64(), Adaptive P&ID recursive extractor.  Key ideas --------- 1. The model NEVER choos, Call the model with rate limiting.

### Community 1 - "Community 1"
Cohesion: 0.5
Nodes (5): choose_split(), dedupe(), process_tile(), Deduplicate items using spatial overlap-based matching.          Only merges ent, run_on_image()

### Community 2 - "Community 2"
Cohesion: 0.67
Nodes (3): ImageTile, Split an image into `split` tiles (2, 4, or 8) arranged in a grid,     with opti, split_image()

### Community 3 - "Community 3"
Cohesion: 1.0
Nodes (2): bboxes_overlap(), Check if two bounding boxes overlap or are close to each other.          Args:

### Community 4 - "Community 4"
Cohesion: 1.0
Nodes (2): has_incomplete_items(), Check if any item has missing critical fields.

## Knowledge Gaps
- **6 isolated node(s):** `Adaptive P&ID recursive extractor.  Key ideas --------- 1. The model NEVER choos`, `Split an image into `split` tiles (2, 4, or 8) arranged in a grid,     with opti`, `Check if any item has missing critical fields.`, `Call the model with rate limiting.`, `Check if two bounding boxes overlap or are close to each other.          Args:` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 3`** (2 nodes): `bboxes_overlap()`, `Check if two bounding boxes overlap or are close to each other.          Args:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 4`** (2 nodes): `has_incomplete_items()`, `Check if any item has missing critical fields.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `dedupe()` connect `Community 1` to `Community 0`, `Community 3`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Why does `process_tile()` connect `Community 1` to `Community 0`, `Community 2`, `Community 4`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Why does `split_image()` connect `Community 2` to `Community 0`, `Community 1`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **What connects `Adaptive P&ID recursive extractor.  Key ideas --------- 1. The model NEVER choos`, `Split an image into `split` tiles (2, 4, or 8) arranged in a grid,     with opti`, `Check if any item has missing critical fields.` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
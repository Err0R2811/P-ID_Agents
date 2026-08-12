```mermaid
graph TD
    C0["LUBE-TANK-01\n"]
    C1["OIL-FILTER-01\n"]
    C2["OIL-FILTER-02\n"]

    # Main Flow Connections
    C0 --> C1
    C1 --> C2
```

**Flow Chart Legend:**
- Arrows indicate process flow direction
- Parallel components (pumps, filters) show redundancy
- Component tags match P&ID labels
- Descriptions indicate component function

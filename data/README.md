# data

The surveyor's measurement of parcel 1561/1. Read-only.

- `terrain.txt` — the points, one per line: number, Y, X, height.
- `terrain.dwg`, `terrain.pdf` — the drawing, the only record of what each point
  is (boundary corner, fence, tree, road).

Y and X are S-JTSK. Heights are metres above sea level (Bpv). A point with height
0.00 marks a position only, not the ground.

## Plot frame

Survey points in plot coordinates:

```text
x = 489216.00 − Y      # metres, east
y = 1201780.00 − X     # metres, north
z = height             # metres above sea level
```

Check: point 1 → (24.53, 10.44), point 3 → (43.69, 4.25).

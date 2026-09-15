# terrain

The plot in 3D from the survey, with a rough house on it. `uv run view --help`
shows how to run it.

## How the terrain is mapped

- **Ground:** flat triangles between the 140 survey points that have a height,
  with no smoothing. Beyond the plot's edge the triangles get long and thin.
- **Coordinates:** the plot frame in [`data/README.md`](../data/README.md);
  heights are metres above sea level.
- **Fence, trees, old shed:** matched from the survey drawing by height and
  position. The hatched strips on the drawing aren't drawn.
- **Slope:** along three parallel lines 7 m apart, from point 115 by the road up
  to point 5002.
- **Sizes and distances:** flat, as on a map, between the surveyed fence
  corners, not the land-registry boundary.

## The house on the plot

```text
                    north side
road  - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  east fence
        +-------------+---------------------------+------+
        | garage      |        upper floor        | shed |
        | (below)     |                           |      |
        +-------------+-------------+-------------+------+
                                    |   terrace   |
                                    +-------------+
                                          * point 24
        uphill ->
```

Every size, position and level is a flag.

- House: a rectangle, long side up the slope, placed from point 115.
- Garage level at the front, dug into the slope: two cars, a utility room and
  the stairs.
- Upper floor over the rest.
- Shed against the back wall, sharing it.
- Terrace on the south side, facing point 24, short of the back wall.
- Excavation: pits with vertical sides, working space around the buried garage
  and shed walls, footings under outer walls only.

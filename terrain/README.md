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
                    north side: 2.5 m to the house
road  - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  east fence
        +-------------+---------------------------+------+
        | garage      |        upper floor        | shed |  2.9 m
        | (below)     |                           |      |
        +-------------+-------------+-------------+------+
                                    |   terrace   |
                                    +-------------+
                                          * point 24
        uphill ->
```

- House 25 x 10 m, long side up the slope, front wall 15 m up from point 115.
- Garage level 9 m deep, dug into the steep bank, floor at 270.2: two cars, a
  utility room and the stairs.
- Upper floor at 273.2, level with the ground about 33 m up.
- Shed 10 x 2.8 m against the back wall, sharing it, floor at 273.2.
- Terrace 7 x 3 m on the south side, facing point 24, 1 m short of the back wall.
- Excavation: pits with vertical sides, working space around the buried garage
  and shed walls, footings under outer walls only.

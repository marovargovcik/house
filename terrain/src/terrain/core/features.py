"""Survey drawing features by point number, matched to the drawing by height."""

FENCES = (
    (1, 8, 7, 6, 5, 4, 3),  # south
    (3, 17, 18, 21, 36, 38),  # east
    (1, 10, 2),  # west
    (2, 27, 90, 91, 104, 143),  # along the neighbour's house
    (143, 133, 135, 134, 136),  # road side
)

# No fence on the north side.
BOUNDARY = (136, 37, 3, 1, 2, 143)

TREES = (52, 61, 62, 63, 64, 65, 66, 67, 69, 108)

EXISTING_SHED = (73, 70, 78, 110)

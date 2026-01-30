def hScore(maze: Maze) -> int:
    """
    Given an input maze compute its hScore.
    hScore: For each box that is not in a target position compute the
    distance to the furthest target, the score is the accumulated sum
    by each box.
    """
    dist = 0
    for r1, c1 in maze.boxes:
        if (r1, c1) in maze.targets:
            continue

        max_dist = 0
        for r2, c2 in maze.targets:
            max_dist = max(max_dist, abs(r2 - r1) + abs(c2 - c1))
        dist += max_dist
    return dist

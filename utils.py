import hashlib

from engine import parseMaze
from typing import List


def computeHashFromMaze(maze: List[str]) -> str:
    """
    Given an input maze compute its hash representation.
    """
    return hashlib.sha256("\n".join(maze).encode("utf-8")).hexdigest()


def hScore(maze: List[str]) -> int:
    """
    Given an input maze compute its hScore.
    hScore: For each box that is not in a target position compute the
    distance to the furthest target, the score is the accumulated sum
    by each box.
    """
    _, targets, boxes, _ = parseMaze(maze)
    dist = 0
    for r1, c1 in boxes:
        if (r1, c1) in targets:
            continue

        max_dist = 0
        for r2, c2 in targets:
            max_dist = max(max_dist, abs(r2 - r1) + abs(c2 - c1))
        dist += max_dist
    return dist

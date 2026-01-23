import hashlib
import heapq

from utils import parse_maze, is_valid_move, apply_movement, is_goal, undo_movement
from math import inf


def compute_hash_from_maze(maze):
    return hashlib.sha256("\n".join(maze).encode("utf-8")).hexdigest()


def H_Score(maze):
    _, targets, boxes, _ = parse_maze(maze)
    dist = 0
    for r1, c1 in boxes:
        if (r1, c1) in targets:
            continue

        max_dist = 0
        for r2, c2 in targets:
            max_dist = max(max_dist, abs(r2 - r1) + abs(c2 - c1))
        dist += max_dist
    return dist


def compute_previous_step(maze, cameFrom):
    maze_hash = compute_hash_from_maze(maze)
    dir = cameFrom[maze_hash]
    return undo_movement(maze, dir)


def A_Star(maze):
    queue = [(0, maze)]
    cameFrom = {}
    start = compute_hash_from_maze(maze)
    gScore, hScore = {}, {}
    gScore[start] = 0
    hScore[start] = H_Score(maze)

    while queue:
        (steps, maze) = heapq.heappop(queue)
        if is_goal(maze):
            return maze, cameFrom, steps
        source_hash = compute_hash_from_maze(maze)
        for step in ["up", "down", "left", "right"]:
            if is_valid_move(maze, step):
                neigh = apply_movement(maze, step)
                dest_hash = compute_hash_from_maze(neigh)
                tentative_score = gScore[source_hash] + 1
                if tentative_score < gScore.get(dest_hash, inf):
                    cameFrom[dest_hash] = step
                    gScore[dest_hash] = tentative_score
                    fScore = tentative_score + H_Score(neigh)
                    heapq.heappush(queue, (fScore, neigh))

    return None, None

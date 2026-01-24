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


def reconstruct_solution_path(maze, cameFrom, steps):
    solution_path, hash = [], compute_hash_from_maze(maze)
    for _ in range(steps):
        dir, hash = cameFrom[hash]
        solution_path.append(dir)
    return list(reversed(solution_path))


def A_Star(maze):
    cameFrom, gScore, hScore = {}, {}, {}
    start = compute_hash_from_maze(maze)
    gScore[start] = 0
    hScore[start] = H_Score(maze)

    queue = [(0, maze)]
    while queue:
        (steps, maze) = heapq.heappop(queue)
        if is_goal(maze):
            return maze, cameFrom, steps
        source_hash = compute_hash_from_maze(maze)

        for step in ["up", "down", "left", "right"]:
            if not is_valid_move(maze, step):
                continue

            neigh = apply_movement(maze, step)
            dest_hash = compute_hash_from_maze(neigh)
            tentative_score = gScore[source_hash] + 1

            if tentative_score < gScore.get(dest_hash, inf):
                cameFrom[dest_hash] = (step, source_hash)
                gScore[dest_hash] = tentative_score
                fScore = tentative_score + H_Score(neigh)
                heapq.heappush(queue, (fScore, neigh))

    return None, None, None


def Beam_Search(maze, beam_size=5000):
    cameFrom = {}
    start = compute_hash_from_maze(maze)
    visited = set([start])

    queue = [(0, 0, maze)]
    while queue:
        (_, steps, maze) = heapq.heappop(queue)
        if is_goal(maze):
            return maze, cameFrom, steps

        source_hash = compute_hash_from_maze(maze)
        for step in ["up", "down", "left", "right"]:
            if not is_valid_move(maze, step):
                continue

            neigh = apply_movement(maze, step)
            dest_hash = compute_hash_from_maze(neigh)

            if dest_hash in visited:
                continue

            score = H_Score(neigh)
            if queue and len(queue) == beam_size and score > queue[0][0]:
                (_, _, tmp_maze) = heapq.heappop(queue)
                visited.remove(compute_hash_from_maze(tmp_maze))

            if len(queue) < beam_size:
                visited.add(dest_hash)
                cameFrom[dest_hash] = (step, source_hash)
                heapq.heappush(queue, (score, steps + 1, neigh))

    return None, None, None

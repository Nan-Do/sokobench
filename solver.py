import hashlib
import heapq

from utils import parseMaze, isValidMove, applyMovement, isGoal
from math import inf


def computeHashFromMaze(maze):
    return hashlib.sha256("\n".join(maze).encode("utf-8")).hexdigest()


def hScore(maze):
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


def reconstructSolutionPath(maze, cameFrom, steps):
    solution_path, hash = [], computeHashFromMaze(maze)
    for _ in range(steps):
        dir, hash = cameFrom[hash]
        solution_path.append(dir)
    return list(reversed(solution_path))


def aStar(maze):
    came_from, g_score, h_score = {}, {}, {}
    start = computeHashFromMaze(maze)
    g_score[start] = 0
    h_score[start] = hScore(maze)

    queue = [(0, maze)]
    while queue:
        (steps, maze) = heapq.heappop(queue)
        if isGoal(maze):
            return maze, came_from, steps
        source_hash = computeHashFromMaze(maze)

        for step in ["up", "down", "left", "right"]:
            if not isValidMove(maze, step):
                continue

            neigh = applyMovement(maze, step)
            dest_hash = computeHashFromMaze(neigh)
            tentative_score = g_score[source_hash] + 1

            if tentative_score < g_score.get(dest_hash, inf):
                came_from[dest_hash] = (step, source_hash)
                g_score[dest_hash] = tentative_score
                fScore = tentative_score + hScore(neigh)
                heapq.heappush(queue, (fScore, neigh))

    return None, None, None


def beamSearch(maze, beam_size=5000):
    came_from = {}
    start = computeHashFromMaze(maze)
    visited = set([start])

    queue = [(0, 0, maze)]
    while queue:
        (_, steps, maze) = heapq.heappop(queue)
        if isGoal(maze):
            return maze, came_from, steps

        source_hash = computeHashFromMaze(maze)
        for step in ["up", "down", "left", "right"]:
            if not isValidMove(maze, step):
                continue

            neigh = applyMovement(maze, step)
            dest_hash = computeHashFromMaze(neigh)

            if dest_hash in visited:
                continue

            score = hScore(neigh)
            if queue and len(queue) == beam_size and score > queue[0][0]:
                (_, _, tmp_maze) = heapq.heappop(queue)
                visited.remove(computeHashFromMaze(tmp_maze))

            if len(queue) < beam_size:
                visited.add(dest_hash)
                came_from[dest_hash] = (step, source_hash)
                heapq.heappush(queue, (score, steps + 1, neigh))

    return None, None, None

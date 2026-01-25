import heapq

from engine import isValidMove, applyMovement, isGoal
from math import inf
from sortedcontainers import SortedList
from utils import hScore, computeHashFromMaze


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

        for direction in ["up", "down", "left", "right"]:
            if not isValidMove(maze, direction):
                continue

            neigh = applyMovement(maze, direction)
            dest_hash = computeHashFromMaze(neigh)
            tentative_score = g_score[source_hash] + 1

            if tentative_score < g_score.get(dest_hash, inf):
                came_from[dest_hash] = (direction, source_hash)
                g_score[dest_hash] = tentative_score
                fScore = tentative_score + hScore(neigh)
                heapq.heappush(queue, (fScore, neigh))

    return None, None, None


def beamSearch(maze, beam_size=5000):
    came_from = {}
    start = computeHashFromMaze(maze)
    visited = set([start])

    queue = SortedList([(0, 0, maze)])
    while queue:
        (_, steps, maze) = queue[0]
        del queue[0]
        if isGoal(maze):
            return maze, came_from, steps

        source_hash = computeHashFromMaze(maze)
        for direction in ["up", "down", "left", "right"]:
            if not isValidMove(maze, direction):
                continue

            neigh = applyMovement(maze, direction)
            dest_hash = computeHashFromMaze(neigh)

            if dest_hash in visited:
                continue

            score = hScore(neigh)
            if len(queue) == beam_size and score < queue[-1][0]:
                (_, _, tmp_maze) = queue[-1]
                del queue[-1]
                visited.remove(computeHashFromMaze(tmp_maze))

            if len(queue) < beam_size:
                visited.add(dest_hash)
                came_from[dest_hash] = (direction, source_hash)
                queue.add((score, steps + 1, neigh))

    return None, None, None

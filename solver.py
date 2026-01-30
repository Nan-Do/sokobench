import heapq

from engine import isValidMove, applyMovement, isGoal, computeHashFromMaze, Maze
from math import inf
from sortedcontainers import SortedList
from utils import hScore
from typing import List, Dict, Tuple


def reconstructSolutionPath(
    maze: Maze, cameFrom: Dict[str, Tuple[List[str], str]], steps: int
) -> List[str]:
    """
    Given the solution maze and the dictionary of previous states
    reconstruct the solution path.
    It returns a list with strings containing the directions taken
    to achieve the solution:
        Ex: ['up', 'left', ...]
    """
    solution_path, hash = [], computeHashFromMaze(maze)
    for _ in range(steps):
        dir, hash = cameFrom[hash]
        solution_path.append(dir)
    return list(reversed(solution_path))


def aStar(
    maze: Maze,
) -> Tuple[Maze | None, Dict[str, Tuple[List[str], str]] | None, int | None]:
    """
    Perform A* Search on the given maze.
    """

    # Keep reference of the previous state to reconstruct the solution using a dictionary,
    # and use another one to keep the best score for each state.
    came_from, g_score = {}, {}
    # Use hashing of to identify the mazes
    start = computeHashFromMaze(maze)
    g_score[start] = 0

    # Queue to keep track of the most promising state.
    # Implemented using a min heap.
    # The queue contains (steps, maze)
    queue = [(0, maze)]
    while queue:
        (steps, maze) = heapq.heappop(queue)

        # Reached the goal?
        if isGoal(maze):
            return maze, came_from, steps

        source_hash = computeHashFromMaze(maze)

        # Expand the frontier computing the possible next states.
        for direction in ["up", "down", "left", "right"]:
            if not isValidMove(maze, direction):
                continue

            neigh = applyMovement(maze, direction)
            dest_hash = computeHashFromMaze(neigh)
            tentative_score = g_score[source_hash] + 1

            # If the next state is better than  the one previously
            # computed or it doesn't exist take it.
            if tentative_score < g_score.get(dest_hash, inf):
                came_from[dest_hash] = (direction, source_hash)
                g_score[dest_hash] = tentative_score
                fScore = tentative_score + hScore(neigh)
                heapq.heappush(queue, (fScore, neigh))

    return None, None, None


def beamSearch(
    maze: Maze, beam_size: int = 5000
) -> Tuple[Maze | None, Dict[str, Tuple[List[str], str]] | None, int | None]:
    """
    Perform Beam Search on the given maze.
    """

    # Keep reference of the previous state to reconstruct the solution using
    # a dictionary
    came_from = {}
    # Use hashing of to identify the mazes
    start = computeHashFromMaze(maze)
    visited = set([start])

    # Queue to keep track of the most promising state.
    # Implemented using a sorted list.
    # The max size of the queue is given by beam_size.
    # The queue contains (best_score, steps, maze)
    queue = SortedList([(0, 0, maze)])
    while queue:
        (_, steps, maze) = queue[0]
        del queue[0]

        # Reached the goal?
        if isGoal(maze):
            return maze, came_from, steps

        source_hash = computeHashFromMaze(maze)

        # Expand the frontier computing the possible next states.
        for direction in ["up", "down", "left", "right"]:
            if not isValidMove(maze, direction):
                continue

            neigh = applyMovement(maze, direction)
            dest_hash = computeHashFromMaze(neigh)

            if dest_hash in visited:
                continue

            score = hScore(neigh)

            # Check if we need to change an element in the queue.
            if len(queue) == beam_size and score < queue[-1][0]:
                (_, _, tmp_maze) = queue[-1]
                del queue[-1]
                visited.remove(computeHashFromMaze(tmp_maze))

            # Check if we need to add an element to the queue.
            if len(queue) < beam_size:
                visited.add(dest_hash)
                came_from[dest_hash] = (direction, source_hash)
                queue.add((score, steps + 1, neigh))

    return None, None, None

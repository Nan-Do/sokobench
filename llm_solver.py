import heapq

from engine import isValidMove, applyMovement, isGoal, parseMaze
from math import inf, exp, log
from utils import hScore, computeHashFromMaze
from openai import OpenAI
from sortedcontainers import SortedList
from typing import List, Dict, Tuple

symbols = """### Maze Symbols:
- `#`: Wall (Impassable)
- `@`: Player
- `+`: Player standing on a Target
- `$`: Box
- `*`: Box on a Target
- `.`: Target (Goal)
- ` `: Empty floor
""".strip()


def getLlmActionPolicy(
    client: OpenAI, prompt: str, prompt_format: str, maze: List[str]
) -> Dict[str, float]:
    """
    Queries the LLM for the next move and returns a probability distribution
    to guide the Tree Search.
    """

    # Build the prompt with the desired format and the state of the maze
    if prompt_format == "ascii":
        system_prompt = prompt.format(format="formatted ASCII maze", symbols=symbols)
        # User prompt only contains the ascii representation of the maze.
        user_prompt = "### current board:\n{}\n\n### best move:".format("\n".join(maze))
    elif prompt_format == "structured":
        system_prompt = prompt.format(
            format="maze represented with tuples of pairs indicating the coordinates of each element of the game",
            symbols="",
        )
        # User prompt only contains the coordinates of the game elements.
        walls, targets, boxes, player = parseMaze(maze)
        user_prompt = '### coordinates:\n"player": {}\n"walls": {}\n"boxes": {}\n"targets": {}\n\n### best move:'.format(
            player,
            walls,
            boxes,
            targets,
        )
    else:  # Both
        system_prompt = prompt.format(
            format="formatted ASCII maze annotated with tuples of pairs indicating the coordinates for each element of the game",
            symbols=symbols,
        )
        # User prompt contains ascii and coordinates of the game elements.
        walls, targets, boxes, player = parseMaze(maze)
        user_prompt = '### current board:\n{}\n\n### coordinates:\n"player": {}\n"walls": {}\n"boxes": {}\n"targets": {}\n\n### best move:'.format(
            "\n".join(maze),
            player,
            walls,
            boxes,
            targets,
        )

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {"role": "user", "content": user_prompt},
    ]

    response = client.chat.completions.create(
        model="llama-7b",  # Name doesn't matter much for local server
        messages=messages,
        temperature=0.0,
        max_tokens=1,  # Constraint: Single step predictor
        logprobs=True,
        top_logprobs=5,  # Get top tokens to see all direction probabilities
    )

    token_logprobs = response.choices[0].logprobs.content[0].top_logprobs

    policy = {"Up": 0.0, "Down": 0.0, "Left": 0.0, "Right": 0.0}
    for token_data in token_logprobs:
        token_str = token_data.token.strip()  # Remove leading spaces
        if token_str in policy:
            # Convert logprob to linear probability: e^logprob
            policy[token_str] = exp(token_data.logprob)

    # Normalize probabilities
    total_prob = sum(policy.values())
    if total_prob > 0:
        policy = {k: v / total_prob for k, v in policy.items()}

    return policy


def llmBeamSearch(
    client: OpenAI,
    prompt: str,
    prompt_format: str,
    maze: List[str],
    alpha: float = 1.0,
    beam_size: int = 5000,
) -> Tuple[List[str] | None, Dict[str, Tuple[List[str], str]] | None, int | None]:
    """
    Perform LLM guided Beam Search on the given maze.
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

        # Get the probabilities for the next movement using the LLM
        policy = getLlmActionPolicy(client, prompt, prompt_format, maze)
        for direction, prob in policy.items():
            direction = direction.lower()
            if not isValidMove(maze, direction):
                continue

            neigh = applyMovement(maze, direction)
            dest_hash = computeHashFromMaze(neigh)

            if dest_hash in visited:
                continue

            # Score function:
            # We modify the score based on the confidence given to the model
            # prediction.
            score = hScore(neigh) - (alpha * log(prob + 0.0000001))

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


def llmAStar(
    client: OpenAI,
    prompt: str,
    prompt_format: str,
    maze: List[str],
    alpha: float = 1.0,
) -> Tuple[List[str] | None, Dict[str, Tuple[List[str], str]] | None, int | None]:
    """
    Perform LLM guided A* Search on the given maze.
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

        # Get the probabilities for the next movement
        policy = getLlmActionPolicy(client, prompt, prompt_format, maze)
        for direction, prob in policy.items():
            direction = direction.lower()
            if not isValidMove(maze, direction):
                continue

            neigh = applyMovement(maze, direction)
            dest_hash = computeHashFromMaze(neigh)
            tentative_score = g_score[source_hash] + 1

            if tentative_score < g_score.get(dest_hash, inf):
                came_from[dest_hash] = (direction, source_hash)
                g_score[dest_hash] = tentative_score
                # Score function:
                # We modify the heuristic score based on the
                # confidence given to the model prediction.
                fScore = tentative_score + int(
                    hScore(neigh) - (alpha * log(prob + 0.0000001))
                )
                heapq.heappush(queue, (fScore, neigh))

    return None, None, None

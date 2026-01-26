import heapq

from engine import isValidMove, applyMovement, isGoal, parseMaze
from math import inf, exp, log
from utils import hScore, computeHashFromMaze
from sortedcontainers import SortedList

symbols = """### Maze Symbols:
- `#`: Wall (Impassable)
- `@`: Player
- `+`: Player standing on a Target
- `$`: Box
- `*`: Box on a Target
- `.`: Target (Goal)
- ` `: Empty floor
""".strip()


def getLlmActionPolicy(client, prompt, prompt_format, maze):
    """
    Queries the LLM for the next move and returns a probability distribution
    to guide the Tree Search.
    """
    if prompt_format == "ascii":
        system_prompt = prompt.format(format="formatted ASCII maze", symbols=symbols)
        user_prompt = "### current board:\n{}\n\n### best move:".format("\n".join(maze))
    elif prompt_format == "structured":
        system_prompt = prompt.format(
            format="maze represented with tuples of pairs indicating the coordinates of each element of the game",
            symbols="",
        )
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


def llmBeamSearch(client, prompt, prompt_format, maze, alpha=1.0, beam_size=5000):
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
        policy = getLlmActionPolicy(client, prompt, prompt_format, maze)
        for direction, prob in policy.items():
            direction = direction.lower()
            if not isValidMove(maze, direction):
                continue

            neigh = applyMovement(maze, direction)
            dest_hash = computeHashFromMaze(neigh)

            if dest_hash in visited:
                continue

            # score = hScore(neigh) * log(1 / (prob + 0.0000001))
            score = hScore(neigh) - (alpha * log(prob + 0.0000001))
            if len(queue) == beam_size and score < queue[-1][0]:
                (_, _, tmp_maze) = queue[-1]
                del queue[-1]
                visited.remove(computeHashFromMaze(tmp_maze))

            if len(queue) < beam_size:
                visited.add(dest_hash)
                came_from[dest_hash] = (direction, source_hash)
                queue.add((score, steps + 1, neigh))

    return None, None, None


def llmAStar(client, prompt, prompt_format, maze, alpha=1.0):
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
                # fScore = tentative_score + int(
                #     hScore(neigh) * log(1 / (prob + 0.0000001))
                # )
                fScore = tentative_score + int(
                    hScore(neigh) - (alpha * log(prob + 0.0000001))
                )
                heapq.heappush(queue, (fScore, neigh))

    return None, None, None

import heapq

from engine import isValidMove, applyMovement, isGoal
from math import inf, exp
from utils import hScore, computeHashFromMaze
from sortedcontainers import SortedList


def getLlmActionPolicy(client, prompt, maze):
    """
    Queries the LLM for the next move and returns a probability distribution
    to guide the Tree Search.
    """

    # 1. Construct the messages
    messages = [
        {
            "role": "system",
            "content": prompt,
        },
        {
            "role": "user",
            "content": f"### Current Board:\n{maze}\n\n### Best Move:",
        },
    ]

    # 2. Call the API with logprobs enabled
    # We need logprobs to use as weights for A*/Beam Search
    response = client.chat.completions.create(
        model="llama-7b",  # Name doesn't matter much for local server
        messages=messages,
        temperature=0.0,  # Deterministic for best single prediction
        max_tokens=1,  # Constraint: Single step predictor [cite: 25]
        logprobs=True,  # Essential for search guidance
        top_logprobs=5,  # Get top tokens to see all direction probabilities
    )

    # 3. Parse the result for Search Integration
    # We want to extract the probability of Up, Down, Left, Right
    token_logprobs = response.choices[0].logprobs.content[0].top_logprobs

    policy = {"Up": 0.0, "Down": 0.0, "Left": 0.0, "Right": 0.0}
    for token_data in token_logprobs:
        token_str = token_data.token.strip()  # Remove leading spaces
        if token_str in policy:
            # Convert logprob to linear probability: e^logprob
            policy[token_str] = exp(token_data.logprob)

    # Normalize probabilities (optional, but good for search heuristics)
    total_prob = sum(policy.values())
    if total_prob > 0:
        policy = {k: v / total_prob for k, v in policy.items()}

    return policy


def llmBeamSearch(client, prompt, maze, beam_size=5000):
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
        policy = getLlmActionPolicy(client, prompt, maze)
        for direction, prob in policy.items():
            direction = direction.lower()
            if not isValidMove(maze, direction):
                continue

            neigh = applyMovement(maze, direction)
            dest_hash = computeHashFromMaze(neigh)

            if dest_hash in visited:
                continue

            score = hScore(neigh) * (1 / (prob + 0.0000001))
            if len(queue) == beam_size and score < queue[-1][0]:
                (_, _, tmp_maze) = queue[-1]
                del queue[-1]
                visited.remove(computeHashFromMaze(tmp_maze))

            if len(queue) < beam_size:
                visited.add(dest_hash)
                came_from[dest_hash] = (direction, source_hash)
                queue.add((score, steps + 1, neigh))

    return None, None, None


def llmAStar(client, prompt, maze):
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

        policy = getLlmActionPolicy(client, prompt, maze)
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
                fScore = tentative_score + int(hScore(neigh) * (1 / (prob + 0.0000001)))
                heapq.heappush(queue, (fScore, neigh))

    return None, None, None

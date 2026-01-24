from rich import print
from time import sleep
from typing import Set, Tuple

# Symbol Definitions
WALL_CHARS = {"#"}
TARGET_CHARS = {".", "+", "*"}
BOX_CHARS = {"$", "*"}
PLAYER_CHARS = {"@", "+"}


def read_mazes(fname: str):
    with open(fname) as f:
        lines = f.readlines()

    mazes = []
    curr_line = 0
    while curr_line < len(lines):
        if lines[curr_line][0] != ";":
            print(
                f"Error: Inconsistent format detected in the mazes file at line {curr_line + 1}, please review the file"
            )
        curr_line += 2
        maze = []
        while curr_line < len(lines) and lines[curr_line].strip():
            maze.append(lines[curr_line][:-1])
            curr_line += 1
        mazes.append(maze)
        curr_line += 1

    return mazes


def parse_maze(
    maze: list[str],
) -> Tuple[
    Set[Tuple[int, int]],  # Walls
    Set[Tuple[int, int]],  # Targets
    Set[Tuple[int, int]],  # Boxes
    Tuple[int, int],  # Player
]:
    walls: Set[Tuple[int, int]] = set()
    targets: Set[Tuple[int, int]] = set()
    boxes: Set[Tuple[int, int]] = set()
    player: Tuple[int, int] = (0, 0)

    for r, row in enumerate(maze):
        for c, char in enumerate(row):
            if char in WALL_CHARS:
                walls.add((r, c))

            if char in BOX_CHARS:
                boxes.add((r, c))

            if char in TARGET_CHARS:
                targets.add((r, c))

            if char in PLAYER_CHARS:
                player = (r, c)

    # print(f"Player: {player}")
    return walls, targets, boxes, player


def is_goal(maze: list[str]):
    _, targets, boxes, _ = parse_maze(maze)
    return targets == boxes


def undo_movement(maze: list[str], direction) -> list[str]:
    """
    Undo the given movement to the current maze, return a copy of the maze
    with the movement applied
    """

    tmp_maze = [list(maze[row]) for row in range(len(maze))]
    _, _, _, (r, c) = parse_maze(maze)
    # Translate the direction into a valid movement
    if direction == "up":
        dr, dc = -1, 0
    elif direction == "down":
        dr, dc = 1, 0
    elif direction == "left":
        dr, dc = 0, -1
    elif direction == "right":
        dr, dc = 0, 1
    else:
        # print("Unknown direction")
        return []

    pr, pc = r - dr, c - dc
    # Change the player's origin cell.
    if tmp_maze[r][c] == "+":
        tmp_maze[r][c] = "."
    else:
        tmp_maze[r][c] = " "

    # Change the player's destination cell.
    if tmp_maze[pr][pc] == ".":
        tmp_maze[pr][pc] = "+"
    else:
        tmp_maze[pr][pc] = "@"

    br, bc = r + dr, c + dc
    if tmp_maze[br][bc] in BOX_CHARS:
        # Change the origin box cell
        if tmp_maze[br][bc] == "*":
            tmp_maze[br][bc] = "."
        else:
            tmp_maze[br][bc] = " "

        # Change the destination box cell
        if tmp_maze[r][c] == ".":
            tmp_maze[r][c] = "*"
        else:
            tmp_maze[r][c] = "$"

    return list(map(lambda row: "".join(row), tmp_maze))


def apply_movement(maze: list[str], direction: str) -> list[str]:
    """
    Apply the given movement to the current maze, return a copy of the maze
    with the movement applied
    """

    tmp_maze = [list(maze[row]) for row in range(len(maze))]
    _, _, _, (r, c) = parse_maze(maze)
    # Translate the direction into a valid movement
    if direction == "up":
        dr, dc = -1, 0
    elif direction == "down":
        dr, dc = 1, 0
    elif direction == "left":
        dr, dc = 0, -1
    elif direction == "right":
        dr, dc = 0, 1
    else:
        # print("Unknown direction")
        return []

    pr, pc = r + dr, c + dc
    # Check if the player is moving a box
    if tmp_maze[pr][pc] in BOX_CHARS:
        br, bc = pr + dr, pc + dc
        # Change the origin box cell
        if tmp_maze[pr][pc] == "*":
            tmp_maze[pr][pc] = "."
        else:
            tmp_maze[pr][pc] = " "

        # Change the destination box cell
        if tmp_maze[br][bc] == ".":
            tmp_maze[br][bc] = "*"
        else:
            tmp_maze[br][bc] = "$"

    # Change the player's origin cell.
    if tmp_maze[r][c] == "+":
        tmp_maze[r][c] = "."
    else:
        tmp_maze[r][c] = " "

    # Change the player's destination cell.
    if tmp_maze[pr][pc] == ".":
        tmp_maze[pr][pc] = "+"
    else:
        tmp_maze[pr][pc] = "@"

    return list(map(lambda row: "".join(row), tmp_maze))


def is_valid_move(maze: list[str], direction: str) -> bool:
    """
    Check if the given direction can be applied to the current maze
    """

    # Parse the maze
    walls, _, _, (r, c) = parse_maze(maze)

    # Translate the direction into a valid movement
    if direction == "up":
        dr, dc = -1, 0
    elif direction == "down":
        dr, dc = 1, 0
    elif direction == "left":
        dr, dc = 0, -1
    elif direction == "right":
        dr, dc = 0, 1
    else:
        # print("Unknown direction")
        return False

    # Check that the player doesn't move into an invalid position.
    pr, pc = r + dr, c + dc
    # print(f"From ({r}, {c}): {maze[r][c]}; To ({pr}, {pc}): {maze[pr][pc]}")
    if maze[pr][pc] in WALL_CHARS:
        return False

    # If the player is pushing a box check that the box can be moved.
    if maze[pr][pc] in BOX_CHARS:
        br, bc = pr + dr, pc + dc
        if (
            (maze[br][bc] in WALL_CHARS)  # There is a wall in the final destination.
            or (maze[br][bc] in BOX_CHARS)  # There is a box in the final destination.
        ):
            return False

    return True


def show_solution_path(maze, solution_path):
    for dir in solution_path:
        print_maze(maze)
        print("\n====================\n")
        if not is_valid_move(maze, dir):
            print("Invalid movement in the solution_path")
            return
        maze = apply_movement(maze, dir)
        sleep(0.3)
    print_maze(maze)


def print_maze(maze: list[str]):
    for row in maze:
        enriched_str = []
        for char in row:
            if char == "#":
                enriched_str.append("[bold]#[/bold]")
            elif char == "*":
                enriched_str.append("[bold green]*[/bold green]")
            elif char == ".":
                enriched_str.append("[green].[/green]")
            elif char == "$":
                enriched_str.append("[bold magenta]$[/bold magenta]")
            elif char in ["+", "@"]:
                enriched_str.append(f"[bold blue]{char}[/bold blue]")
            else:
                enriched_str.append(char)
        print("".join(enriched_str))

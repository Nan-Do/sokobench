from rich import print
from sys import stdout
from time import sleep
from typing import Set, Tuple, List

# Symbol Definitions
WALL_CHARS = {"#"}
TARGET_CHARS = {".", "+", "*"}
BOX_CHARS = {"$", "*"}
PLAYER_CHARS = {"@", "+"}


def readMazes(fname: str) -> List[List[str]]:
    """
    Parse the file containing the Microban mazes.
    fname must be the path to the file containing the mazes.
    It returns a list with all the mazes parsed.
    """

    with open(fname) as f:
        lines = f.readlines()

    mazes = []
    curr_line = 0
    while curr_line < len(lines):
        # The first parsing line must contain a ";", otherwise return an error
        if lines[curr_line][0] != ";":
            print(
                f"Error: Inconsistent format detected in the mazes file at line {curr_line + 1}, please review the file"
            )
        # Skip the initial ';' and the following line which is empty.
        curr_line += 2
        maze = []

        # Read lines until we detect an empty line
        while curr_line < len(lines) and lines[curr_line].strip():
            maze.append(lines[curr_line][:-1])
            curr_line += 1

        # Add the parsed maze to the list
        mazes.append(maze)
        # Skip the empty line
        curr_line += 1

    return mazes


def parseMaze(
    maze: list[str],
) -> Tuple[
    Set[Tuple[int, int]],  # Walls
    Set[Tuple[int, int]],  # Targets
    Set[Tuple[int, int]],  # Boxes
    Tuple[int, int],  # Player
]:
    """
    Parse a maze represented as a list of strings:
    Ex:
       [['#####'],
        ['#@$.#'],
        ['#####']]

    It returns a tuple with set of positions for the elements of the game.
    Each set contains pairs of tuples in the form (r, c).
    For example:
    If walls contains the tuple (2, 3) it means there's a wall in the maze
    in the second row and third position.
    The game elements it returns are:
        walls, targets, boxes, player
    Player is not a set but a single tuple.
    """

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

    return walls, targets, boxes, player


def isGoal(maze: list[str]):
    """
    Check if a maze is solved.
    """

    _, targets, boxes, _ = parseMaze(maze)
    return targets == boxes


def undoMovement(maze: list[str], direction) -> list[str]:
    """
    Undo the given movement to the current maze, return a copy of the maze
    with the movement applied.
    """

    tmp_maze = [list(maze[row]) for row in range(len(maze))]
    _, _, _, (r, c) = parseMaze(maze)
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


def applyMovement(maze: list[str], direction: str) -> list[str]:
    """
    Apply the given movement to the current maze, return a copy of the maze
    with the movement applied.
    """

    tmp_maze = [list(maze[row]) for row in range(len(maze))]
    _, _, _, (r, c) = parseMaze(maze)
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


def isValidMove(maze: list[str], direction: str) -> bool:
    """
    Check if the given direction can be applied to the current maze
    """

    # Parse the maze
    walls, _, _, (r, c) = parseMaze(maze)

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


def animateSolutionPath(maze: List[str], solution_path: str) -> None:
    """
    Given a maze and a string with directions that solve the maze
    make an animation solving the maze.
    """

    for dir in solution_path:
        # Clean the screen
        stdout.write("\033[2J\033[H")
        stdout.flush()
        printMaze(maze)
        print("\n\n")
        if not isValidMove(maze, dir):
            print("Invalid movement in the solution_path")
            return
        maze = applyMovement(maze, dir)
        sleep(0.3)
    stdout.write("\033[2J\033[H")
    stdout.flush()
    printMaze(maze)


def printMaze(maze: list[str]) -> None:
    """
    Given a maze pretty print it.
    """

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


def isValidSuccesor(prev: list[str], curr: list[str]) -> bool:
    """
    Validates if 'curr' is a legal next state from 'prev' based on Sokoban rules.
    """

    # Basic dimension checks
    if len(prev) != len(curr) or not prev:
        return False
    rows = len(prev)
    if any(len(prev[i]) != len(curr[i]) for i in range(rows)):
        return False

    # Parse the mazes
    prev_walls, prev_targets, prev_boxes, prev_player = parseMaze(prev)
    curr_walls, curr_targets, curr_boxes, curr_player = parseMaze(curr)

    # Validate static elements (walls & targets cannot change)
    if prev_walls != curr_walls or prev_targets != curr_targets:
        return False

    # Check the player exists in both mazes
    if not prev_player or not curr_player:
        return False

    pr, pc = prev_player
    cr, cc = curr_player
    dr, dc = cr - pr, cc - pc

    # Must move exactly 1 square orthogonally
    if abs(dr) + abs(dc) != 1:
        return False

    # Player cannot move into a wall
    if curr_player in curr_walls:
        return False

    # validate box interaction
    expected_boxes = prev_boxes.copy()

    # Check if player moved into a box
    if curr_player in prev_boxes:
        # Calculate where the box should be pushed to
        box_dest = (cr + dr, cc + dc)

        # Box cannot be pushed into a wall
        if box_dest in curr_walls:
            return False

        # Box cannot be pushed into another box
        if box_dest in prev_boxes:
            return False

        # Update expected box positions
        expected_boxes.remove(curr_player)  # Remove box from where player is now
        expected_boxes.add(box_dest)  # Add box to new destination

    # Final state match
    # The boxes in 'curr' must match our calculated expectations exactly.
    # This ensures no other boxes magically moved or disappeared.
    return curr_boxes == expected_boxes

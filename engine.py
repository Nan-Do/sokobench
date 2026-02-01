import hashlib

from rich import print
from sys import stdout
from time import sleep
from typing import FrozenSet, Set, Tuple, List, NamedTuple

# Symbol Definitions
WALL_CHARS = {"#"}
TARGET_CHARS = {".", "+", "*"}
BOX_CHARS = {"$", "*"}
PLAYER_CHARS = {"@", "+"}


class Maze(NamedTuple):
    walls: FrozenSet[Tuple[int, int]]
    targets: FrozenSet[Tuple[int, int]]
    boxes: Set[Tuple[int, int]]
    player: Tuple[int, int]
    rows: int
    columns: int


def getChar(maze: Maze, row: int, column: int) -> Tuple[char, string]:
    """
    Given a position in the maze return its character representation
    and its rich color representation
    """

    if (row, column) in maze.walls:
        return "#", "[bold]#[/bold]"

    elif (row, column) in maze.boxes and (row, column) in maze.targets:
        return "*", "[bold green]*[/bold green]"

    elif (row, column) == maze.player and (row, column) in maze.targets:
        return "+", "[bold blue]+[/bold blue]"

    elif (row, column) in maze.targets:
        return ".", "[green].[/green]"

    elif (row, column) in maze.boxes:
        return "$", "[bold magenta]$[/bold magenta]"

    elif (row, column) == maze.player:
        return "@", "[bold blue]@[/bold blue]"

    return " ", " "


def copy_maze(maze: Maze, player: Tuple[int, int] | None = None) -> Maze:
    """
    Make a copy of the input maze, if a position of the player is
    given as parameter it will be used instead the position of the
    original position for the player.
    """

    if not player:
        player = maze.player

    return Maze(
        maze.walls,
        maze.targets,
        maze.boxes.copy(),
        player,
        maze.rows,
        maze.columns,
    )


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
        mazes.append(parseMaze((maze)))
        # Skip the empty line
        curr_line += 1

    return mazes


def parseMaze(
    maze: list[str],
) -> Maze:
    """
    Parse a maze represented as a list of strings:
    Ex:
       [['#####'],
        ['#@$.#'],
        ['#####']]

    It returns a namedtuple (Maze) with set of positions for the elements of
    the game. Each set contains pairs of tuples in the form (r, c).
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
    max_col = 0

    for r, row in enumerate(maze):
        max_col = max(max_col, len(row))
        for c, char in enumerate(row):
            if char in WALL_CHARS:
                walls.add((r, c))

            if char in BOX_CHARS:
                boxes.add((r, c))

            if char in TARGET_CHARS:
                targets.add((r, c))

            if char in PLAYER_CHARS:
                player = (r, c)

    return Maze(frozenset(walls), frozenset(targets), boxes, player, len(maze), max_col)


def isGoal(maze: Maze) -> bool:
    """
    Check if a maze is solved.
    """

    return maze.targets == maze.boxes


def undoMovement(maze: Maze, direction) -> Maze | None:
    """
    Undo the given movement to the current maze, return a copy of the maze
    with the movement applied.
    """

    # !TODO: Finish the undoMovement implementation
    return None


def applyMovement(maze: Maze, direction: str) -> Maze:
    """
    Apply the given movement to the current maze, return a copy of the maze
    with the movement applied.
    """
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
        dr, dc = 0, 0

    r, c = maze.player
    pr, pc = r + dr, c + dc
    new_maze = copy_maze(maze, (pr, pc))

    # Check if the player is moving a box
    if (pr, pc) in maze.boxes:
        new_maze.boxes.remove((pr, pc))
        br, bc = pr + dr, pc + dc
        new_maze.boxes.add((br, bc))

    return new_maze


def isValidMove(maze: Maze, direction: str) -> bool:
    """
    Check if the given direction can be applied to the current maze
    """
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
        return False

    r, c = maze.player
    # Check that the player doesn't move into an invalid position.
    pr, pc = r + dr, c + dc
    if (pr, pc) in maze.walls:
        return False

    # If the player is pushing a box check that the box can be moved.
    if (pr, pc) in maze.boxes:
        br, bc = pr + dr, pc + dc
        if (
            (br, bc) in maze.walls  # There is a wall in the final destination.
            or (br, bc) in maze.boxes  # There is a box in the final destination.
        ):
            return False

    return True


def animateSolutionPath(maze: Maze, solution_path: str) -> None:
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


def renderMaze(maze: Maze) -> str:
    """
    Turn the input maze into an ascii representation of the maze.
    """

    rendered_maze = []
    for row in range(maze.rows):
        enriched_str = [" "] * maze.columns
        for column in range(maze.columns):
            character, _ = getChar(maze, row, column)
            enriched_str[column] = character

        rendered_maze.append("".join(enriched_str))

    return "\n".join(rendered_maze)


def printMaze(maze: Maze) -> None:
    """
    Given a maze pretty print it.
    """

    for row in range(maze.rows):
        enriched_str = [" "] * maze.columns
        for column in range(maze.columns):
            _, enriched_character = getChar(maze, row, column)
            enriched_str[column] = enriched_character

        print("".join(enriched_str))


def computeHashFromMaze(maze: Maze) -> str:
    """
    Given an input maze compute its hash representation.
    """

    return hashlib.sha256(renderMaze(maze).encode("utf-8")).hexdigest()


def isValidSuccesor(prev: Maze, curr: Maze) -> bool:
    """
    Validates if 'curr' is a legal next state from 'prev' based on Sokoban rules.
    """

    # Basic dimension checks
    if prev.columns != curr.columns or prev.rows != curr.rows:
        return False

    # Validate static elements (walls & targets cannot change)
    if prev.walls != curr.walls or prev.targets != curr.targets:
        return False

    # Check the player exists in both mazes
    if not prev.player or not curr.player:
        return False

    pr, pc = prev.player
    cr, cc = curr.player
    dr, dc = cr - pr, cc - pc

    # Must move exactly 1 square orthogonally
    if abs(dr) + abs(dc) != 1:
        return False

    # Player cannot move into a wall
    if curr.player in curr.walls:
        return False

    # validate box interaction
    expected_boxes = prev.boxes.copy()

    # Check if player moved into a box
    if curr.player in prev.boxes:
        # Calculate where the box should be pushed to
        box_dest = (cr + dr, cc + dc)

        # Box cannot be pushed into a wall
        if box_dest in curr.walls:
            return False

        # Box cannot be pushed into another box
        if box_dest in prev.boxes:
            return False

        # Update expected box positions
        expected_boxes.remove(curr.player)  # Remove box from where player is now
        expected_boxes.add(box_dest)  # Add box to new destination

    # Final state match
    # The boxes in 'curr' must match our calculated expectations exactly.
    # This ensures no other boxes magically moved or disappeared.
    return curr.boxes == expected_boxes

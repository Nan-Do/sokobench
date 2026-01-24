import argparse
import tty
import termios

from solver import aStar, beamSearch, reconstructSolutionPath
from sys import stdin, stdout, exit
from engine import (
    readMazes,
    printMaze,
    isValidMove,
    applyMovement,
    isGoal,
    showSolutionPath,
)


def getKey():
    fd = stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(stdin.fileno())
        key = stdin.read(1)
        if key == "\x1b":  # Escape character
            key += stdin.read(2)  # Read the next two characters (e.g., [A for up)
        return key
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agentic solver for Sokoban puzzles.")

    parser.add_argument(
        "-f",
        "--input_file",
        metavar="input_file",
        help="File containinig the description of the mazes in textual format.",
        required=True,
        type=str,
    )

    parser.add_argument(
        "-n",
        "--number",
        metavar="number",
        help="Number of the maze to solve.",
        required=True,
        type=int,
    )

    parser.add_argument(
        "-p",
        "--play",
        help="Play to the game manually.",
        action="store_true",
    )

    parser.add_argument(
        "-s",
        "--solver",
        choices=["a", "b"],
        help="Solve the maze using the specified algorithm (a:A*, b:Beam Search).",
    )

    parser.add_argument(
        "-a",
        "--animation",
        help="Show an animation of how the maze is solved (requires the -s option).",
        action="store_true",
    )
    args = parser.parse_args()
    input_file = args.input_file
    idx_maze = args.number
    play_game = args.play
    solve_game = args.solver
    show_animation = args.animation

    mazes = readMazes(input_file)
    print(f"Number of mazes: {len(mazes)}")
    if not 1 <= idx_maze <= len(mazes):
        print(f"Please select a number between 1 and {len(mazes)}")
        exit(0)

    maze = mazes[idx_maze - 1]
    original_maze = [row[:] for row in maze]
    if solve_game:
        if solve_game == "a":
            print("Solving the maze using A*.")
            goal_maze, came_from, steps = aStar(maze)
        else:
            print("Solving the maze using Beam Search.")
            goal_maze, came_from, steps = beamSearch(maze)

        if show_animation:
            solution_path = reconstructSolutionPath(goal_maze, came_from, steps)
            showSolutionPath(original_maze, solution_path)

        print(f"Solved in {steps} steps, {len(came_from)} states explored")

    if play_game:
        while True:
            stdout.write("\033[2J\033[H")
            stdout.flush()
            printMaze(maze)
            print("Movement (↑,↓,←,→,r:reset,q:quit):", end=" ", flush=True)

            dir = "no"
            char = getKey()
            print()
            if char in ["k", "K", "\x1b[A"]:
                dir = "up"
            if char in ["j", "J", "\x1b[B"]:
                dir = "down"
            if char in ["l", "L", "\x1b[C"]:
                dir = "right"
            if char in ["h", "H", "\x1b[D"]:
                dir = "left"
            elif char in ["r", "R"]:
                maze = [row[:] for row in original_maze]
            elif char == "q":
                break

            if not isValidMove(maze, dir):
                print(f"Error applying {dir}")
                continue

            maze = applyMovement(maze, dir)
            if isGoal(maze):
                stdout.write("\033[2J\033[H")
                stdout.flush()
                printMaze(maze)
                print("Goal reached!!!")
                break

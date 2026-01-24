import argparse
import sys
import tty
import termios

from solver import A_Star, Beam_Search, reconstruct_solution_path
from utils import (
    read_mazes,
    print_maze,
    is_valid_move,
    apply_movement,
    is_goal,
    show_solution_path,
)


def get_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        key = sys.stdin.read(1)
        if key == "\x1b":  # Escape character
            key += sys.stdin.read(2)  # Read the next two characters (e.g., [A for up)
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
        help="Number of the maze to solve",
        required=True,
        type=int,
    )

    parser.add_argument(
        "-p",
        "--play",
        help="Play to the game manually",
        action="store_true",
    )

    parser.add_argument(
        "-s",
        "--solve",
        help="Solve the maze automatically",
        action="store_true",
    )

    args = parser.parse_args()
    input_file = args.input_file
    idx_maze = args.number
    play_game = args.play
    solve_game = args.solve

    mazes = read_mazes(input_file)
    print(f"Number of mazes: {len(mazes)}")
    if not 1 <= idx_maze <= len(mazes):
        print(f"Please select a number between 1 and {len(mazes)}")
        sys.exit(0)

    maze = mazes[idx_maze - 1]
    original_maze = [row[:] for row in maze]
    if solve_game:
        # goal_maze, cameFrom, steps = A_Star(maze)
        goal_maze, cameFrom, steps = Beam_Search(maze)
        print(f"Solved in {steps} steps, {len(cameFrom)} states explored")
        solution_path = reconstruct_solution_path(goal_maze, cameFrom, steps)
        show_solution_path(original_maze, solution_path)

    if play_game:
        while True:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()
            print_maze(maze)
            print("Movement (↑,↓,←,→,r:reset,q:quit):", end=" ", flush=True)

            dir = "no"
            char = get_key()
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

            if not is_valid_move(maze, dir):
                print(f"Error applying {dir}")
                continue

            maze = apply_movement(maze, dir)
            if is_goal(maze):
                sys.stdout.write("\033[2J\033[H")
                sys.stdout.flush()
                print_maze(maze)
                print("Goal reached!!!")
                break

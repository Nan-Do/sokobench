import argparse
import tty
import termios

from solver import aStar, beamSearch, reconstructSolutionPath
from llm_solver import llmAStar, llmBeamSearch
from sys import stdin, stdout, exit
from engine import (
    readMazes,
    printMaze,
    isValidMove,
    applyMovement,
    isGoal,
    animateSolutionPath,
)
from openai import OpenAI


def getKey():
    """
    Parse input keys for playing the sokoban game manually.
    The function doesn't require to press enter to record the key press and
    can handle the introduction of the arrow keys.
    """
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
    # Define the argument parser
    parser = argparse.ArgumentParser(description="Agentic solver for Sokoban puzzles.")

    parser.add_argument(
        "-i",
        "--input_file",
        metavar="input_file",
        help="file containinig the description of the mazes in textual format.",
        required=True,
        type=str,
    )

    parser.add_argument(
        "-n",
        "--number",
        metavar="number",
        help="number of the maze to solve.",
        required=True,
        type=int,
    )

    parser.add_argument(
        "-m",
        "--manually",
        help="play to the game manually.",
        action="store_true",
    )

    parser.add_argument(
        "-s",
        "--solver",
        choices=["a", "b", "c", "d"],
        help="solve the maze using the specified algorithm (a: A*, b: Beam Search, c: A* (LLM), d: Beam Search (LLM).",
    )

    parser.add_argument(
        "-r",
        "--animation",
        help="show an animation of how the maze is solved (requires the -s option).",
        action="store_true",
    )

    parser.add_argument(
        "-l",
        "--address",
        metavar="address",
        help="address of the llama-server endpoint.",
        type=str,
    )

    parser.add_argument(
        "-x",
        "--port",
        metavar="port",
        help="port of the llama-server endpoint.",
        default=10000,
        type=int,
    )

    parser.add_argument(
        "-p",
        "--prompt",
        metavar="prompt",
        help="file containinig the prompt for the model.",
        type=str,
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=["ascii", "structured", "both"],
        default="ascii",
        help="select the maze format for the prompt (ascii, structured or both, default: ascii)",
    )

    parser.add_argument(
        "-c",
        "--csv",
        action="store_true",
        help="ouput only the required data for analysis in CSV format (maze_id,algorithm,steps,states,format_string)",
    )

    parser.add_argument(
        "-a",
        "--alpha",
        metavar="alpha",
        help="confidence on the LLM's prediction (the higher the value the higher the confidence default 1.0",
        default=1.0,
        type=float,
    )

    # Get the variables from the argument parser
    args = parser.parse_args()
    input_file = args.input_file
    idx_maze = args.number
    manually = args.manually
    solve_game = args.solver
    show_animation = args.animation
    prompt_file = args.prompt
    address = args.address
    port = args.port
    prompt_format = args.format
    print_csv = args.csv
    alpha = args.alpha

    # Make sure there are not contradictory flags being used
    if print_csv and show_animation:
        print("Error: csv and show_animation options can't be used at the same time")
        exit(0)
    if manually and solve_game:
        print("Error: manually and solve_game options can't be used at the same time")
        exit(0)
    if show_animation and not solve_game:
        print(
            "Error: the show_animation option requires to specify the solve_game option"
        )
        exit(0)

    # Handle the prompt format and client connection if a llm solving approach was requested
    cvs_prompt_format = "null"
    if solve_game and solve_game in "cd":
        if not address or not prompt_file:
            print(
                "Error: user is requesting to use an LLM solving algorithm but the server address or the system prompt file are missing."
            )
            exit(0)
        cvs_prompt_format = prompt_format
        prompt = open(prompt_file).read()
        client = OpenAI(
            base_url=f"http://{address}:{port}/v1",  # Standard llama.cpp server address
            api_key="sk-no-key-required",  # Local llama-cpp server doesn't need a real key
        )

    # Load the Microban mazes into memory and make sure that the number of the requested
    # maze is between bounds.
    mazes = readMazes(input_file)
    if not print_csv:
        print(f"Number of mazes: {len(mazes)}")
    if not 1 <= idx_maze <= len(mazes):
        print(f"Error: Please select a number between 1 and {len(mazes)}")
        exit(0)

    # Load the requested maze and keep a copy to be able to reset the game state
    # when playing manually.
    maze = mazes[idx_maze - 1]
    original_maze = [row[:] for row in maze]

    # Solving the maze using a search algorithm was requested.
    # Take care of what information need to be printed and call the proper searching function
    if solve_game:
        solving_algorithm = ""
        if solve_game == "a":
            if not print_csv:
                print("Solving the maze using A*.")
            solving_algorithm = "A*"
            goal_maze, came_from, steps = aStar(maze)
        elif solve_game == "b":
            if not print_csv:
                print("Solving the maze using Beam Search.")
            solving_algorithm = "Beam Search"
            goal_maze, came_from, steps = beamSearch(maze)
        elif solve_game == "c":
            if not print_csv:
                print("Solving the maze using A* (LLM policy).")
            solving_algorithm = "A*(LLM-Policy)"
            goal_maze, came_from, steps = llmAStar(
                client, prompt, prompt_format, maze, alpha
            )
        elif solve_game == "d":
            if not print_csv:
                print("Solving the maze using Beam Search (LLM policy).")
            solving_algorithm = "Beam Search(LLM-Policy)"
            goal_maze, came_from, steps = llmBeamSearch(
                client, prompt, prompt_format, maze, alpha
            )

        # Do we need to show an animation of how the maze is solved?
        if show_animation:
            solution_path = reconstructSolutionPath(goal_maze, came_from, steps)
            animateSolutionPath(original_maze, solution_path)

        # Do we need to print the regular output or the csv version for later analysis.
        if not print_csv:
            print(f"Solved in {steps} steps, {len(came_from)} states explored")
        else:
            print(
                f"{idx_maze},{solving_algorithm},{steps},{len(came_from)},{cvs_prompt_format}"
            )

    # Play the game manually:
    # Use the arrows to produce a movement, q for quitting and r to going back
    # to the initial state.
    if manually:
        steps = 0
        while True:
            stdout.write("\033[2J\033[H")
            stdout.flush()
            printMaze(maze)
            print("Movement (↑,↓,←,→,r:reset,q:quit):", end=" ", flush=True)

            steps += 1
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
                steps = 0
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
                print(f"Solved the maze in {steps} steps.")
                break

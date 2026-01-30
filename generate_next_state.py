import argparse
import json

from engine import isValidSuccesor, readMazes, printMaze, parseMaze, renderMaze
from openai import OpenAI
from tqdm import tqdm

symbols = """### Symbols:
- `#`: Wall (Impassable)
- `@`: Player
- `+`: Player standing on a Target
- `$`: Box
- `*`: Box on a Target
- `.`: Target (Goal)
- ` `: Empty floor
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test how probable it is for a model to generate a succesful Sokoban movement using different input representations for the maze."
    )

    parser.add_argument(
        "-i",
        "--input_file",
        metavar="input_file",
        help="File containinig the description of the mazes in textual format.",
        required=True,
        type=str,
    )

    parser.add_argument(
        "-p",
        "--prompt",
        metavar="prompt",
        help="file containinig the prompt for the model.",
        required=True,
        type=str,
    )

    parser.add_argument(
        "-t",
        "--tries",
        metavar="tries",
        help="number of tries to generate a succesor.",
        required=True,
        type=int,
    )

    parser.add_argument(
        "-a",
        "--address",
        metavar="address",
        help="address of the llama-server endpoint.",
        required=True,
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
        "-n",
        "--number",
        metavar="number",
        help="number of the maze to use",
        default=1,
        type=int,
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=["ascii", "structured", "both"],
        default="ascii",
        help="select the maze format for the prompt (ascii, structured or both, default: ascii)",
    )

    parser.add_argument(
        "-d", "--debug", help="show the debug output", action="store_true"
    )

    # Parse the input options
    args = parser.parse_args()
    mazes_file = args.input_file
    number = args.number - 1
    prompt = args.prompt
    tries = args.tries
    address = args.address
    port = args.port
    prompt_format = args.format
    debug = args.debug

    mazes = readMazes(mazes_file)
    input_maze = mazes[number]

    format_input = ""
    output = "a string with the ASCII representation of the maze after applying the best movement."
    if prompt_format == "ascii":
        format_input = "formatted ASCII maze"
    elif prompt_format == "structured":
        format_input = "maze represented with tuples of pairs indicating the coordinates of each element of the game"
    elif prompt_format == "both":
        format_input = "formatted ASCII maze annotated with tuples of pairs indicating the coordinates for each element of the game"

    with open(prompt) as f:
        template = f.read()
    prompt = template.format(format=format_input, symbols=symbols, output=output)

    if debug:
        print("Prompt:")
        print(prompt)

    valid = 0
    client = OpenAI(base_url=f"http://{address}:{port}/v1", api_key="not-needed")

    if not debug:
        print("Input Maze:")
        printMaze(input_maze)

    user_input = f"Input Maze:\n```\n{renderMaze(input_maze)}\n```\n"
    if prompt_format in ["both", "structured"]:
        structured = """\nCoordinates:\n\"player\": {}\n\"walls\": {}\n\"boxes\": {}\n\"targets\": {}\n""".format(
            input_maze.player,
            input_maze.walls,
            input_maze.boxes,
            input_maze.targets,
        )
        user_input += structured

    if debug:
        print("User Input:")
        print(user_input)

    for _ in tqdm(range(tries)):
        response = client.chat.completions.create(
            model="mistral-7b-v0.3",
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": user_input,
                },
            ],
            response_format={"type": "json_object"},  # Enforces JSON
            temperature=0.5,
        )

        if response:
            try:
                data = json.loads(response.choices[0].message.content)
                text_maze = data["output"].split("\n")
                output_maze = parseMaze(text_maze)
                score = data["score"]
                if isValidSuccesor(input_maze, output_maze):
                    valid += 1
                    if debug:
                        print("Valid output:")
                        printMaze(output_maze)
                        print(f"Score: {score}")
                else:
                    if debug:
                        print("Invalid output:")
                        printMaze(output_maze)
                        print(f"Score: {score}")
            except KeyError:
                continue
            except json.JSONDecodeError:
                continue

    print(f"Valid outputs: ({valid}/{tries})")

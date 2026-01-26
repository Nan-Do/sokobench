import argparse
import json

from engine import isValidSuccesor, readMazes, printMaze, parseMaze
from openai import OpenAI
from tqdm import tqdm

DEBUG = False

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
        description="Test how probable it is for a model to generate a succesful Sokoban movement using an ascii art representation."
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
        help="Select the maze format for the prompt (ascii, structured or both, default: ascii)",
    )

    # Parse the input options
    args = parser.parse_args()
    mazes_file = args.input_file
    number = args.number - 1
    prompt = args.prompt
    tries = args.tries
    address = args.address
    port = args.port
    format_prompt = args.format

    mazes = readMazes(mazes_file)
    input_maze = mazes[number]

    format_input = ""
    output = "a string with the ASCII representation of the maze after applying the best movement."
    if format_prompt == "ascii":
        format_input = "formatted ASCII maze"
    elif format_prompt == "structured":
        format_input = "maze represented using tuples of pairs indicating the coordinates of each element of the game"
    elif format_prompt == "both":
        format_input = "formatted ASCII maze annotated with tuples of pairs with the coordinates for each element of the game"

    with open(prompt) as f:
        template = f.read()
    prompt = template.format(format=format_input, symbols=symbols, output=output)

    if DEBUG:
        print("Prompt:")
        print(prompt)

    valid = 0
    client = OpenAI(base_url=f"http://{address}:{port}/v1", api_key="not-needed")

    if not DEBUG:
        print("Input Maze:")
        printMaze(input_maze)

    user_input = f"Input Maze:\n```\n{'\n'.join(input_maze)}\n```\n"
    if format_prompt in ["both", "structured"]:
        walls, targets, boxes, player = parseMaze(input_maze)
        structured = """Coordinates:\n\"player\": {}\n\"walls\": {}\n\"boxes\": {}\n\"targets\": {}\n""".format(
            player,
            walls,
            boxes,
            targets,
        )
        user_input += structured

    if DEBUG:
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
                output_maze = data["output"]
                score = data["score"]
                if isValidSuccesor(input_maze, output_maze):
                    valid += 1
                    if DEBUG:
                        print("Valid output:")
                        print(output_maze)
                        print(f"Score: {score}")
                else:
                    if DEBUG:
                        print("Invalid output:")
                        print(output_maze)
                        print(f"Score: {score}")
            except KeyError:
                continue
            except json.JSONDecodeError:
                continue

    print(f"Valid outputs: ({valid}/{tries})")

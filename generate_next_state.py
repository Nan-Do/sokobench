import argparse
import json

from engine import isValidSuccesor, readMazes, printMaze
from openai import OpenAI
from tqdm import tqdm

DEBUG = True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test how probable it is for a model to generate a succesful Sokoban movement using an ascii art representation."
    )

    parser.add_argument(
        "-f",
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
        "-d",
        "--direction",
        metavar="direction",
        help="direction for the move",
        choices=["up", "down", "left", "right"],
        default="up",
    )

    # Parse the input options
    args = parser.parse_args()
    mazes_file = args.input_file
    number = args.number - 1
    prompt = args.prompt
    tries = args.tries
    address = args.address
    port = args.port
    direction = args.direction

    mazes = readMazes(mazes_file)
    input_maze = mazes[number]
    with open(prompt) as f:
        prompt = "\n".join(f.readlines())

    valid = 0
    client = OpenAI(base_url=f"http://{address}:{port}/v1", api_key="not-needed")

    print(f"Applying {direction} to maze:")
    printMaze(input_maze)

    for _ in tqdm(range(tries)):
        response = client.chat.completions.create(
            model="mistral-7b-v0.3",
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": f"Input Maze:\n```\n{input_maze}\n```\nDirection: {direction}",
                },
            ],
            response_format={"type": "json_object"},  # Enforces JSON
            temperature=0.5,
        )

        if response:
            data = json.loads(response.choices[0].message.content)
            output_maze = data["output"]
            if isValidSuccesor(input_maze, output_maze):
                valid += 1
                if DEBUG:
                    print("Valid output:")
                    printMaze(output_maze)

    print(f"Valid outputs: ({valid}/{tries})")

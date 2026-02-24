# 🧩 SokoBench: A Framework for LLM-Guided Spatial Planning

**SokoBench** is an open-source evaluation framework designed to test the 2D spatial awareness and planning capabilities of Large Language Models (LLMs). By using LLMs as heuristic guides for traditional search algorithms (A* and Beam Search), SokoBench measures a model's ability to map symbolic state representations to effective spatial actions within the constrained environment of Sokoban puzzles.

---

## 🔭 Overview

Traditional benchmarks often rely on tasks that LLMs may have encountered during training, while the Abstraction and Reasoning Corpus (ARC) can be too high-level for granular spatial analysis. SokoBench sits in the middle ground, providing a concrete, reproducible environment for testing:

* 🧭**Spatial Reasoning:** Can the model "visualize" a 2D grid from ASCII or coordinate-based text?
* 🎯**Heuristic Accuracy:** Do the model's log-probabilities for movement directions (Up, Down, Left, Right) align with optimal path-finding?
* 🧠**Planning vs. Execution:** How well does the model anticipate the consequences of pushing objects in a zero-tolerance environment where mistakes are often irreversible?

---

## ✨ Features

* **Dual Search Integration:** Use LLM probabilities to influence A* for optimality or Beam Search for high-complexity mazes.
* **Flexible Representations:** Support for ASCII grids, structured coordinate lists, or hybrid prompts.
* **Agnostic Backend:** Compatible with local llama-server (GGUF) or OpenAI-compatible APIs.
* **Benchmarking Tools:** Automated CSV export for large-scale analysis of steps taken, states explored, and model efficiency.

---

## 🚀 Installation

### 1. Requirements

Ensure you have Python 3.8+ installed. You will need to clone the repository and install the dependencies listed in the requirements file.

```bash
git clone https://github.com/Nan-Do/sokobench.git
cd SokoBench
pip install -r requirements.txt
```

### 2. LLM Backend

SokoBench is configured to point to a llama-server endpoint by default. You should have a server instance running on your local machine or a reachable network address before running the solver.

```bash
./llama-server -m your-model.gguf --port 8080
```

---

## Usage

Run experiments via the main entry point. The framework allows for manual play, traditional solving, or LLM-guided exploration.

```bash
python3 main.py -i Microban.txt -n 1 -s a -f both -p generate_next_movement.txt -l 192.168.0.1 -p 8080 
```

### Key Arguments

| Flag | Description |
| :--- | :--- |
| -i, --input_file | Path to the maze dataset (e.g., Microban.txt). |
| -n, --number | Specific maze number to solve from the dataset. |
| -s, --solver | a: **A\***, b: **Beam**, c: **LLM-Guided A\***, d: **LLM-Guided Beam**. |
| -f, --format | Prompt format: ascii, structured, or both. |
| -a, --alpha | **Confidence Weight**: Adjusts the influence of the LLM heuristic (f(n) = g(n) + α • h(n)). |
| -c, --csv | Headless mode for data collection (outputs maze_id, algorithm, steps, states, format). |
| -r, --animation | Visualize the solver's path in the terminal. |
| -l, --address | Address of the LLM end-point. |
| -x, --port | Port of the LLM end-point. |
| -p, --prompt | File containing the prompt. |
| -m, --manually | Solve the maze manually. |

---

## 📊 Methodology

The framework treats the LLM as a **heuristic function** $h(s)$. For a given state $s$:

1. The state is serialized into the chosen format (ASCII, coordinates, or both).
2. The LLM predicts the next token.
3. The probabilities for the four cardinal directions (Up, Down, Left, Right) are extracted and normalized to create a probability distribution.
4. The search algorithm uses these probabilities to prioritize node expansion.

The **Alpha** parameter allows researchers to tune the weight of the model's prediction. A higher value puts more trust in the LLM's spatial intuition, while a lower value relies more on the cost-to-reach ($g(n)$) of the traditional search.

---

## 📁 Project Structure

* **main.py**: Entry point for experiments and manual play.
* **engine.py**: Core Sokoban logic and state management.
* **solver.py**: Implementation of traditional A* and Beam Search.
* **llm_solver.py**: Search algorithms integrated with LLM log-probability guidance.
* **generate_next_state.py**: Script to evaluate if an LLM can predict the resulting maze state after a move.
* **Microban.txt**: Included dataset containing puzzles from the Microban collection.

---

## 🤝 Contributing

SokoBench is an open-source project aimed at improving how we measure "world models" and spatial planning in LLMs. Contributions regarding new state representations, different search algorithms, or benchmark results are welcome.

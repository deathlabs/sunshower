# `sunshower`
A Python library for evaluating AI agents declaratively.

## Installation
The instructions below explain how to install `sunshower`.

**Step 1.** Clone this repository and change directories to it.
```bash
git https://github.com/deathlabs/sunshower.git
cd sunshower
```

**Step 2.** Create a Python virtual environment.
```bash
python -m venv .venv
```

**Step 3.** Activate the Python virtual environment you just created. This step assumes you're working in a Linux-based environment. If you're using another operating system, adjust accordingly. 
```bash
source .venv/bin/activate
```

**Step 4.** Install the Python dependencies.
```bash
pip install -r requirements
```

## Usage
The instructions below provide an example of using `sunshower` (they assume you are using VS Code in a Linux-based environment and have already completed the [Installation](#installation) instructions above).

**Step 1.** Add `ipykernel`, `ipywidgets`, `langchain`, and `matplotlib` to your Python virtual environment.
```bash
pip install ipykernel ipywidgets langchain matplotlib
```

**Step 2.** Create a file called `.env` and added your Large Language Model (LLM) provider API keys to it. 

**Step 3.** Create a file called `experiments.yaml` using `example.yaml` for reference. 

**Step 4.** Open the provided Jupyter Notebook.

**Step 5.** Click "Select Kernel" and then click "Python Environments..." when prompted.

**Step 6.** Select your Python virtual environment.

**Step 7.** Click "Run All" and review the results at the bottom of the Jupyter Notebook.

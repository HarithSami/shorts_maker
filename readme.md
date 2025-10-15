# 🎬 YouTube Shorts Maker (`shorts_maker.py`)

This project automatically processes longer video files and extracts short, vertical clips optimized for **YouTube Shorts**, **TikTok**, and **Instagram Reels**.

---

## 🚀 Getting Started

These instructions will get your project up and running on your local machine.

### Prerequisites

You need **Python 3** installed on your system.

### Installation and Setup

Follow these steps to set up the necessary environment and dependencies:

1.  **Save the files:** Ensure you have the following files in your project directory:
    * `shorts_maker.py` (The main Python script)
    * `requirements.txt` (The list of required Python packages)
    * `run.bat` (The helper script to automate setup/execution)
    * Your source video files (e.g., `my_long_video.mp4`)

2.  **Run the Setup Script:**
    Execute the batch script to create a virtual environment, install dependencies, and run the program.

    ```bash
    run.bat
    ```

    * *Note: The `run.bat` script handles everything: creating a **virtual environment** (`venv`), installing packages from **`requirements.txt`**, and executing **`shorts_maker.py`**.*

---

## 💻 How to Use

The script is executed via the `run.bat` file.

Currently, the video processing logic (which video to cut, where to cut, output naming) is determined **within the `shorts_maker.py` script itself**.

1.  **Configure:** Open `shorts_maker.py` and modify the input/output settings, segment timings, or other parameters as required by your workflow.
2.  **Execute:** Double-click **`run.bat`** (or run it from the command line).

### Output

The resulting short, vertical video clips will be saved to the location specified within the `shorts_maker.py` script (e.g., an `output/` folder).

---

## 🛠 Project Structure

| File Name | Description |
| :--- | :--- |
| `shorts_maker.py` | The main logic for video cutting and formatting. |
| `requirements.txt` | Lists all necessary Python packages (like `moviepy`, `ffmpeg`, etc.). |
| `run.bat` | The Windows batch script for setup and execution. |
| `venv/` | The virtual environment folder (automatically created). |

---

## ✨ Why a Virtual Environment?

Using the `run.bat` script automatically sets up a **Virtual Environment (`venv`)** to:
* **Isolate Dependencies:** Keep project packages separate from your global Python installation.
* **Ensure Reproducibility:** Guarantee the script runs with the exact package versions defined in `requirements.txt`.
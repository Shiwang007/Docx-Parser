# Medjeex Exam Studio Setup Guide

Welcome to the **Medjeex Exam Studio**. This high-performance utility allows you to extract questions from Word documents with cinema-grade high-resolution math rendering.

## 🚀 One-Click Setup (Windows)

The simplest way to run the studio is using the included **`run.bat`** file.

1.  **Extract the folder** to your preferred location.
2.  **Double-click `run.bat`**.
3.  The script will automatically detect your environment, create a secure virtual workspace (`venv`), and install all necessary high-performance libraries.
4.  Once the terminal says "Uvicorn running", open your browser to: **[http://localhost:8001](http://localhost:8001)**

---

## 🛠 Prerequisites

If you are setting this up manually or helping a teammate:

*   **Python 3.10+**: Ensure Python is installed and added to your system **PATH**.
    *   [Download Python Here](https://www.python.org/downloads/)
*   **Modern Browser**: We recommend Chrome or Edge for the best mathematical rendering performance.

---

## 📂 Project Structure

*   **/web**: Contains the cinema-grade UI and KaTeX rendering logic.
*   **/src**: The core extraction engine (`parser_engine.py`).
*   **/scripts**: Advanced transformers for the Legacy Bridge.
*   **/output**: (Auto-generated) Where your PDF and JSON results are stored.

---

## 💡 Troubleshooting

### Math Rendering Failing
If you don't see math symbols correctly, ensure you run the app via `run.bat`. This script enforces **UTF-8 encoding**, which is critical for complex mathematical characters on Windows.

### Installation Errors
Ensure you have an active internet connection during the first-time setup as `run.bat` needs to download the `matplotlib` and `fastapi` libraries.

---
**Medjeex Advanced Agentic Coding - Production-Ready Deployment**

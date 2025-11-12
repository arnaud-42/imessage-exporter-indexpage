# imessage-exporter-indexpage

# 💬 Conversation Index Generator (Chat HTML File Indexing)

## Introduction

This Python script (`index-generator.py`) is an analysis and indexing tool designed to facilitate the searching and management of exported chat conversations in HTML format from imessage-exporter project.

It parses a folder filled with HTML conversation files (one file per contact/conversation), extracts key metadata (Contact Name, Last Message Date, Message Count), and generates a single interactive HTML index page (`index.html`).

The generated index allows for **sorting**, **filtering** by date, and performing lightning-fast **full-text searches** across thousands of messages, all without requiring an internet connection.

## ✨ Key Features

* **Fast Indexing:** Generates a comprehensive index from all HTML files within a specified folder.
* **Dynamic Sorting:** Sort the index directly in the browser by Contact Name, Last Contact Date, or Message Count.
* **Multi-Faceted Search:** Filter by contact name, date range, and message content.
* **"Fuzzy" Search:** Includes an approximate search mode (Fuzzy search) to find terms even with minor spelling errors or typos.
* **Message Preview:** Displays a snippet of the relevant message directly in the index during content searches.
* **Localization:** Supports French (`-l fr`) and English (`-l en`), with dynamic language switching within the interface.

## ⚙️ Prerequisites

This script is written in **Python 3**.

* **Python:** Ensure you have Python 3 installed on your system.
* **Source Files:** A folder containing only your exported conversation files in `.html` format.

## 🖥️ Usage

### 1. Download and Setup

1.  Place the **`index-generator.py`** script in your desired directory.
2.  Create a folder (e.g., `conversations/`) and place all your HTML conversation files inside it.

### 2. Running the Script

Open your terminal or command prompt, navigate to the directory where **`index-generator.py`** is located, and execute the following command, replacing `<YOUR_CONVERSATION_FOLDER>` with the path to your data folder:

```bash
# Example using the default language (French)
python3 index-generator.py <YOUR_CONVERSATION_FOLDER>

# Example forcing English interface
python3 index-generator.py <YOUR_CONVERSATION_FOLDER> -l en

# To specify a different output filename (e.g., my_index.html)
python3 index-generator.py <YOUR_CONVERSATION_FOLDER> -o my_index.html


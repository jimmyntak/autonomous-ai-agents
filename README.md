# Autonomous AI Agents: Real-Time Vision & Orchestration

> **An advanced, autonomous orchestration system for real-time computer vision, OCR analysis, and Discord integration.**

This repository contains the core vision processing, data orchestration, and communication modules of our autonomous AI agent. It is designed to parse visual data, perform advanced Optical Character Recognition (OCR), process complex state changes, and relay structured information across channels.

## Core Features

- **Real-Time Computer Vision & OCR**: Utilizes advanced text recognition and bounding box analysis (`text_recognition.py`) to extract structured data from unstructured visual inputs.
- **OpenAI Vision Fallback**: Features a robust, GPT-4V powered fallback mechanism (`openai_fallback.py`) that handles highly complex image-to-text extractions when standard OCR fails.
- **Configurable Data Processing**: Implements sophisticated data processing pipelines (`bet_data_processor.py`) capable of parsing state changes and triggering automated responses based on a configurable rule engine.
- **Discord Integration & Reporting**: Features integrated Discord capabilities (`discord_bot.py`, `txt-to-discord-master/*`) that orchestrate communication, broadcast real-time alerts, and deliver activity logs directly to specified channels.
- **Multi-Threaded Orchestration**: Efficiently coordinates multiple concurrent analysis and broadcasting tasks (`thread_manager.py`).

## Architecture & Tech Stack

- **Python**: Core data processing, computer vision analysis, and orchestration.
- **OpenAI API**: Advanced vision models (GPT-4o) for state processing.
- **Discord.py / Discord.js**: Real-time messaging and remote system monitoring.
- **Node.js**: Supplemental scripts for text-to-discord forwarding.

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js (v16+)
- A Discord Bot Token
- An OpenAI API Key (for vision/OCR features)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jimmyntak/autonomous-vision-and-orchestration.git
   cd autonomous-vision-and-orchestration
   ```

2. Install Python dependencies:
   ```bash
   pip install openai discord.py pyautogui opencv-python Pillow
   ```
   *(Note: Ensure you have your desired OCR engines installed if running `text_recognition.py` locally)*

3. Install Node.js dependencies (for specific Discord integrations):
   ```bash
   npm install dotenv discord.js
   ```

### Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Populate the `.env` file with your specific API keys, tokens, and credentials.
3. Review and copy `config/config.example.json` to `config/config.json` and adjust the general parameters as needed to fit your target environment.

## Security Note

This repository has been scrubbed of all hardcoded secrets. Please ensure `config.json` and `.env` remain in your `.gitignore` to prevent accidental credential leaks. Scripts containing private or site-specific automation logic have been explicitly excluded from this repository.

## License

MIT License

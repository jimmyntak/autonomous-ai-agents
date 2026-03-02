# Autonomous AI Agents: Real-Time Vision & Orchestration

> **An advanced, autonomous orchestration system integrating real-time computer vision, browser automation, and Discord communications.**

This project demonstrates a multi-agent orchestration architecture designed for real-time monitoring, data extraction, and automated decision execution across various web platforms. It leverages Playwright, Puppeteer, and computer vision (with OpenAI fallback) to interact with complex web interfaces securely and autonomously.

## Core Features

- **Autonomous Browser Orchestration**: Utilizes stealth-enabled Puppeteer and Playwright to navigate, monitor, and interact with complex web applications (e.g., live data feeds, dashboards) without human intervention.
- **Real-Time Computer Vision & OCR**: Integrates advanced computer vision techniques to analyze visual changes on screen. Includes an OpenAI Vision API fallback for robust Optical Character Recognition (OCR) when traditional parsing fails.
- **Discord Integration & Reporting**: Features multiple integrated Discord bots that orchestrate communication, broadcast real-time alerts, and deliver activity logs directly to specified channels.
- **Configurable Action Logic**: Implements sophisticated data processing pipelines (`bet_data_processor.py`) capable of parsing state changes and triggering automated responses based on a configurable rule engine.
- **Secure Secret Management**: Built with security best practices, utilizing `dotenv` and environment variables to ensure zero hardcoded credentials in the source code.

## Architecture & Tech Stack

- **Python**: Core data processing, computer vision analysis, and Playwright orchestration.
- **Node.js / JavaScript**: Discord bot orchestration and Puppeteer stealth operations.
- **OpenAI API**: Advanced OCR and visual state processing.
- **Playwright / Puppeteer**: Headless and headed browser automation.
- **Discord.js & discord.py**: Real-time messaging and remote system monitoring.

## Getting Started

### Prerequisites

- Node.js (v16+)
- Python (3.9+)
- Chrome / Chromium browser installed
- A Discord Bot Token
- An OpenAI API Key (for vision/OCR features)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jimmyntak/autonomous-vision-and-orchestration.git
   cd autonomous-vision-and-orchestration
   ```

2. Install Node.js dependencies:
   ```bash
   # In the root or specific program directories
   npm install dotenv discord.js puppeteer-extra puppeteer-extra-plugin-stealth
   ```

3. Install Python dependencies:
   ```bash
   pip install playwright openai discord.py
   playwright install
   ```

### Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Populate the `.env` file with your specific API keys, tokens, and credentials.
3. Review and copy `config/config.example.json` to `config/config.json` and adjust the general parameters as needed to fit your target environment.

## Security Note

This repository has been scrubbed of all hardcoded secrets. Please ensure `config.json` and `.env` remain in your `.gitignore` to prevent accidental credential leaks.

## License

MIT License

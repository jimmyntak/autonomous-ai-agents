#!/usr/bin/env python3
"""
Run the betting slip pipeline with a single photo.

Usage:

  # OpenAI only: send the full photo to GPT-4o, get JSON (no YOLO, no Google Vision)
  python3 run_with_photo.py /path/to/your/betting_screenshot.jpg

  # Optional: set category name (default "TestCategory")
  python3 run_with_photo.py /path/to/photo.jpg --category "ΚΟΡΩΝΑ"

  # Full pipeline: YOLO crops → Google Vision OCR → (optional) OpenAI fallback on crops
  # If YOLO/crops fail, falls back to OpenAI on the full photo.
  python3 run_with_photo.py /path/to/photo.jpg --full

Output: data.json and novidata.json in blade/ (and translated_data.json in forPerumal/).
"""

import os
import sys
import shutil
import argparse

_PROGRAM_DIR = os.path.dirname(os.path.abspath(__file__))
if _PROGRAM_DIR not in sys.path:
    sys.path.insert(0, _PROGRAM_DIR)

# Paths
BLADE_ROOT = os.path.dirname(_PROGRAM_DIR)
CROPS_DIR = os.path.join(BLADE_ROOT, "runs", "detect", "predict", "crops")
CREDENTIALS_PATH = os.path.join(BLADE_ROOT, "bets-414519-13edca7b7e58.json")
CONFIG_PATH = os.path.join(BLADE_ROOT, "config", "config.json")


def run_openai_only(photo_path: str, category: str) -> int:
    """Use only OpenAI Vision on the full photo. No YOLO, no Google Vision."""
    import openai_fallback
    result = openai_fallback.process_with_openai_fallback(photo_path, category)
    if result == "error":
        print("OpenAI fallback returned error.")
        return 1
    print("Done. Check blade/data.json and blade/novidata.json")
    return 0


def run_full_pipeline(photo_path: str, category: str) -> int:
    """YOLO on photo → crops → bet_data_processor (Google OCR + optional OpenAI on crops). On error, OpenAI on full photo."""
    if not os.path.isfile(CONFIG_PATH):
        print("Config not found:", CONFIG_PATH)
        return 1
    if os.path.isfile(CREDENTIALS_PATH):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
    else:
        print("Google credentials not found:", CREDENTIALS_PATH)

    from config_manager import ConfigManager
    from google.cloud import vision
    import bet_data_processor as bdp
    import openai_fallback
    from ultralytics import YOLO
    import torch

    config = ConfigManager(CONFIG_PATH)
    general = config.get_general_config()
    path_to_model = general.path_to_model
    if not os.path.isfile(path_to_model):
        print("YOLO model not found:", path_to_model)
        return 1

    # Clear previous runs
    runs_dir = os.path.join(BLADE_ROOT, "runs")
    if os.path.exists(runs_dir):
        shutil.rmtree(runs_dir)

    # YOLO predict → save crops
    model = YOLO(path_to_model)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model.to(device)
    model.predict(source=photo_path, save_crop=True)

    # Process crops
    client = vision.ImageAnnotatorClient()
    result = bdp.run(client, category)
    if result != "error":
        print("Done (crop pipeline). Check blade/data.json and blade/novidata.json")
        return 0

    # Fallback: full photo → OpenAI
    print("Crop pipeline failed. Trying OpenAI on full photo...")
    result = openai_fallback.process_with_openai_fallback(photo_path, category)
    if result == "error":
        print("OpenAI fallback also failed.")
        return 1
    print("Done (OpenAI fallback). Check blade/data.json and blade/novidata.json")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Run betting slip extraction on a photo.")
    parser.add_argument("photo", help="Path to betting slip image (jpg/png)")
    parser.add_argument("--category", default="TestCategory", help="Category name (default: TestCategory)")
    parser.add_argument("--full", action="store_true", help="Full pipeline: YOLO → crops → OCR (default: OpenAI only on photo)")
    args = parser.parse_args()

    photo_path = os.path.abspath(args.photo)
    if not os.path.isfile(photo_path):
        print("Photo not found:", photo_path)
        return 1

    if args.full:
        return run_full_pipeline(photo_path, args.category)
    return run_openai_only(photo_path, args.category)


if __name__ == "__main__":
    sys.exit(main())

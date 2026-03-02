#!/usr/bin/env python3
"""
Test script for the OpenAI OCR fallback in bet_data_processor.

Usage:

1) Test full pipeline (primary OCR + optional fallback)
   - Run YOLO first so crops exist under blade/runs/detect/predict/crops/
   - Then run this script. It will call bet_data_processor.run() and print the result.

   From blade/program:
     python test_ocr_fallback.py

   To force the OpenAI fallback path (skip Google Vision, use GPT-4o on crop images):
     FORCE_OCR_FALLBACK=1 python test_ocr_fallback.py

2) Test OpenAI fallback in isolation (no Google Vision)
   - Pass paths to directories that each contain at least one image (.jpg/.jpeg/.png).
   - Edit the PATHS dict below or pass as env TEST_CROP_DIR.

   Example with a single crop root (e.g. blade/runs/detect/predict/crops) that has
   subdirs bet1, bet2, teamA, teamB, bet_category1, bet_category2 (bet builder)
   or bet, bet_category, teamA, teamB (simple bet):

     TEST_CROP_DIR=/Users/jimmyntak/Downloads/blade/runs/detect/predict/crops python test_ocr_fallback.py --fallback-only
"""

import os
import sys
import json

# Add program dir so imports work
_PROGRAM_DIR = os.path.dirname(os.path.abspath(__file__))
if _PROGRAM_DIR not in sys.path:
    sys.path.insert(0, _PROGRAM_DIR)

# Default: use the same crops path as bet_data_processor
CROPS_ROOT = os.environ.get(
    "TEST_CROP_DIR",
    "/Users/jimmyntak/Downloads/blade/runs/detect/predict/crops",
)


def test_fallback_only():
    """Test openai_ocr_fallback() only: pass crop subdirs, print extracted text per field."""
    import bet_data_processor as bdp

    # Bet builder subdirs (adjust if you have simple bet: bet, bet_category, teamA, teamB)
    subdirs_bet_builder = [
        "bet1", "bet2", "bet_category1", "bet_category2", "teamA", "teamB"
    ]
    subdirs_simple = ["bet", "bet_category", "teamA", "teamB"]

    if os.path.isdir(os.path.join(CROPS_ROOT, "bet_builder")):
        field_dirs = {name: os.path.join(CROPS_ROOT, name) for name in subdirs_bet_builder}
    else:
        field_dirs = {name: os.path.join(CROPS_ROOT, name) for name in subdirs_simple}

    missing = [k for k, p in field_dirs.items() if not os.path.isdir(p)]
    if missing:
        print("Missing directories (no crop run yet?):", missing)
        print("CROPS_ROOT:", CROPS_ROOT)
        return 1

    print("Calling openai_ocr_fallback with:", list(field_dirs.keys()))
    result = bdp.openai_ocr_fallback(field_dirs)
    if result is None:
        print("openai_ocr_fallback returned None (OpenAI not available or error).")
        return 1
    print("Extracted text per field:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def test_full_run():
    """Run full bet_data_processor.run() with Vision client and category."""
    # Set Google Vision credentials (same path as bet_data_processor / thread_manager config)
    _credentials_path = "/Users/jimmyntak/Downloads/blade/bets-414519-13edca7b7e58.json"
    if os.path.isfile(_credentials_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _credentials_path
    else:
        print("Google credentials not found at:", _credentials_path)
        print("Set GOOGLE_APPLICATION_CREDENTIALS or run with --fallback-only to test OpenAI only.")
        return 1

    from google.cloud import vision
    import bet_data_processor as bdp

    if not os.path.isdir(CROPS_ROOT):
        print("Crops directory does not exist. Run YOLO first (e.g. via your app) to create:")
        print(" ", CROPS_ROOT)
        return 1

    # Use same client as thread_manager
    client = vision.ImageAnnotatorClient()
    category = os.environ.get("TEST_CATEGORY", "TestCategory")

    if os.environ.get("FORCE_OCR_FALLBACK") == "1":
        print("FORCE_OCR_FALLBACK=1: will use OpenAI OCR fallback path.")

    result = bdp.run(client, category)
    if result == "error":
        print("run() returned 'error'.")
        return 1
    print("run() completed successfully (no return value; check data.json / novidata.json).")
    return 0


def main():
    if "--fallback-only" in sys.argv:
        return test_fallback_only()
    return test_full_run()


if __name__ == "__main__":
    sys.exit(main())

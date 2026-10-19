#!/usr/bin/python

import sys
import json
import os
import argparse
from typing import NamedTuple

import cv2
import numpy as np

threshold = 0

class Frames(NamedTuple):
    frame: np.ndarray
    grey: np.ndarray
    diffrence: np.ndarray
    threshold: np.ndarray


def load_config(path):
    if not path or not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

    return {
        "input": data.get("input"),
        "output": data.get("output"),
        "verbose": bool(data.get("verbose", False)),
    }


def save_config(path, args):
    data = {
        "input": args.input,
        "output": args.output,
        "verbose": bool(args.verbose),
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return data


def extract_motion_fd(video_path, outfile):
    cap = cv2.VideoCapture(video_path)
    with open(outfile, "wb") as videofile:
        last = None
        current = None

        ret, frame = cap.read()
        if not ret:
            cap.release()
            return

        last = Frames(
            frame=frame,
            grey=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
            diffrence=None,
            threshold=None,
        )

        if videofile:
            videofile.write(last.frame)

    while ret:
        ret, current_frame = cap.read()
        if not ret:
            break

        current = Frames(
            frame=current_frame,
            grey=cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY),
            diffrence=None,
            threshold=None,
        )

        current = current._replace(
            diffrence=cv2.absdiff(last.grey, current.grey),
            threshold=cv2.threshold(
                cv2.absdiff(last.grey, current.grey), 30, 255, cv2.THRESH_BINARY
            )[1],
        )

        if videofile:
            videofile.write(current.frame)

        cv2.imshow("Grayscale", current.threshold)

        if cv2.waitKey(40) == 27:
            break

        last = current

    cv2.destroyAllWindows()
    cap.release()


def main(input_path, outfile):
    print(input_path, outfile)
    if input_path == 0:
        extract_motion_fd(0, outfile)
    else:
        extract_motion_fd(input_path, outfile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="MotionExtraction",
        description="Identifies motion occurring in the video",
    )
    parser.add_argument(
        "--config",
        help="Path to a JSON configuration file",
    )
    parser.add_argument(
        "--input",
        nargs="?",
        help="Camera id number or input file path to process",
    )
    parser.add_argument(
        "--output",
        nargs="?",
        help="File path in which to save video output",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )

    # Load config file first
    default_config = {}
    if "--config" in sys.argv:
        # a simple way to read the value before parse
        raw = sys.argv[sys.argv.index("--config") + 1] if "--config" in sys.argv and sys.argv.index("--config") + 1 < len(sys.argv) else None
        if raw:
            default_config = load_config(raw)
    else:
        default_config = load_config("config.json")

    parser.set_defaults(**default_config)
    args = parser.parse_args()

    # Save config after parsing, if the user supplied one
    if args.config:
        save_config(args.config, args)

    main(args.input, args.output)
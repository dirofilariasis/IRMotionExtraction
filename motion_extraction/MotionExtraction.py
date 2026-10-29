#!/usr/bin/python

import sys
import json
import os
import argparse
from typing import NamedTuple
from pathlib import Path
import ConfigDb 


import cv2
import numpy as np

threshold = 0

config = ConfigDb.get_instance()
config.create_value("verbose", False)


def verbose_callback(key, value):
    if key == "verbose":
        print(f"Verbose mode changed to: {value}")  

class Frames(NamedTuple):
    frame: np.ndarray
    grey: np.ndarray
    diffrence: np.ndarray
    threshold: np.ndarray

def extract_motion_fd(video_path, outfile):
    cap = cv2.VideoCapture(video_path)
    with open(outfile, "wb") as videofile:
        previous = None
        current = None

        ret, frame = cap.read()
        if not ret:
            cap.release()
            return

        current = Frames(
            frame=frame,
            grey=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),
            diffrence=None,
            threshold=None,
        )

        if videofile:
            videofile.write(current.frame)

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
                diffrence=cv2.absdiff(previous.grey, current.grey),
                threshold=cv2.threshold(
                    cv2.absdiff(previous.grey, current.grey), 30, 255, cv2.THRESH_BINARY
                )[1],
            )

            if videofile:
                videofile.write(current.frame)

            cv2.imshow("Grayscale", current.threshold)

            if cv2.waitKey(40) == 27:
             break

            previous = current

    cv2.destroyAllWindows()
    cap.release()


def main(input_path, outfile, options):
    print(input_path, outfile)
    if input_path == 0:
        extract_motion_fd(0, outfile)
    else:
        extract_motion_fd(input_path, outfile)


if __name__ == "__main__":
    current_dir = os.getcwd()
    print(current_dir)

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
   
    configPath = current_dir + "/motion_extraction/config.json"
    parser.set_defaults(**options)

    args = parser.parse_args()
    saveConfig = False

    config.register_callback("verbose", verbose_callback)

    # Set some defaults 
    config.create_value("input", 0) # camera or video file input
    config.create_value("verbose", False) # extra debugging output
    # where to save video output
    video_output_path = current_dir + "/motion_extraction/output.avi"
    config.create_value("output", video_output_path)
    config.create_value("configPath", None)
    config.create_value("saveConfig", False)

    if args.config != None:
        configPath = args.config
        config.load_from_json(configPath)
        config.create_value("configPath", configPath)
        config.create_value("saveConfig", True)
    else:
        # collect arguments and update the config file
        if args.input != None and args.input != options["input"]:
            config.update_value("input", args.input)
            config.update_value("saveConfig", True)
        if args.output != None and args.output != options["output"]:
            options["output"] = args.output
            config.update_value("output", args.output)
            config.update_value("saveConfig", True)
        if args.verbose != options["verbose"]:
            options["verbose"] = args.verbose
            config.update_value("verbose", args.output)
            config.update_value("saveConfig", True)
        # Save config after parsing, if the user supplied one
   
    if saveConfig:
        config.save_to_json(configPath)

    main(options["input"], options["output"], options)



#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "u/beeznutsonly"

"""
Quick python script to batch-watermark .mp4 files in a
directory using the vlc's transcoding feature
(as seen on https://www.reddit.com/r/romanticxxx).
"""

import configparser
import os
import shlex
import signal
import subprocess
import sys


# Class definitions
# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------


# Class which defines the general properties of a watermark
class Overlay:

    x:        int
    y:        int
    position: int
    opacity : int

    def __init__(
        self,
        x, y,
        position,
        opacity
    ):

        self.x = x
        self.y = y
        self.position = position
        self.opacity  = opacity


# Class which defines the properties of a Marquee watermark
class MarqueeOverlay(Overlay):

    marquee  : str
    size     : int
    color    : str

    def __init__(
        self,
        marquee,
        size,
        color
    ):
        self.marquee  = marquee
        self.size     = size
        self.color    = color


    def __init__(
        self,
        marquee,
        size,
        color,
        x, y,
        position,
        opacity
    ):

        super(MarqueeOverlay, self).__init__(
            x, y, position, opacity
        )
        self.marquee  = marquee
        self.size     = size
        self.color    = color


# Class which defines the properties of a Logo watermark
class LogoOverlay(Overlay):

    logoFileName : str

    def __init__(
        self,
        logoFileName,
        x, y,
        position,
        opacity
    ):

        super(LogoOverlay, self).__init__(
            x, y, position, opacity
        )
        self.logoFileName = logoFileName


    def __init__(
        self,
        logoFileName
    ):
        self.logoFileName = logoFileName


# Application global variables
# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------


# Root directory
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Directory containing vids to be watermarked
TO_BE_WATERMARKED_DESTINATION = os.path.join(BASE_PATH, 'tobewatermarked')

# Destination directory for watermarked vids
WATERMARKED_DESTINATION = os.path.join(BASE_PATH,'watermarked')

# Directory contain all logo overlays
LOGOS_DIRECTORY = os.path.join(BASE_PATH,'logos')

# Overlay configuration file
OVERLAYS_CONFIG = os.path.join(BASE_PATH, 'overlays.ini')


# Application commands
# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------


# Start single-watermarking job
def startWatermarking(overlay, originalVideoFileName):
    
    print('\nProcessing: "{}"\n'.format(originalVideoFileName))
        
    originalVideoPath = os.path.join(
        TO_BE_WATERMARKED_DESTINATION, 
        originalVideoFileName
    )
    
    # sfilter module determination based on overlay type
    if isinstance(overlay, MarqueeOverlay):
        sfilter = (
            "marq{{"
                "marquee={marquee},"
                "x={x},"
                "y={y},"
                "position={position},"
                "opacity={opacity},"
                "size={size},"
                "color={color},"
                "scale=Auto"
            "}}".format(
                marquee=overlay.marquee,
                x=overlay.x,
                y=overlay.y,
                position=overlay.position,
                opacity=overlay.opacity,
                size=overlay.size,
                color=overlay.color
            )
        )
    elif isinstance(overlay, LogoOverlay):
        sfilter = (
            "logo{{"
                "file='{logoFilePath}',"
                "x={x},"
                "y={y},"
                "position={position},"
                "opacity={opacity}"
            "}}".format(
                logoFilePath=os.path.join(
                    LOGOS_DIRECTORY,
                    overlay.logoFileName
                ),
                x=overlay.x,
                y=overlay.y,
                position=overlay.position,
                opacity=overlay.opacity
            )
        )
    else:
        print(
            "Invalid overlay type '{}' provided"
            .format(type(overlay))
        )
        return

    # The transcoding instruction
    transcodingInstruction = (
        "#transcode{{vcodec=h264,soverlay,sfilter="
        "{sfilter}}}"
        ":std{{access=file,dst=\"{destDirectory}/"
        "{name}\"}}".format(
            sfilter=sfilter,
            destDirectory=WATERMARKED_DESTINATION,
            name=originalVideoFileName
        )
    )

    # The vlc terminal command to initiate the watermarker
    watermarkerTerminalCommandString = (
        "cvlc --sout-mux-caching=5000 --no-repeat --no-loop "
        "\"{}\" --sout='{}' vlc://quit"
        .format(
            originalVideoPath,
            transcodingInstruction
        )
    )
    partitionedCommand = shlex.split(
        watermarkerTerminalCommandString
    )

    # New process to execute the transcoding instruction
    process = subprocess.Popen(
        partitionedCommand,
        stdout=subprocess.PIPE
    )

    # Process display configuration
    output, error = process.communicate()
    print(output)


# Start batch-watermarking job
def startBatchWatermarking(overlay):
    
    # List containing names of all the video
    # files in the 'to be watermarked' dir.
    originalVideoFileNames = [
        file for file in os.listdir(
                TO_BE_WATERMARKED_DESTINATION
            ) if file.endswith('.mp4')
    ]

    print('Starting batch-watermarking\n')

    # Loop to traverse through all the videos for transcoding
    for originalVideoFileName in originalVideoFileNames:
        startWatermarking(overlay, originalVideoFileName)

    # Completo
    print('\nBatch-watermarking completed')


# Validity checks
# -------------------------------------------------------------------------------

# Check and inform validity of overlay
def informIfOverlayInvalid(overlay):
    if not (overlay in ["logo", "l", "marquee", "m"]):
        print(
            'The overlay "{}" is invalid. '
            'Please check it and try again'
            .format(overlay)
        )
        return True
    return False

# Check and inform validity of task
def informIfTaskInvalid(task):
    if not (task in ["batch", "b", "single", "s", "multiple", "m"]):
        print(
            'The task "{}" is invalid. '
            'Please check it and try again'
            .format(task)
        )
        return True
    return False

# Check and inform validity of fileName
def informIfFileNameInvalid(fileName):
    if not fileName.endswith('.mp4'):
        print(
            'The file name "{}" is invalid. '
            'Please check it and try again'
            .format(fileName)
        )
        return True
    return False

# Check and inform validity of fileName
def informIfFileNamesInvalid(fileNames):
    for fileName in fileNames.split(','):
        if not fileName.endswith('.mp4'):
            print(
                'The file name "{}" is invalid. '
                'Please check it and try again'
                .format(fileName)
            )
            return True
        return False


# Command building
# -------------------------------------------------------------------------------

# Build up program command from user input
def startCommandWizard():
    command = []
    try:
        # Overlay prompt loop
        while True:
            overlay = input(
                'What type of watermark do you want?'
                ' (logo [default]/marquee): '
            )
            if (overlay == '' or overlay == '\n'):
                overlay = 'logo'
            elif informIfOverlayInvalid(overlay):
                continue

            command.append(overlay)

            # Task type prompt loop
            while True:
                task = input(
                    'What type of task do you want '
                    'performed? (batch/multiple/single [default]): '
                )
                if (task == '' or task == '\n'):
                    task = 'single'
                elif informIfTaskInvalid(task):
                    continue
                command.append(task)

                if (task == 'single' or task == 's'):
                    # File name prompt loop for 'single' task
                    while True:

                        fileName = input(
                            'Enter the name of the file '
                            'you want watermarked '
                            '(including the extension): '
                        )
                        if informIfFileNameInvalid(fileName):
                            continue
                        command.append(fileName)
                        break
                    break
                elif (task == 'multiple' or task == 'm'):
                    # Prompt for multiple files for 'multiple' task
                    fileNames = input(
                            'Enter a comma-separated list of the '
                            'names of the files '
                            '(including the extensions) '
                            'you want watermarked: '
                    )
                    validFileNames = []
                    for fileName in fileNames.split(','):
                        if not informIfFileNameInvalid(fileName):
                            validFileNames.append(fileName)
                    command.append(",".join(validFileNames))
                    break
                break
            break
                
    # Handle if forced shutdown requested 
    except (KeyboardInterrupt, EOFError):
        print('Application aborted, now quitting')
        sys.exit(1)
    
    return command

# Command executor
def executeCommand(command):

    # Checking validity of command by length
    if len(command) <= 1:
        print('Cannot process incomplete command')
        return
    
    # Overlay determination
    overlay = command[0]
    if informIfOverlayInvalid(overlay):
        return

    configReader = configparser.ConfigParser()

    with open(OVERLAYS_CONFIG) as file:
        configReader.read_file(file)

    if (overlay == 'marquee' or overlay == 'm'):
        section = "Marquee"
        marquee = configReader.get(
            section, "marquee"
        )
        size = configReader.getint(
            section, "size"
        )
        color = configReader.get(
            section, "color"
        )
        overlayObj = MarqueeOverlay(
            marquee=marquee,
            size=size,
            color=color
        )

    elif (overlay == 'logo' or overlay == 'l'):
        
        section = "Logo"
        logoFileName = configReader.get(
            section, "logoFileName"
        )
        overlayObj = LogoOverlay(
            logoFileName
        )

    overlayObj.x = configReader.getint(
        section, "x"
    )
    overlayObj.y = configReader.getint(
        section, "y"
    )
    overlayObj.position = configReader.getint(
        section, "position"
    )
    overlayObj.opacity = configReader.getint(
        section, "opacity"
    )

    # Task type validity checks and execution
    task = command[1]
    if informIfTaskInvalid(task):
        return

    if len(command) == 2:
        if (task != 'batch' or task != 'b'):
            print('Incorrect arguments for task')
            return
        else:
            startBatchWatermarking(overlayObj)
            return

    if (task == 'single' or task == 's'):
        if informIfFileNameInvalid(command[2]):
            return
        startWatermarking(overlayObj, command[2])

    elif (task == 'multiple' or task == 'm'):
        if informIfFileNamesInvalid(command[2]):
            return
        for fileName in command[2].split(','):
            startWatermarking(overlayObj, fileName)
        
# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------


# Let the games begin boysss
# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------
if __name__ == "__main__":

    if len(sys.argv) == 1:
        # If no additional CL arguments provided
        executeCommand(startCommandWizard())
    else:
        executeCommand(sys.argv[1:])

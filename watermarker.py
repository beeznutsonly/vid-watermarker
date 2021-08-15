#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "u/beeznutsonly"

"""
Quick python script to batch-watermark .mp4 files in a
directory using the vlc CLI
(as seen on https://www.reddit.com/r/romanticxxx).
"""

import configparser
import os
import shlex
import signal
import subprocess
import sys
import pickle


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
        x=20,
        y=20,
        position=10,
        opacity=255,
    ):

        self.x = x
        self.y = y
        self.position = position
        self.opacity  = opacity


# Class which defines the properties of a marquee watermark
class MarqueeOverlay(Overlay):

    marquee     : str
    size     : int
    color    : str

    def __init__(
        self,
        marquee,
        size=30,
        color='0xFFFFFF',
        x=20, y=20,
        position=10,
        opacity=255
    ):

        self.marquee  = marquee
        self.size     = size
        self.color    = color
        super(MarqueeOverlay, self).__init__(
            x, y, position, opacity
        )


# Class which defines the properties of Logo watermark
class LogoOverlay(Overlay):

    logoFileName : str

    def __init__(
        self,
        logoFileName,
        x=20, y=20,
        position=10,
        opacity=255
    ):

        self.logoFileName = logoFileName
        super(LogoOverlay, self).__init__(
            x, y, position, opacity
        )


# Application global variables
# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------


# Root directory
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Directory containing vids to be watermarked
TO_BE_WATERMARKED_DESTINATION = os.path.join(BASE_PATH, 'tobewatermarked')

# Destination directory for watermarked vids
WATERMARKED_DESTINATION = os.path.join(BASE_PATH,'watermarked')

# Overlay configuration file details
OVERLAYS_CONFIG = os.path.join(BASE_PATH, 'overlays.ini')


# Application commands
# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------


# Start single-watermarking job
def startWatermarking(overlay, originalVideoFileName):
    
    print('Processing: "{}"'.format(originalVideoFileName))
        
    originalVideoPath = os.path.join(
        TO_BE_WATERMARKED_DESTINATION, 
        originalVideoFileName
    )
    
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
                "scale=0"
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
                "scale=0"
            "}}".format(
                logoFilePath=os.path.join(
                    BASE_PATH,
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
        "cvlc --no-repeat --no-loop "
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
    if not (overlay in ["logo", "marquee"]):
        print(
            'The overlay "{}" is invalid. '
            'Please check it and try again'
            .format(overlay)
        )
        return True
    return False

# Check and inform validity of task
def informIfTaskInvalid(task):
    if not (task in ["batch", "single", "multiple"]):
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


# Input methods
# -------------------------------------------------------------------------------

# Build up program command from user input
def startCommandWizard():
    command = []
    try:
        while True:
            overlay = input(
                'What type of watermark do you want?'
                ' (logo/marquee): '
            )
            if informIfOverlayInvalid(overlay):
                continue

            command.append(overlay)
            while True:
                task = input(
                    'What type of task do you want '
                    'performed? (batch/single/multiple): '
                )
                if informIfTaskInvalid(task):
                    continue
                command.append(task)

                if task == 'single':
                    
                    # File name prompt loop for single task
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
                elif task == 'multiple':
                    fileNames = input(
                            'Enter a comma-separated list of the'
                            'names of the files '
                            '(including the extensions)'
                            'you want watermarked: '
                    )
                    for fileName in fileNames.split(','):
                        validFileNames = ''
                        if informIfFileNameInvalid(fileName):
                            validFileNames += fileName + ','
                    command.append(validFileNames)
                    break
                break
            break
                
    # Handle if forced shutdown requested 
    except KeyboardInterrupt or EOFError:
        print('Application aborted, now quitting')
        sys.exit(1)
    
    return command

# Execute 
def executeCommand(command):

    if len(command) <= 1:
        print('Cannot process incomplete command')
        return
    
    overlay = command[0]
    if informIfOverlayInvalid(overlay):
        return

    configReader = configparser.ConfigParser()

    with open(OVERLAYS_CONFIG) as file:
        configReader.read_file(file)

    if overlay == 'marquee':
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

    elif overlay == 'logo':
        
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


    task = command[1]
    if len(command) == 2:
        if task != 'batch':
            print('Incorrect arguments for task')
            return
        else:
            startBatchWatermarking(overlayObj)
            return

    if informIfTaskInvalid(task):
        return

    if task == 'single':
        if informIfFileNameInvalid(command[2]):
            return False
        startWatermarking(overlayObj, command[2])

    elif task == 'multiple':
        if informIfFileNamesInvalid(command[2]):
            return False
        for fileName in command[2].split(','):
            startWatermarking(overlayObj, fileName)
        
    

# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------


# Let the games begin boysss
# -------------------------------------------------------------------------------
# -------------------------------------------------------------------------------
if __name__ == "__main__":

    if len(sys.argv) == 1:
        executeCommand(startCommandWizard())
    else:
        executeCommand(sys.argv[1:])
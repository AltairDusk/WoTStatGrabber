import sys
from cx_Freeze import setup, Executable

setup(name = 'World of Tanks Statistics Grabber',
      description = 'A tool to grab user statistics for World of Tanks and output them to CSV.',
      executables = [Executable('WotStatGrabber.py')]
      )
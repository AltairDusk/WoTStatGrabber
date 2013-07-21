WotStatGrabber is a simple script for retrieving user statistics from the official World of Tanks API with output in an easy to use .csv format.  

You must provide 2 arguments when calling WotStatGrabber: the input file and the output file.  You can optionally provide the number of top played low tier tanks to return in the low tier battles calculation with the --top_lt flag.

Usage:
python WotStatGrabber.py inputFilePath outputFilePath --top_lt #

inputFilePath: Full pathname of the input file which contains the names of users stats will be retrieved for.  Each username should be on a separate line.
outputFilePath: Full pathname of the output file which will be generated with the statistics in CSV format.
--top_lt: (Optional) Number of top played low tier tanks to include in the low tier battles calculation, if not provided the top 3 most played low tier tanks will be used.

Example:
python WotStatGrabber.py C:\temp\names.txt C:\temp\stats.csv --top_lt 5



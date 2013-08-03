WotStatGrabber is a simple script for retrieving user statistics from the official World of Tanks API with output in an easy to use .csv format.  

You must provide 2 arguments when calling WotStatGrabber: the input file and the output file.  You can optionally provide a flag to indicate WNx development mode and the number of top played low tier tanks to return in the low tier battles calculation.

Usage:
python WotStatGrabber.py inputFilePath outputFilePath --wn --top_lt1 # --top_lt2 #

inputFilePath: Full pathname of the input file which contains the names of users stats will be retrieved for.  Each username should be on a separate line.
outputFilePath: Full pathname of the output file which will be generated with the statistics in CSV format.
--wn: (Optional) WNx development mode. This will output additional information useful in development of the WNx statistic.
--top_lt1: (Optional) Number of top played low tier tanks used to calculate games played in low tiers for the first output field. This only functions when used with the --wn flag. If not provided 3 is used.
--top_lt2: (Optional) Number of top played low tier tanks used to calculate games played in low tiers for the second output field. This only functions when used with the --wn flag. If not provided 5 is used.

Examples:
Basic output:
python WotStatGrabber.py C:\temp\names.txt C:\temp\stats.csv
WNx development mode:
python WotStatGrabber.py C:\temp\names.txt C:\temp\stats.csv --wn
WNx development mode with custom top(x) low tiers:
python WotStatGrabber.py C:\temp\names.txt C:\temp\stats.csv --wn --top_lt1 2 --top_lt_2 8



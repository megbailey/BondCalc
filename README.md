# CMD Bond

CMD Bond is a command line tool that is able to do a mass lookup of USA Treasury Bond redemption values given their Denom, Series, and Issue Date. This information is parsed from a CSV on your filesystem to form a targeted query for the current redemption value from the [USA Treasury API](https://fiscaldata.treasury.gov/api-documentation). The primary use case for this is for paper bonds which USA no longer issues (circa 2011)*. 

*Series EE bonds reach full-maturity at 20 years and stop occuring interest at 30 years. Paper bonds may exist until 2041.

More in depth information on the contents of the USA Treasury API to extend cmd-bond for further functionality use option -f or refer to the official documentation.

[Redemption Tables Fields](https://fiscaldata.treasury.gov/datasets/redemption-tables/redemption-tables)

[Fiscaldata.treasury.gov Filtering](https://fiscaldata.treasury.gov/api-documentation/#filters)

## Steps to Run
```
python3 cmd-bond.py [-h,m,s,v,f] -i inputfile

options:
-h,--help Prints usage
-p,--print Prints the results to stdout
-m,--modify Modify the given input file
-s,--sum Calculate sum. This will always print to stdout
-v,--verbose Prints stats and other information during processing. Useful for debugging
-f,--fields Availble fields for search from (url)
```

## Building from source
```
pip install pyinstaller
pyinstaller cmd-bond.py
```
In /disto/cmd-bond/, you'll find the newly bundled app
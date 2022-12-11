# CMD Bond

CMD Bond is a script that is capable of doing a mass lookup of USA Treasury Bond redemption values given a CSV containing their Denom, Series, and Issue Date. The CSV is parsed to form a targeted query for the current redemption value from the [USA Treasury API](https://fiscaldata.treasury.gov/api-documentation). CMD Bond is capable of modifying the CSV with the found data or simply printing the new information to stdout.

CMD Bond's primairy use case is for paper bonds which USA stopped issuing circa 2011. Series EE bonds reach full-maturity at 20 years and stop occuring interest at 30 years. Therefore, paper bonds may exist until 2041.

More in depth information on the contents of the USA Treasury API to extend cmd-bond for further functionality use option -f or refer to the official documentation.

[Redemption Tables Fields](https://fiscaldata.treasury.gov/datasets/redemption-tables/redemption-tables)
[Fiscaldata.treasury.gov Filtering](https://fiscaldata.treasury.gov/api-documentation/#filters)

## The CSV file
At minimum, the CSV file must contain the columns "Denom", "Series", and "Issue Date" and the associated bond data.
If the modify flag is set, the script will append (or populate if existing) the columns and data for "Interest Rate", "Interest Earned", "Current Value".

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
In /dist/cmd-bond/, you'll find the newly bundled app by the same name.

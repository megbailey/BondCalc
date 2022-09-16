# CMD Bond
CMD Bond is a command line tool that is able to do a mass lookup of USA Treasury Bond redemption values given their Denom, Series, and Issue Date. This information is parsed from a CSV on your filesystem to form a targeted query for the current redemption value from the USA Tresaury API. The primary use case for this is for paper bonds which USA no longer issues (circa 2011). Series EE bonds reach full-maturity at 20 years and stop occuring interest at 30 years. Paper bonds may exist till then.

Usage: cmdbond -h

More in depth information on the contents of the USA Treasury API and descriptions on query fields.
use option -f, or the following documentation official
Fields: https://fiscaldata.treasury.gov/datasets/redemption-tables/redemption-tables\
Filters: https://fiscaldata.treasury.gov/api-documentation/#filters"

## Steps to Run
1. cmdbond -i <inputfile>


## Building from source
pip install pyinstaller
pyinstaller bond.py
in /disto, you'll find the newly bundled app


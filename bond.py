import sys, getopt
import datetime
from datetime import date
import csv
import re
import requests
import os

BASE_URL ='https://api.fiscaldata.treasury.gov/services/api/fiscal_service'
BOND_ENDPOINT ='/v2/accounting/od/redemption_tables'
# Some hard-coded validation
valid_denom = ["10", "25", "50", "75", "100", "200", "500", "1000", "5000", "10000"]
valid_series = ["I", "E", "EE", "H", "HH"]
valid_series_regex = "(Series )?(I|E{2}|E|H{2}|H)"

def usage():
    print('Usage:\n\tbond.py [-h,f] -i <inputfile>\n\
            Options:\n\
            -h,--help\t Prints usage\n\
            -m,--modify\t Modify the given input file\n\
            -s,--sum\t Calculate Sum. This will always print to stdout. If -m, It will also write to the file\n\
            -v,--verbose\t Prints Stats and other information during processing\n\
            -f,--fields\t Availble fields for search from (url) ' + BASE_URL)

def info():
    print( "\n\
            --------------------------------------------------------------------------------------\n\
            CMD Bond is able to do a mass lookup of USA Treasury Bond redemption values given their Denom, Series, and Issue Date.\n\
            This information is parsed from a CSV on your filesystem to form a targeted query for the current redemption value from the USA Tresaury API.\n\
            The primary use case for this is for paper bonds which USA no longer issues (circa 2011). \n\
            More Options: bond.py -h \n\
            --------------------------------------------------------------------------------------\n\
            For more information on the contents of the USA Treasury API and descriptions on query field,\n\
            use option -f, or the following documentation official ->\n\
            Fields: https://fiscaldata.treasury.gov/datasets/redemption-tables/redemption-tables\n\
            Filters: https://fiscaldata.treasury.gov/api-documentation/#filters\n" )

# Main loop to parse command line inputs
def main(argv):

    input_file = ''
    input_flag = False
    modify_flag = False
    sum_flag = False
    print_flag = False

    try:
        opts, args = getopt.getopt(argv, "hpsmfi:",["input="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-p", "--print"):
            print_flag = True
        elif opt in ("-s", "--sum"):
            sum_flag = True
        elif opt in ("-m", "--modify"):
            modify_flag = True
        elif opt in ("-f", "--fields"):
            get_api_fields()
            sys.exit()
        elif opt in ("-i", "--input"):
            input_file = arg
            input_flag = True

    if not input_flag:
        print("Input file is required.")
        usage()
        sys.exit(2)

    # Look through the CSV file so that we can ask the API for a more targeted amount of info
    (denoms, series, years) = preprocess_csv( input_file, print_flag )

    # Returns a dictionary of relevant bond info. Key is a tuple of ( issue_date(s), issue_name/series )
    usa_bonds = fetch_bond_data ( 
        denoms, 
        series, 
        years,
        print_flag
    )

    # Compare the two sets to get the results
    lookup_user_bonds ( 
        input_file,
        usa_bonds,
        modify_flag,
        sum_flag,
        print_flag
    )  


def lookup_user_bonds( inputfile, usa_bonds, modify_flag, sum_flag, print_flag ):

    # Init dictionaries to keep track of csv columns index for ease of lookup
    required_csv_headers = { "Denom": -1, "Series": -1, "Issue Date": -1 }
    to_add_headers = { "Interest Rate": -1, "Interest": -1, "Current Value": -1 }

    csvfile = open( inputfile, 'r', encoding="utf-8" )

    # Store the index of the headers
    csv_headers = csvfile.readline().split(',')
    for index, header in enumerate(csv_headers):
        header = header.strip('\n')
        csv_headers[index] = header
        if header in required_csv_headers.keys():
            required_csv_headers[header] = index
        if header in to_add_headers.keys():
            to_add_headers[header] = index

    print("Found headers: " + str(csv_headers) )

    # Modify CSV headers or deteremine if the CSV already has allocated the additional columns
    modified_file = []
    modified_headers = csv_headers
    if modify_flag:
        for header in to_add_headers.items():
            if header[1] == -1: # header is a tuple
                next_index = len(modified_headers)
                modified_headers[next_index] = header[0]

    count = 0
    redemp_sum = 0
    interest_sum = 0

    # continue after header line
    for row in csvfile.readlines():
        row = row.split(',')

        denom_value = str(re.sub('[\$,]', '', row[ required_csv_headers["Denom"] ]))
        series_value = re.findall( valid_series_regex, row[required_csv_headers["Series"]] )[0][1]
        issue_date_value = row[required_csv_headers["Issue Date"]]

        series_value = 'Series ' + series_value
        mock_tuple = (issue_date_value, series_value )
        int_earned_key = 'int_earned_' + denom_value + '_amt'
        redemp_value_key = 'redemp_value_' + denom_value + '_amt'

        if (usa_bonds[mock_tuple]):
            count = count + 1
            int_earned_value = usa_bonds[mock_tuple][int_earned_key]
            redemp_value_value = usa_bonds[mock_tuple][redemp_value_key]
            print(  "| (" + str(count) + ") " + 
                    "Issue Date: " +  issue_date_value + ", " +
                    "Denom: " + denom_value + ", " +
                    "Series: " + series_value + ", " +
                    "Interest Earned: " + int_earned_value + ", " +
                    "Redemption Value: " + redemp_value_value + ", "
                )
            redemp_sum = redemp_sum + float(redemp_value_value)
            interest_sum = interest_sum + float(int_earned_value)

    redemp_sum = str( round(redemp_sum, 2) )
    interest_sum = str( round(interest_sum, 2) )
    print(" -------------------------------------------------------\nTotal Redemption Value: " + redemp_sum + ", Total Interest Earned: " + interest_sum )

def preprocess_csv(inputfile, print_flag):

    # Init a dictionary so we can keep track of the required csv columns index for ease of lookup
    required_csv_headers = { "Denom": -1, "Series": -1, "Issue Date": -1 }
    
    csvfile = open( inputfile, 'r', encoding="utf-8" )

    # Store the index of the headers
    csv_headers = csvfile.readline().split(',')
    for index, header in enumerate(csv_headers):
        if header in required_csv_headers.keys():
            required_csv_headers[header] = index

    # If the minimumm required headers arent found, throw an exception
    for required_header in required_csv_headers.items():
        if required_csv_headers[required_header[0]] == -1:
            raise Exception( "At minimum, the CSV file must contain columns" + str(required_csv_headers) + "\n Could not find: " + required_header )

    # Keep track of unique found values so that we can form a targeted query to the API
    found_series = []
    found_denom = []
    found_years = []
    for row in csvfile.readlines():
        row = row.split(',')

        # Check if its a valid denom
        denom_value = str(re.sub('[\$,]', '', row[ required_csv_headers["Denom"] ]))
        if denom_value not in valid_denom:
            raise Exception( "Valid Denom values are: " + str(valid_denom) + "\n Provided: " + denom_value )
        if denom_value not in found_denom:
            found_denom.append(denom_value)

        #  Check if its a valid issue date
        issue_date_value = row[required_csv_headers["Issue Date"]].split('-')
        if len(issue_date_value) != 2:
            raise Exception( "Valid Issue Date format is yyyy-mm" + "\n Provided: " + row[required_csv_headers["Issue Date"]])
        if issue_date_value[0] not in found_years:
            found_years.append(issue_date_value[0])

        # Check if its a valid series
        series_value = re.findall( valid_series_regex, row[required_csv_headers["Series"]] )[0]
        if series_value[1] not in valid_series:
            raise Exception( "Valid Bond series are: " + str(valid_series) + "\n Provided: " + row[required_csv_headers["Series"]])
        if series_value[1] not in found_series:
            found_series.append(series_value[1])

    if print_flag:
        print("Found Denom: " + str(found_denom)   + "\n\
               Found Series: " + str(found_series) + "\n\
               Found Years: " + str(found_years)   + "\n"
        )
    # Return all of the denoms, series, and years in the csv
    return (found_denom, found_series, found_years)

def fetch_bond_data(denoms, series, years, print_flag):

    # Redemption period is always today
    today = date.today()
    today = date.today()
    redemp_period = 'redemp_period:eq:' + today.strftime("%Y-%m")

    # form issue_name filter
    issue_name = 'issue_name:in:('
    for s in series:
        if issue_name[-1] != '(':
            issue_name += ","
        issue_name += "Series%20" + s # html encoded str
    issue_name += ')'

    # form issue_year filter
    issue_year = 'issue_year:in:('
    for y in years:
        if issue_year[-1] != '(':
            issue_year += ","
        issue_year += y
    issue_year += ')'

    filters = issue_year + ',' + redemp_period + ',' + issue_name    
    parameters = '?filter=' + filters
    get_request = BASE_URL + BOND_ENDPOINT + parameters
    response = requests.get( get_request )
    payload = response.json()

    cur_page = ""
    next_page = ""
    last_page = payload['links']['last']

    # Dictionary to hold in memory the API info. Keys are a tuple of ( issue-date(s), issue_name/series )
    treasury_dict = { }

    # Continue scraping until 'last' != 'self'
    while ( cur_page != last_page ):

        cur_page = payload['links']['self']
        next_page = payload['links']['next']

        for data in payload['data']:
            issue_months = data['issue_months']
            issue_year = data['issue_year']
            bond_info = []
            # If months is a range
            if ( '-' in issue_months ):
                month_range = issue_months.split('-')
                start = datetime.datetime.strptime( issue_year + "-" + month_range[0].strip(), "%Y-%b").strftime("%Y-%m")
                end =  datetime.datetime.strptime( issue_year + "-" + month_range[1].strip(), "%Y-%b").strftime("%Y-%m")
                bond_info.append(start)
                bond_info.append(end)
            else:
                bond_date = datetime.datetime.strptime(issue_year + "-" + issue_months.strip(),  "%Y-%b").strftime("%Y-%m")
                bond_info.append(bond_date)
            
            bond_info.append( data['issue_name'] )
            treasury_dict[ tuple(bond_info) ] = data

        #If there is a next page, continue
        if ( next_page is not None ):
            get_request = BASE_URL + BOND_ENDPOINT + parameters + next_page
            response = requests.get( get_request )
            payload = response.json()

    # Print method stats   
    total_pages = payload['meta']['total-pages']
    total_count = payload['meta']['total-count']     
    print( "Scanned through " + str( total_count ) + " results on " + str( total_pages ) + " pages." )

    return treasury_dict

def get_api_fields():
    get_request = BASE_URL + BOND_ENDPOINT
    # Attempt to reach out to USA Treasury beforehand to gather some data
    #TODO: Catch error if cannot connect
    initial_response = requests.get( get_request )
    available_fields = ( initial_response.json() )['meta']['dataTypes']
    for field in available_fields:
        print( "\t\tField: " + field + "\tType: " + available_fields[field] )


if __name__ == "__main__":
   main(sys.argv[1:])

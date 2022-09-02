import sys, getopt
import datetime
from datetime import date
import csv
import re
import requests
import os

BASE_URL ='https://api.fiscaldata.treasury.gov/services/api/fiscal_service'
BOND_ENDPOINT ='/v2/accounting/od/redemption_tables'

def usage():
    print('Usage:\n\tbond.py [-h,f] -i <inputfile>\n\
            Options:\n\
            -h,--help\t Prints usage\n\
            -f,--fields\t Availble fields for search from (url) ' + BASE_URL)

def info():
    print( "\n\
            --------------------------------------------------------------------------------------\n\
            This script parses a CSV that contains USA Treasury Bonds information.\n\
            It then queries the USA Treasury API for the current redemption value.\n\
            --------------------------------------------------------------------------------------\n\
            For more information on the contents of the USA Treasury API, use option -f, or the following documentation ->\n\
            Fields: https://fiscaldata.treasury.gov/datasets/redemption-tables/redemption-tables\n\
            Filters: https://fiscaldata.treasury.gov/api-documentation/#filters\n" )

# Main loop to parse command line inputs
def main(argv):

    given_input = False
    modify_input = False
    input_file = ''
    try:
        opts, args = getopt.getopt(argv, "hfmi:",["input="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-i", "--input"):
            input_file = arg
            given_input = True
        elif opt in ("-m", "--modify") :
            modify_input = True
        elif opt in ("-f", "--fields"):
            get_api_fields()
            sys.exit()

    if not given_input:
        print("Input file is required.")
        usage()
        sys.exit(2)

    (denoms, series, years) = scan_csv(input_file)
    #Dictionary of relevant bond info. Key is issue_date
    usa_bonds = curl_api(denoms, series, years)
    print(usa_bonds)
    
    #compare_results(input_file, usa_bon)
    #if modify_input_file:
    #    modify_csv(input_file)
    #else:

def get_api_fields():
    get_request = BASE_URL + BOND_ENDPOINT
    # Attempt to reach out to USA Treasury beforehand to gather some data
    #TODO: Catch error if cannot connect
    initial_response = requests.get( get_request )
    available_fields = ( initial_response.json() )['meta']['dataTypes']
    for field in available_fields:
        print( "\t\tField: " + field + "\tType: " + available_fields[field] )


def scan_csv(inputfile):

    #treasury_data = curl_bond_data()
    # Checking curl response
    #for key, value in treasury_data.items():
       #print( str(key) + ' -> ' + str(value) + '\n\n')
       #print( str(key) + '\n\n')

    valid_denom = ["10", "25", "50", "75", "100", "200", "500", "1000", "5000", "10000"]
    valid_series = ["I", "E", "EE", "H", "HH"]
    valid_series_regex = "(Series )?(I|E{2}|E|H{2}|H)"
    # Init a dictionary so we can store where certain csv columns are
    required_csv_headers = { "Denom": -1, "Series": -1, "Issue Date": -1 }
    
    csvfile = open( inputfile, 'r', encoding="utf-8" )

    #store the index of the headers
    csv_headers = csvfile.readline().split(',')
    for index, header in enumerate(csv_headers):
        if header in required_csv_headers.keys():
            required_csv_headers[header] = index

    # Keep track of unique found values so that we can form a targeted query
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


    return (found_denom, found_series, found_years)

def curl_api(denoms, series, years):

    # Redemption period is always today
    today = date.today()
    today = date.today()
    redemp_period = 'redemp_period:eq:' + today.strftime("%Y-%m")

    # form issue_name filter
    issue_name = 'issue_name:in:('
    for s in series:
        if issue_name[-1] != '(':
            issue_name += ","
        issue_name += "Series%20" + s
    issue_name += ')'

    #form issue_year filter
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

    # Dictionary to hold date driven values
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
            
            bond_info.append(data['issue_name'])
            treasury_dict[ tuple(bond_info) ] = data

        #If there is a next page
        if ( next_page is not None ):
            get_request = BASE_URL + BOND_ENDPOINT + parameters + next_page
            response = requests.get( get_request )
            payload = response.json()

    # Print method stats   
    total_pages = payload['meta']['total-pages']
    total_count = payload['meta']['total-count']     
    print( "Scanned through " + str( total_count ) + " results on " + str( total_pages ) + " pages." )

    return treasury_dict


  #int_earned_key = 'int_earned_' + denom_value + '_amt'
    #redemp_value_key = 'redemp_value_' + denom_value + '_amt'
    #added_csv_headers = { "Interest Rate": -1, "Interest": -1, "Current Value": -1 }
    #modified_file =[]

 # Checking if the treasury data is relevant to the user data
    # Then, change the row for a write back
    # if (mimic_tuple in treasury_data): # issue_date is a single year-month
    #     row[5] = treasury_data[mimic_tuple][yield_int] + '%'
    #     row[6] = '$' + treasury_data[mimic_tuple][int_earned]
    #     row[7] = '$' + treasury_data[mimic_tuple][redemp_value]
    # else: 
    #     for key, value in treasury_data.items(): # Iterate through keys to find a possible match
    #         if ( set(mimic_tuple).issubset(key) ): # issue date is a range
    #             row[5] = value[yield_int] + '%'
    #             row[6] = '$' + value[int_earned]
    #             row[7] = '$' + value[redemp_value]
    # modified_file.append(row)
               
    # with open(inputfile, 'w') as csvfile:
    #    writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    #    for data in modified_file:
    #         writer.writerow(data)

if __name__ == "__main__":
   main(sys.argv[1:])

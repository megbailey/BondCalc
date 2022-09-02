import sys, getopt
import datetime
from datetime import date
import csv
import re
import requests

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

def get_api_fields():
    get_request = BASE_URL + BOND_ENDPOINT
    # Attempt to reach out to USA Treasury beforehand to gather some data
    #TODO: Catch error if cannot connect
    initial_response = requests.get( get_request )
    available_fields = ( initial_response.json() )['meta']['dataTypes']
    for field in available_fields:
        print( "\t\tField: " + field + "\tType: " + available_fields[field] )

# Main loop to parse command line inputs
def main(argv):

    given_input_file = False
    input_file = ''
    try:
        opts, args = getopt.getopt(argv, "hfi:",["input="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-i", "--input"):
            input_file = arg
            given_input_file = True
        elif opt in ("-f", "--fields"):
            get_api_fields()
            sys.exit()

    if not given_input_file:
        print("Input file is required.")
        usage()
        sys.exit(2)
    else:
        print(scan_csv(input_file))


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


def curl_bond_data():
    today = date.today()
    today_redemp_period = today.strftime("%Y-%m")

    #TODO: make user input / scraped from csv
    issue_name = 'issue_name:eq:Series%20EE'
    issue_year = 'issue_year:in:(1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011)'

    # Redemption period is always today
    redemp_period = 'redemp_period:eq:' + today_redemp_period
    filters = issue_year + ',' + redemp_period + ',' + issue_name    
    parameters = '?filter=' + filters
    get_request = BASE_URL + BOND_ENDPOINT + parameters

    #int_earned_key = 'int_earned_' + denom_value + '_amt'
    #redemp_value_key = 'redemp_value_' + denom_value + '_amt'
        #added_csv_headers = { "Interest Rate": -1, "Interest": -1, "Current Value": -1 }
    yield_int = 'yield_from_issue_pct'
    modified_file =[]

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
            bond_list = []
            # If months is a range
            if ( '-' in issue_months ):
                month_range = issue_months.split('-')
                start = datetime.datetime.strptime( issue_year + "-" + month_range[0].strip(), "%Y-%b").strftime("%Y-%m")
                end =  datetime.datetime.strptime( issue_year + "-" + month_range[1].strip(), "%Y-%b").strftime("%Y-%m")
                bond_list.append(start)
                bond_list.append(end)
            else:
                bond_date = datetime.datetime.strptime(issue_year + "-" + issue_months.strip(),  "%Y-%b").strftime("%Y-%m")
                bond_list.append(bond_date)
            
            bond_list.append(data['issue_name'])
            treasury_dict[ tuple(bond_list) ] = data

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


if __name__ == "__main__":
   main(sys.argv[1:])

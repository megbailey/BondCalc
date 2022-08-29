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
    try:
        initial_response = requests.get( get_request )
    except MaxRetryError:
        print("Could not reach (url) " + get_request + ". Aborting." )
    else:
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
        process_csv(input_file)


def curl_bond_data():
    today = date.today()
    today_redemp_period = today.strftime("%Y-%m")

    #TODO: make user input / scraped from csv
    issue_name = 'issue_name:eq:Series%20EE'
    issue_year = 'issue_year:in:(1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011)'
    values = [ 50, 200, 1000 ]

    # Redemption period is always today
    redemp_period = 'redemp_period:eq:' + today_redemp_period
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
            bond_list = []
            # If months is a range
            if ( issue_months.__contains__('-') ):
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

def process_csv(inputfile):

    treasury_data = curl_bond_data()
    
    # Checking curl response
    #for key, value in treasury_data.items():
       #print( str(key) + ' -> ' + str(value) + '\n\n')
       #print( str(key) + '\n\n')
        
    #csv_file = "/Users/meganbailey/git/BondCalc/MB - USA SB - Sheet1.csv"
    csv_headers = ['Denom', 'Series', 'Issue Price', 'Issue Date', 'Serial #', 'Interest Rate', 'Interest', 'Current Value']
    yield_int = 'yield_from_issue_pct'
    modified_file =[]
    
    with open( inputfile, 'r', encoding="utf-8" ) as csvfile:
        csv_reader = csv.reader(csvfile)

        for row in csv_reader:
            denom = re.sub('[\$,]', '', row[0])
            
            issue_date = row[3]
            int_earned = 'int_earned_' + denom + '_amt'
            redemp_value = 'redemp_value_' + denom + '_amt'

            if ( 'Series' not in row[1] ):
                row[1] = 'Series ' + row[1]
            mimic_tuple = ( issue_date, row[1] )

            # Checking if the treasury data is relevant to the user data
            # Then, change the row for a write back
            if (mimic_tuple in treasury_data): # issue_date is a single year-month
                row[5] = treasury_data[mimic_tuple][yield_int] + '%'
                row[6] = '$' + treasury_data[mimic_tuple][int_earned]
                row[7] = '$' + treasury_data[mimic_tuple][redemp_value]
            else: 
                for key, value in treasury_data.items(): # Iterate through keys to find a possible match
                    if ( set(mimic_tuple).issubset(key) ): # issue date is a range
                        row[5] = value[yield_int] + '%'
                        row[6] = '$' + value[int_earned]
                        row[7] = '$' + value[redemp_value]
            modified_file.append(row)
               
    with open(inputfile, 'w') as csvfile:
       writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
       for data in modified_file:
            writer.writerow(data)




if __name__ == "__main__":
   main(sys.argv[1:])

import datetime
from datetime import date
import requests

BASE_URL ='https://api.fiscaldata.treasury.gov/services/api/fiscal_service'
BOND_ENDPOINT ='/v2/accounting/od/redemption_tables'

def read_write_CSV( file_name ):
    
    """ csv_uniques = []
    with open( file_name, 'r', encoding="utf-8" ) as csv_file:
        reader = csv.reader( csv_file )

        for row in reader:
            denom = row[0]
            series = row[1]
            issue_date = row[3]
            csvTuple = (denom, series, issue_date)
            if  """

def curl_bond_data():
    today = date.today()
    print(  type( today ) )
    today_redemp_period = today.strftime("%Y-%m")
    print( today_redemp_period)
    print( today.strftime("%b") ) 

    #TODO: make user input / scraped from csv
    issue_name = 'issue_name:eq:Series%20EE'
    issue_year = 'issue_year:in:(1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011)'
    values = [ 50, 200, 1000 ]

    # Redemption period is always today
    redemp_period = 'redemp_period:eq:' + today_redemp_period
    filters = issue_year + ',' + redemp_period + ',' + issue_name
    
    #parameters = '?fields=' + fields + '&filter=' + filters
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
            
            # print(  data['redemp_period'] + " " + data['issue_year'] + " " + data['issue_months'] + " " + data['issue_name'] + 
            #         " 50 -> " + data['int_earned_50_amt'] + " " + data['redemp_value_50_amt'] + 
            #         " 200 -> " + data['int_earned_200_amt'] + " " + data['redemp_value_200_amt']  + 
            #         " 1000 -> " + data['int_earned_1000_amt'] + " " + data['redemp_value_1000_amt']
            #         )

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

def main():

    get_request = BASE_URL + BOND_ENDPOINT
    response = requests.get( get_request )
    payload = response.json()
    available_fields = payload['meta']['dataTypes']

    print( "\n\
            --------------------------------------------------------------------------------------\n\
            This script parses a CSV or spreadsheet that contains USA Treasury Bonds information.\n\
            It then queries the USA Tresurey API for the redemption value.\n\
            --------------------------------------------------------------------------------------\n\
            Current fields that can be returned ->\n" )
    for field in available_fields:
        print( "\t\tField: " + field + "\tType: " + available_fields[field] )

    print( "\n\
            -------------------------------------------------------------------------------------\n\
            See the following documentation for more requests ->\n\
            Fields: https://fiscaldata.treasury.gov/datasets/redemption-tables/redemption-tables\n\
            Filters: https://fiscaldata.treasury.gov/api-documentation/#filters\n\
            -------------------------------------------------------------------------------------\n")
    treasury_data = curl_bond_data()
    for entry in treasury_data:
        print(entry)
        #print('{0} -> ' + treasury_data[entry].format(entry))
        
    read_write_CSV("/Users/meganbailey/git/BondCalc/MB - USA SB - Sheet1.csv")


    #fields='issue_name,issue_months,issue_year,int_earned_50_amt,redemp_value_50_amt,yield_from_issue_pct'
    #bond_date = strptime

if __name__=="__main__":
    main()

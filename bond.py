import json
import requests


def main():
    base_url ='https://api.fiscaldata.treasury.gov/services/api/fiscal_service'
    bond_endpoint ='/v2/accounting/od/redemption_tables'

    get_request = base_url + bond_endpoint
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

    #fields='issue_name,issue_months,issue_year,int_earned_50_amt,redemp_value_50_amt,yield_from_issue_pct'
    values = [ 50, 200, 1000]
    redemp_period = 'redemp_period:eq:2022-06'
    issue_name = 'issue_name:eq:Series%20EE'
    issue_year = 'issue_year:in:(1998,1999,2000,2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011)'
    filters= issue_year + ',' + redemp_period + ',' + issue_name
    
    #parameters = '?fields=' + fields + '&filter=' + filters
    parameters = '?filter=' + filters
    get_request = base_url + bond_endpoint + parameters

    response = requests.get( get_request )
    payload = response.json()

    metadata = payload['meta']
    total_pages = payload['meta']['total-pages']
    total_count = payload['meta']['total-count']


    cur_page = 'link to the current page'
    next_page = 'link to the neext page'
    last_page = payload['links']['last']

    # Continue scraping until 'last' != 'self'
    while ( cur_page != last_page ):

        cur_page = payload['links']['self']
        next_page = payload['links']['next']

        for data in payload['data']:
            print(  data['redemp_period'] + " " + data['issue_year'] + " " + data['issue_months'] + " " + data['issue_name'] + 
                    " 50 -> " + data['int_earned_50_amt'] + " " + data['redemp_value_50_amt'] + 
                    " 200 -> " + data['int_earned_200_amt'] + " " + data['redemp_value_200_amt']  + 
                    " 1000 -> " + data['int_earned_1000_amt'] + " " + data['redemp_value_1000_amt']
                    )
        #If there is a next page
        if ( next_page is not None ):
            get_request = base_url + bond_endpoint + parameters + next_page
            response = requests.get( get_request )
            payload = response.json()


if __name__=="__main__":
    main()

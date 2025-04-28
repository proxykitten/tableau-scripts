## GET ALL WORKBOOKS IN TABLEAU SERVER

This script is to get all and list all workbooks inside the Tableau Server. The script itself fetches these data:
- Site Name
- Workbook ID
- Workbook Name
- Content URL
- Webpage URL
- Created At
- Updated At
- Owner
- Project


## USAGE

1. Install the required libraries

    `pip install -r requirements.csv`

2. Simply just run these commands

    `python3 get-wb-runner.py --tableau-url <your-tableau-server-url> --output <output-name> --username <tableau-server-username>`
    
    Example:

    `python3 get-wb-runner.py --tableau-url https://myserver.com --output workbook-list.csv --username admin`

## LIMITATION

1. For now, the limitation is it can only fetch the workbook with maximum number 1000 per site.

## ENVIRONMENT

Tested on Python 3.6.8. It should work with Python 3.6 and above.
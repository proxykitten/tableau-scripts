## GET ALL WORKBOOKS IN TABLEAU SERVER

This script retrieves all workbooks inside the Tableau Server. The script itself fetches these data:
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

    ```bash
    pip install -r requirements.csv
    ```

2. Simply just run these commands

    ```bash
    python3 get-tableau-workbook.py --tableau-url <your-tableau-server-url> --output <output-name> [--pages <number]
    ```
    
    Example:

    ```bash
    python3 get-tableau-workbook.py --tableau-url https://myserver.com --output workbooks-list.csv
    ```

## LIMITATION / KNOWN ISSUES

## ENVIRONMENT

Tested on Python 3.6.8. It should work with Python 3.6 and above.

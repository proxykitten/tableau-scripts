## GET ALL DATASOURCES IN TABLEAU SERVER

This script retrieves all datasources inside the Tableau Server. The script itself fetches these data:
- Site Name
- Site ID
- Project
- Datasource Name
- contentURL
- Type
- Owner


## USAGE

1. Install the required libraries

    ```bash
    pip install -r requirements.csv
    ```

2. Simply just run these commands

    ```bash
    python3 get-tableau-datasource.py --tableau-url <your-tableau-server-url> --output <output-name> [--pages <number]
    ```
    
    Example:

    ```bash
    python3 get-tableau-datasource.py --tableau-url https://myserver.com --output datasources-list.csv
    ```

## LIMITATION / KNOWN ISSUES

## ENVIRONMENT

Tested on Python 3.6.8. It should work with Python 3.6 and above.

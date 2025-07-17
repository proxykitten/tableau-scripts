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

When the Tableau Server contains two or more sites, the REST API does not return the type for all datasources for unknown reason. However, in testing with a single-site Tableau Server, the type field was returned correctly for each datasource. I tested it using Tableau Server REST API version 3.20 and 3.23 but the result still same. This is not the issue of the script itself, but the REST API.

## ENVIRONMENT

Tested on Python 3.6.8. It should work with Python 3.6 and above.

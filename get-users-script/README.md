## GET ALL USERS IN TABLEAU SERVER

This script retrieves all users in the Tableau Server. It fetches the following data:
- Display Name
- Username
- Email
- Site Role
- License Level
- Last Login (UTC)
- User ID

## USAGE

1. Install the required libraries:

    ```bash
    pip install -r requirements.txt
    ```

2. Run the script with the following command:

    ```bash
    python3 get-user-runner.py --tableau-url <your-tableau-server-url> --output-file <output-file-name>.csv [--api-version <api-version>]
    ```

    Example:

    ```bash
    python3 get-user-runner.py --tableau-url https://myserver.com --output-file users-list.csv
    ```

## LIMITATION / KNOWN ISSUES

## ENVIRONMENT

Tested on Python 3.6.8. The script should work with Python 3.6 and above.

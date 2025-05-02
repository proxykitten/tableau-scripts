## GET ALL USERS IN TABLEAU SERVER

This script retrieves all users in the Tableau Server. It fetches the following data:
- Display Name
- Username
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

1. The user's site role is fetches from the first site found. Be sure to double check if some users are a member or multiple sites.
2. The user's license is depend on the user's role. If user is a member of multiple site, the license may be wrong.

## ENVIRONMENT

Tested on Python 3.6.8. The script should work with Python 3.6 and above.

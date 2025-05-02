import logging
import argparse
import requests
import xml.etree.ElementTree as ET
import os
import csv
import re
import getpass
from datetime import datetime

# Setup basic logging
logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s - (%(funcName)s.%(lineno)d)',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# Global constants
NAMESPACE = {'ns': 'http://tableau.com/api'}
BASE_URL = None
USERNAME = None
PASSWORD = None

# Role hierarchy
ROLE_PRIORITY = {
    "Server Administrator": 10,
    "Site Administrator Creator": 9,
    "Creator": 8,
    "Site Administrator Explorer": 7,
    "Explorer (Can Publish)": 6,
    "Explorer": 5,
    "Viewer": 4,
    "Unlicensed": 0
}

def get_role_priority(role):
    """Returns the priority of the given role."""
    return ROLE_PRIORITY.get(role, -1)  # Default to -1 if role is unknown

def authenticate(site_id=''):
    logger.debug(f"Authenticating (site_id='{site_id}')")
    headers = {'Content-Type': 'application/xml'}
    xml_body = f'''
    <tsRequest>
        <credentials name="{USERNAME}" password="{PASSWORD}">
            <site contentUrl="{site_id}" />
        </credentials>
    </tsRequest>
    '''
    try:
        response = requests.post(f"{BASE_URL}/auth/signin", headers=headers, data=xml_body)
        response.raise_for_status()
        return ET.fromstring(response.content)
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        exit(1)

def fetch_sites(token):
    logger.debug("Fetching sites")
    headers = {'X-Tableau-Auth': token}
    try:
        response = requests.get(f"{BASE_URL}/sites", headers=headers)
        response.raise_for_status()
        return ET.fromstring(response.content)
    except Exception as e:
        logger.error(f"Fetching sites failed: {e}")
        exit(1)

def fetch_users(site_id, token):
    logger.debug(f"Fetching users for site_id='{site_id}'")
    headers = {'X-Tableau-Auth': token}
    try:
        response = requests.get(f"{BASE_URL}/sites/{site_id}/users?pageSize=500", headers=headers)
        response.raise_for_status()
        return ET.fromstring(response.content)
    except Exception as e:
        logger.error(f"Fetching users failed: {e}")
        exit(1)

def extract_token(auth_response):
    try:
        token = auth_response.find('ns:credentials', namespaces=NAMESPACE).get('token')
        return token
    except Exception as e:
        logger.error(f"Token extraction failed: {e}")
        exit(1)

def extract_site_id(auth_response):
    try:
        site_id = auth_response.find('ns:credentials/ns:site', namespaces=NAMESPACE).get('id')
        return site_id
    except Exception as e:
        logger.error(f"Site ID extraction failed: {e}")
        exit(1)

def extract_content_urls(sites_response):
    content_urls = []
    try:
        site_elements = sites_response.findall('ns:sites/ns:site', namespaces=NAMESPACE)
        for site in site_elements:
            content_url = site.get('contentUrl')
            content_urls.append(content_url)
        return content_urls
    except Exception as e:
        logger.error(f"Content URL extraction failed: {e}")
        exit(1)

def determine_license_level(site_role):
    """Returns the license level for the given site role."""
    if site_role in ['Server Administrator', 'Site Administrator Creator', 'Creator']:
        return 'Creator'
    elif site_role in ['Site Administrator Explorer', 'Explorer (Can Publish)', 'Explorer']:
        return 'Explorer'
    elif site_role == 'Viewer':
        return 'Viewer'
    else:
        return 'Unlicensed'

def clean_site_role(site_role):
    """Cleans and formats the site role."""
    if not site_role:
        return ''
    site_role = site_role.replace('CanPublish', ' (Can Publish)')
    return re.sub(r'(?<!\s|\()(?=[A-Z])', ' ', site_role).strip()

def extract_users(users_response):
    users_list = []
    try:
        user_elements = users_response.findall('ns:users/ns:user', namespaces=NAMESPACE)
        for user in user_elements:
            cleaned_site_role = clean_site_role(user.get('siteRole'))
            user_data = {
                'Display Name': user.get('fullName'),
                'Username': user.get('name'),
                'Site Role': cleaned_site_role,
                'License Level': determine_license_level(cleaned_site_role),
                'Last Login (UTC)': user.get('lastLogin'),
                'User ID': user.get('id')
            }
            users_list.append(user_data)
        return users_list
    except Exception as e:
        logger.error(f"User extraction failed: {e}")
        exit(1)

def save_to_csv(data, output_file):
    logger.debug(f"Saving {len(data)} users to '{output_file}'")
    try:
        if not data:
            raise ValueError("No data to save.")

        seen_usernames = {}
        unique_data = []

        for row in data:
            username = row['Username']
            if username not in seen_usernames:
                seen_usernames[username] = row
            else:
                # Compare the roles, keep the highest priority role
                existing_role = seen_usernames[username]['Site Role']
                new_role = row['Site Role']
                if get_role_priority(new_role) > get_role_priority(existing_role):
                    seen_usernames[username]['Site Role'] = new_role
                    seen_usernames[username]['License Level'] = determine_license_level(new_role)

        # Add the user data to unique_data
        for user in seen_usernames.values():
            unique_data.append(user)

        # Write the final data to CSV
        with open(output_file, mode='w', newline='', encoding='utf-8') as f:
            fieldnames = unique_data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_data)

            # Add the "Fetched On" line at the end
            fetched_on = datetime.utcnow().strftime('Fetched on %Y-%m-%d %H:%M:%S UTC')
            f.write(f"\n{fetched_on}\n")

        logger.info(f"Data successfully saved to '{output_file}'")
    except Exception as e:
        logger.error(f"Failed to save CSV: {e}")
        exit(1)

def main():
    global BASE_URL, USERNAME, PASSWORD

    logger.debug("Starting main function")
    parser = argparse.ArgumentParser(description="Export Tableau users to CSV")
    parser.add_argument('--tableau-url', required=True, type=str, help="Base Tableau server URL")
    parser.add_argument('--output-file', required=True, type=str, help="CSV output filename")
    parser.add_argument('--api-version', default='3.19', type=str, help="Tableau API version (default: 3.19)")

    args = parser.parse_args()

    if not args.output_file.endswith('.csv'):
        args.output_file += '.csv'

    BASE_URL = f"{args.tableau_url}/api/{args.api_version}"
    USERNAME = input("TABLEAU USERNAME: ")
    PASSWORD = getpass.getpass("TABLEAU PASSWORD: ")

    auth_response = authenticate()
    token = extract_token(auth_response)

    sites_response = fetch_sites(token)
    content_urls = extract_content_urls(sites_response)

    all_users = []

    for content_url in content_urls:
        auth_response = authenticate(content_url)
        token = extract_token(auth_response)
        site_id = extract_site_id(auth_response)

        users_response = fetch_users(site_id, token)
        users = extract_users(users_response)

        all_users.extend(users)

    if all_users:
        save_to_csv(all_users, args.output_file)
    else:
        logger.error("No users found to export.")
        exit(1)

if __name__ == '__main__':
    try:
        print('\n== Start Processing ==\n')
        main()
        print('\n== Process Finished ==\n')
    except Exception as e:
        logger.critical(f"Critical error occurred: {e}")
        exit(1)
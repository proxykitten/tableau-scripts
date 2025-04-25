import requests
import csv
import argparse
import getpass
from datetime import datetime

def log(message, debug=False, always=False):
    if debug or always:
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        print(f"{timestamp} {message}")

def sign_in(base_path, username, password, content_url="", debug=False):
    log(f"Signing in to site (contentUrl: '{content_url}')", debug)
    headers = {
        'Content-Type': 'application/xml',
        'Accept': 'application/json'
    }
    xml_data = f"""<tsRequest>
    <credentials name="{username}" password="{password}">
        <site contentUrl="{content_url}"/>
    </credentials>
</tsRequest>"""
    response = requests.post(f"{base_path}/auth/signin", headers=headers, data=xml_data)
    response.raise_for_status()
    return response.json()["credentials"]["token"], response.json()["credentials"]["site"]["id"]

def get_sites(base_path, xauth_token, debug=False):
    log("Fetching list of sites...", debug)
    headers_with_auth = {
        'X-Tableau-Auth': xauth_token,
        'Accept': 'application/json'
    }
    response = requests.get(f"{base_path}/sites", headers=headers_with_auth)
    response.raise_for_status()
    return response.json()["sites"]["site"]

def get_workbooks(base_path, site_id, xauth_token, debug=False):
    log(f"Fetching workbooks for site_id: {site_id}", debug)
    headers_with_auth = {
        'X-Tableau-Auth': xauth_token,
        'Accept': 'application/json'
    }
    response = requests.get(f"{base_path}/sites/{site_id}/workbooks?pageSize=1000", headers=headers_with_auth)
    response.raise_for_status()
    return response.json()["workbooks"]["workbook"]

def save_workbooks_to_csv(all_workbooks, filename, debug=False):
    log(f"Saving {len(all_workbooks)} workbooks to '{filename}'...", debug or True)
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Site', 'ID', 'Name', 'Content URL', 'Webpage URL',
            'Created At', 'Updated At', 'Owner', 'Project'
        ])

        for wb in all_workbooks:
            writer.writerow([
                wb.get('site_name'),
                wb.get('id'),
                wb.get('name'),
                wb.get('contentUrl'),
                wb.get('webpageUrl'),
                wb.get('createdAt'),
                wb.get('updatedAt'),
                wb.get('owner', {}).get('name'),
                wb.get('project', {}).get('name')
            ])

def main():
    parser = argparse.ArgumentParser(description="Fetch Tableau workbooks and export to a single CSV")
    parser.add_argument('--tableau-url', required=True, help='Base Tableau REST API URL (e.g., https://server/api/3.18)')
    parser.add_argument('--output-file', required=True, help='Output CSV file name (e.g., out.csv)')
    parser.add_argument('--username', required=True, help='Tableau username')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()
    base_path = args.tableau_url
    output_file = args.output_file
    username = args.username
    debug = args.debug

    password = getpass.getpass("Enter Tableau password: ")

    log("Starting script...", debug or True)
    xauth_token, _ = sign_in(base_path, username, password, debug=debug)
    sites = get_sites(base_path, xauth_token, debug=debug)

    all_workbooks = []

    for site in sites:
        content_url = site['contentUrl']
        site_id = site['id']
        site_name = site.get('name')

        log(f"Processing site: {site_name} (contentUrl: '{content_url}')", debug or True)

        # Re-auth for each site
        xauth_token, site_id = sign_in(base_path, username, password, content_url, debug=debug)
        workbooks = get_workbooks(base_path, site_id, xauth_token, debug=debug)

        for wb in workbooks:
            wb['site_name'] = site_name

        all_workbooks.extend(workbooks)
        log(f"Collected {len(workbooks)} workbooks from site '{site_name}'", debug or True)

    save_workbooks_to_csv(all_workbooks, output_file, debug=debug)
    log("✅ Done!", debug or True)

if __name__ == "__main__":
    main()
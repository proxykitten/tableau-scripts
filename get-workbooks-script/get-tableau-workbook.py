import argparse
import getpass
import requests
import csv
import sys
from datetime import datetime

def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def sign_in(base_path, username, password, content_url=""):
    log(f"Signing in to site (contentUrl: '{content_url}')")
    headers = {
        'Content-Type': 'application/xml',
        'Accept': 'application/json'
    }
    xml_data = f"""<tsRequest>
    <credentials name="{username}" password="{password}">
        <site contentUrl="{content_url}"/>
    </credentials>
</tsRequest>"""

    response = requests.post(f"{base_path}/api/3.20/auth/signin", headers=headers, data=xml_data)
    response.raise_for_status()

    creds = response.json()["credentials"]
    return creds["token"], creds["site"]["id"]

def get_sites(base_path, xauth_token):
    log("Fetching list of sites...")
    headers = {
        'X-Tableau-Auth': xauth_token,
        'Accept': 'application/json'
    }

    response = requests.get(f"{base_path}/api/3.20/sites", headers=headers)
    response.raise_for_status()
    return response.json()["sites"]["site"]

def get_workbooks(base_path, site_id, xauth_token, pages=1):
    all_workbooks = []
    headers = {
        'X-Tableau-Auth': xauth_token,
        'Accept': 'application/json'
    }

    for page in range(1, pages + 1):
        url = f"{base_path}/api/3.20/sites/{site_id}/workbooks?pageSize=1000&pageNumber={page}"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            page_workbooks = response.json().get("workbooks", {}).get("workbook", [])

            if not page_workbooks:
                log(f"  ℹ️  Page {page} returned 0 workbooks")
            else:
                log(f"  → Page {page}: {len(page_workbooks)} workbooks")
                all_workbooks.extend(page_workbooks)

        except requests.RequestException as e:
            log(f"  ⚠️  Skipping page {page} due to error: {e}")
            continue

    return all_workbooks

def save_workbooks_to_csv(all_workbooks, filename):
    log(f"Saving {len(all_workbooks)} workbooks to '{filename}'...")
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

        writer.writerow([])
        writer.writerow([f"Fetched on {datetime.now().strftime('%Y-%m-%d')}"])

def main():
    parser = argparse.ArgumentParser(description="Export Tableau workbooks from all sites to CSV file.")
    parser.add_argument('--tableau-url', required=True, help='Base Tableau REST API URL (e.g., https://my-tableau.com)')
    parser.add_argument('--output', default='workbooks_export.csv', help='Output CSV filename (default: workbooks_export.csv)')
    parser.add_argument('--pages',type=int, default=1, help='Number of pages to fetch per site (1 page = up to 1000 workbooks). For example, use --pages 3 to fetch up to 3000 per site.')
    args = parser.parse_args()

    output_file = args.output if args.output.lower().endswith(".csv") else args.output + ".csv"

    username = input("Enter Tableau username: ")
    password = getpass.getpass("Enter Tableau password: ")

    log("Starting workbook export...")

    try:
        xauth_token, _ = sign_in(args.tableau_url, username, password)
    except Exception as e:
        log(f"Failed to authenticate: {e}")
        sys.exit(1)

    try:
        sites = get_sites(args.tableau_url, xauth_token)
    except Exception as e:
        log(f"Failed to fetch sites: {e}")
        sys.exit(1)

    all_workbooks = []

    for site in sites:
        site_name = site.get("name")
        content_url = site.get("contentUrl")

        log(f"Processing site: {site_name} (contentUrl: '{content_url}')")

        try:
            xauth_token, site_id = sign_in(args.tableau_url, username, password, content_url)
            workbooks = get_workbooks(args.tableau_url, site_id, xauth_token, args.pages)
        except Exception as e:
            log(f"Failed to fetch workbooks for site '{site_name}': {e}")
            continue

        for wb in workbooks:
            wb['site_name'] = site_name

        log(f"  → Found {len(workbooks)} workbooks in '{site_name}'")
        all_workbooks.extend(workbooks)

    save_workbooks_to_csv(all_workbooks, output_file)
    log("✅ Done.")

if __name__ == "__main__":
    main()

import argparse
import getpass
import requests
import csv
import sys
from datetime import datetime

def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def signin(tableau_url, username, password, content_url=""):
    url = f"{tableau_url}/api/3.20/auth/signin"
    headers = {
        "Content-Type": "application/xml",
        "Accept": "application/json"
    }
    xml_payload = f"""
    <tsRequest>
        <credentials name="{username}" password="{password}">
            <site contentUrl="{content_url}"/>
        </credentials>
    </tsRequest>
    """.strip()

    response = requests.post(url, headers=headers, data=xml_payload)
    response.raise_for_status()
    return response.json()["credentials"]

def get_sites(tableau_url, token):
    url = f"{tableau_url}/api/3.20/sites"
    headers = {
        "X-Tableau-Auth": token,
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["sites"]["site"]

def get_datasources(tableau_url, site_id, token, pages=1):
    all_datasources = []
    headers = {
        "X-Tableau-Auth": token,
        "Accept": "application/json"
    }

    for page in range(1, pages + 1):
        url = f"{tableau_url}/api/3.20/sites/{site_id}/datasources?pageSize=1000&pageNumber={page}"
        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            break
        response.raise_for_status()

        page_data = response.json().get("datasources", {}).get("datasource", [])
        if not page_data:
            break
        all_datasources.extend(page_data)

    return all_datasources

def main():
    parser = argparse.ArgumentParser(description="Export Tableau datasources across all sites to CSV.")
    parser.add_argument("--tableau-url", required=True, help="Base Tableau URL like https://my-tableau.com")
    parser.add_argument("--output", default="datasources_export.csv", help="Output CSV filename")
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Number of pages to fetch per site (1 page = up to 1000 datasources). "
             "For example, use --pages 3 to fetch up to 3000 datasources per site. Default is 1."
    )
    args = parser.parse_args()

    output_file = args.output if args.output.lower().endswith(".csv") else args.output + ".csv"

    username = input("Enter Tableau username: ")
    password = getpass.getpass("Enter Tableau password: ")

    log("Authenticating to Tableau Server...")
    try:
        creds = signin(args.tableau_url, username, password)
    except Exception as e:
        log(f"Failed to authenticate: {e}")
        sys.exit(1)

    global_token = creds["token"]
    sites = get_sites(args.tableau_url, global_token)

    rows = []
    for site in sites:
        site_name = site["name"]
        site_id = site["id"]
        content_url = site["contentUrl"]

        log(f"Processing site: {site_name}")

        try:
            creds_site = signin(args.tableau_url, username, password, content_url)
            site_token = creds_site["token"]
            site_id = creds_site["site"]["id"]
        except Exception as e:
            log(f"Failed to authenticate to site '{site_name}': {e}")
            continue

        datasources = get_datasources(args.tableau_url, site_id, site_token, args.pages)
        log(f"  → Found {len(datasources)} datasources in '{site_name}'")

        for ds in datasources:
            row = {
                "site": site_name,
                "id": ds.get("id", ""),
                "project": ds.get("project", {}).get("name", ""),
                "name": ds.get("name", ""),
                "contentUrl": ds.get("contentUrl", ""),
                "type": ds.get("type", ""),
                "owner": ds.get("owner", {}).get("name", "")
            }
            rows.append(row)

    log(f"Writing {len(rows)} rows to {output_file}...")

    with open(output_file, mode="w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["site", "id", "project", "name", "contentUrl", "type", "owner"])
        writer.writeheader()
        writer.writerows(rows)

    log("Done.")

if __name__ == "__main__":
    main()

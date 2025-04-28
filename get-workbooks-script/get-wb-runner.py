import requests
import csv
import argparse
import getpass
from datetime import datetime

def log(message, debug=False, always=False):
    if debug or always:
        timestamp = datetime.utcnow().strftime("[%Y-%m-%d %H:%M:%S UTC]")  # Using UTC time
        print(f"{timestamp} {message}")

def log_request_response(request_type, url, headers, body=None, response=None, debug=False):
    if debug:
        # Log request details
        log(f"Request {request_type} {url}", debug)
        log(f"Headers: {headers}", debug)
        if body:
            log(f"Body: {body}", debug)

        # Log response details
        if response:
            log(f"Response Status Code: {response.status_code}", debug)
            log(f"Response Headers: {response.headers}", debug)
            log(f"Response Body: {response.text}", debug)

def sign_in(base_path, username, password, content_url="", debug=False, api_version="3.19"):
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
    
    # Log request before sending
    log_request_response('POST', f"{base_path}/api/{api_version}/auth/signin", headers, xml_data, debug=debug)
    
    response = requests.post(f"{base_path}/api/{api_version}/auth/signin", headers=headers, data=xml_data)
    response.raise_for_status()
    
    # Log the response
    log_request_response('POST', f"{base_path}/api/{api_version}/auth/signin", headers, xml_data, response=response, debug=debug)
    
    return response.json()["credentials"]["token"], response.json()["credentials"]["site"]["id"]

def get_sites(base_path, xauth_token, debug=False, api_version="3.19"):
    log("Fetching list of sites...", debug)
    headers_with_auth = {
        'X-Tableau-Auth': xauth_token,
        'Accept': 'application/json'
    }
    
    # Log request before sending
    log_request_response('GET', f"{base_path}/api/{api_version}/sites", headers_with_auth, debug=debug)
    
    response = requests.get(f"{base_path}/api/{api_version}/sites", headers=headers_with_auth)
    response.raise_for_status()
    
    # Log the response
    log_request_response('GET', f"{base_path}/api/{api_version}/sites", headers_with_auth, response=response, debug=debug)
    
    return response.json()["sites"]["site"]

def get_workbooks(base_path, site_id, xauth_token, debug=False, api_version="3.19"):
    log(f"Fetching workbooks for site_id: {site_id}", debug)
    headers_with_auth = {
        'X-Tableau-Auth': xauth_token,
        'Accept': 'application/json'
    }
    
    # Log request before sending
    log_request_response('GET', f"{base_path}/api/{api_version}/sites/{site_id}/workbooks?pageSize=1000", headers_with_auth, debug=debug)
    
    response = requests.get(f"{base_path}/api/{api_version}/sites/{site_id}/workbooks?pageSize=1000", headers=headers_with_auth)
    response.raise_for_status()
    
    # Log the response
    log_request_response('GET', f"{base_path}/api/{api_version}/sites/{site_id}/workbooks?pageSize=1000", headers_with_auth, response=response, debug=debug)
    
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

        # Add the "Fetched on" line after all workbook rows
        writer.writerow([])
        writer.writerow([f"Fetched on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"])  # Use UTC for "Fetched on"

def main():
    parser = argparse.ArgumentParser(description="Fetch Tableau workbooks and export to a single CSV")
    parser.add_argument('--tableau-url', required=True, help='Base Tableau server URL (e.g., https://myserver.com)')
    parser.add_argument('--output-file', required=True, help='Output CSV file name (e.g., out.csv)')
    parser.add_argument('--username', required=True, help='Tableau username')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--api-version', default="3.19", help='API version (default: 3.19)')

    args = parser.parse_args()
    base_path = args.tableau_url
    output_file = args.output_file
    username = args.username
    debug = args.debug
    api_version = args.api_version

    password = getpass.getpass("Enter Tableau password: ")

    log("Starting script...", debug or True)
    
    # Ensure that the base path is properly formatted
    if not base_path.endswith('/'):
        base_path += '/'
    
    # Sign in to the Tableau server
    xauth_token, _ = sign_in(base_path, username, password, debug=debug, api_version=api_version)
    
    # Get the list of sites
    sites = get_sites(base_path, xauth_token, debug=debug, api_version=api_version)

    all_workbooks = []

    for site in sites:
        content_url = site['contentUrl']
        site_id = site['id']
        site_name = site.get('name')

        log(f"Processing site: {site_name} (contentUrl: '{content_url}')", debug or True)

        # Re-auth for each site
        xauth_token, site_id = sign_in(base_path, username, password, content_url, debug=debug, api_version=api_version)
        workbooks = get_workbooks(base_path, site_id, xauth_token, debug=debug, api_version=api_version)

        for wb in workbooks:
            wb['site_name'] = site_name

        all_workbooks.extend(workbooks)
        log(f"Collected {len(workbooks)} workbooks from site '{site_name}'", debug or True)

    save_workbooks_to_csv(all_workbooks, output_file, debug=debug)
    log(f"✅ Done! Fetching completed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", debug or True)

if __name__ == "__main__":
    main()
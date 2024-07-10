import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def fetch_html(url):
    """
    Fetches the HTML content from the given URL.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

def parse_initial_parking_pass_info(html_content):
    """
    Parses the initial HTML content to extract parking pass options.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    pass_options = soup.find('select', {'name': 'inv_id'}).find_all('option')
    
    passes_info = []
    for option in pass_options:
        if option['value']:
            pass_text = option.text.strip()
            coverage_dates = pass_text.split('(')[0].strip()
            available = pass_text.split('(')[1].split(' ')[0].strip()
            pass_id = option['value']
            passes_info.append((coverage_dates, available, pass_id))
    
    return passes_info

def fetch_pass_details(pass_id):
    """
    Fetches the HTML content for a specific parking pass option.
    """
    url = "https://secure.xpressbillpay.com/portal/payment_forms/?id=MzYzNQ%3D%3D"
    payload = {
        'inv_id': pass_id
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching details for pass ID {pass_id}: {e}")
        return None

def clean_html(raw_html):
    """
    Removes HTML tags and special characters from the input string.
    """
    clean_text = re.sub('<.*?>', '', raw_html)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    clean_text = re.sub(r'\\xc2\\xa0', ' ', clean_text)
    clean_text = re.sub(r'\\r\\n', ' ', clean_text)
    return clean_text.strip()

def parse_pass_details(html_content):
    """
    Parses the HTML content to extract the cost and validity period of a parking pass.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    cost_tag = soup.find('td', class_='instruct')
    if cost_tag:
        cost = cost_tag.find('strong').text.strip()
    else:
        cost = "Cost information not found"

    # Clean the HTML content before searching for validity information
    clean_content = clean_html(str(html_content))

    # Define regex patterns for different validity formats
    semester_pattern = re.compile(r'Valid beginning (\w+ \d{1,2}) thru (\w+ \d{1,2}), (\d{4})')
    annual_pattern = re.compile(r'Valid from (\w+ \d{1,2}, \d{4}) to (\w+ \d{1,2}, \d{4})')

    # Search for validity information using regex
    validity_text = semester_pattern.search(clean_content)
    if validity_text:
        valid_from = f"{validity_text.group(1)}, {validity_text.group(3)}"
        valid_to = f"{validity_text.group(2)}, {validity_text.group(3)}"
    else:
        validity_text = annual_pattern.search(clean_content)
        if validity_text:
            valid_from = validity_text.group(1).strip()
            valid_to = validity_text.group(2).strip()
        else:
            valid_from = "Validity information not found"
            valid_to = "Validity information not found"

    return cost, valid_from, valid_to

def scrape_parking_pass_info():
    """
    Scrapes parking pass information including cost and validity dates.
    Returns a list of dictionaries containing the pass details.
    """
    url = "https://secure.xpressbillpay.com/portal/payment_forms/?id=MzYzNQ%3D%3D"
    html_content = fetch_html(url)

    if not html_content:
        return []

    passes_info = parse_initial_parking_pass_info(html_content)
    pass_details = []

    for pass_info in passes_info:
        coverage_dates, available, pass_id = pass_info
        pass_details_html = fetch_pass_details(pass_id)

        if not pass_details_html:
            continue

        cost, valid_from, valid_to = parse_pass_details(pass_details_html)
        pass_details.append({
            "Pass Type": coverage_dates,
            'Cost': cost,
            "Available": available,
            "Valid From": valid_from,
            "Valid To": valid_to
        })

    return pass_details

def print_pass_details(pass_details):
    """
    Prints the parking pass details in a formatted way.
    """
    for pass_detail in pass_details:
        print(f"Pass Type: {pass_detail['Pass Type']}")
        print(f"Cost: {pass_detail['Cost']}")
        print(f"Available: {pass_detail['Available']}")
        print(f"Valid From: {pass_detail['Valid From']}")
        print(f"Valid Through: {pass_detail['Valid To']}")
        print("")

if __name__ == "__main__":
    pass_details = scrape_parking_pass_info()
    print_pass_details(pass_details)

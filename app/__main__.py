import os
import requests
import yaml 
import smtplib
import pdfkit # pyright: ignore[reportMissingImports]
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from argparse import ArgumentParser
from email.message import EmailMessage
from pathlib import Path

'''
-> https://api.artic.edu/api/v1/artworks/search?q=war&fields=id,title,artist_title,date_display&size=25

-> Run: python -m app run --config config/queries.yml --out out --dry-run

-> reports :
    name: "war-art"
    search: "war"
    fields: ["id", "title", "artist title", "date_display"]
    max items: 25
    recipients: ["tean@example.com" ]
'''
def scriptBanner():
    banner =r'''
  ______   _______  ________  __       __   ______   _______   __    __   ______          ______    ______   _______   ______  _______  ________ 
 /      \ |       \ |        \| \  _  |  \ /      \ |       \ |  \  /  \ /      \        /      \  /      \ |       \ |      \|       \ |       \ 
|  $$$$$$\| $$$$$$$\ \$$$$$$$$| $ / \ | $$|  $$$$$$\| $$$$$$$\| $$ /  $$|  $$$$$$\      |  $$$$$$\|  $$$$$$\| $$$$$$$\ \$$$$$$| $$$$$$$\ \$$$$$$$
| $$__| $$| $$__| $$  | $$   | $$/  $\| $$| $$  | $$| $$__| $$| $$/  $$ | $$___\$$      | $$___\$$| $$   \$$| $$__| $$  | $$  | $$__/ $$  | $$   
| $$    $$| $$    $$  | $$   | $$  $$$\ $$| $$  | $$| $$    $$| $$  $$   \$$    \        \$$    \ | $$      | $$    $$  | $$  | $$    $$  | $$   
| $$$$$$$$| $$$$$$$\  | $$   | $$ $$\$$\$$| $$  | $$| $$$$$$$\| $$$$$\   _\$$$$$$\       _\$$$$$$\| $$   __ | $$$$$$$\  | $$  | $$$$$$$   | $$   
| $$  | $$| $$  | $$  | $$   | $$$$  \$$$$| $$__/ $$| $$  | $$| $$ \$$\ |  \__| $$      |  \__| $$| $$__/  \| $$  | $$ _| $$_ | $$        | $$   
| $$  | $$| $$  | $$  | $$   | $$$    \$$$ \$$    $$| $$  | $$| $$  \$$\ \$$    $$       \$$    $$ \$$    $$| $$  | $$|   $$ \| $$        | $$   
 \$$   \$$ \$$   \$$   \$$    \$$      \$$  \$$$$$$  \$$   \$$ \$$   \$$  \$$$$$$         \$$$$$$   \$$$$$$  \$$   \$$ \$$$$$$ \$$         \$$   
                                                                                                                                                 '''                                                                             
    print(banner)
    print("SCRIPT INFO: Starting report generation...")
    return

def jinjaSetup():
    # Jinja setup for using templates
    env = Environment(loader = FileSystemLoader('templates'))
    template = env.get_template('report.html')
    return template

def setConfig(parser):
    # Load the yaml query info to feed the script SETUP
    with open(parser.config, 'r') as file:
        config = yaml.safe_load(file)
    config = config.get('reports')
    config = config[0]
    return config

def parserSetup(): #SETUP
    # Script CLI options for receiving arguments in command line
    parser = ArgumentParser(
        prog = 'Artworks Report Script',
        description='Generate a report of artworks from the Art Institute of Chicago API.'
        )

    subparsers = parser.add_subparsers(dest = 'command', required = True)

    run_parser = subparsers.add_parser('run', help='Run the report generation')
    run_parser.add_argument('--config', 
                            type = str, 
                            help = 'Input parameters path for the input information of the report: report name, search term, fields, max items, recipients for email.',
                            required = True)
    run_parser.add_argument('--out',
                            type = str,
                            help = 'Output directory for the generated report files.',
                            required = True)

    args = parser.parse_args()
    return args

def searchArtworks(search, fields, artworks, parser): #FUNCTION
    # Define the search URL and parameters
    base_search = 'https://api.artic.edu/api/v1/artworks/search'
    params = {
        'q': search,
        'fields': fields,
        'size': artworks
    }

    # Make the search request
    response = requests.get(base_search, params=params)
    if isinstance(response, requests.Response) and response.status_code == 200:
        json_data = response.json()
    else:
        print(f"SCRIPT ERROR: fetching artworks: {response.status_code}")
        return []

    if isinstance(json_data, dict) and 'data' in json_data:
        if not os.path.exists(parser.out):
            os.makedirs(parser.out)
        # Output the json query file with the search results
        with open(os.path.join(parser.out, 'query.json'), 'w', encoding='utf-8') as f:
            f.write(json.dumps(json_data))
        print(f"SCRIPT INFO: Query JSON file created successfully.")
    else:
        print(f"SCRIPT INFO: Unexpected response format: {json_data}")

    data = json_data["data"][:artworks]
    return data

def makeSearch(search_input,fields_input,max_items_input, parser):
    # Make the API fetch query call
    search_data = searchArtworks( 
        search=search_input,
        fields=fields_input,
        artworks=max_items_input,
        parser = parser
    )
    return search_data

# Timestamp of the report FUNCTION
def getTimestamp():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return timestamp

# HTML report creation MAIN
def htmlReportCreation(template, search_data, name, parser):
    timestamp = getTimestamp()
    output = template.render(data=search_data, name=name, created_at=timestamp)
    if not os.path.exists(parser.out):
        os.makedirs(parser.out)
        print('SCRIPT INFO: Output directory created successfully.')
    with open(os.path.join(parser.out, 'report.html'), 'w', encoding='utf-8') as f:
        f.write(output)
        print('SCRIPT INFO: HTML report created successfully.')
    return
    
# Convert HTML to PDF MAIN
def pdfReportCreation(file, parser):
    try:
        pdfkit.from_file(file, os.path.join(parser.out, 'report.pdf'), verbose=False, options={'enable-local-file-access': ''})
        print('SCRIPT INFO: PDF report created successfully.')
    except Exception as e:
        print(f"SCRIPT INFO: Error creating PDF: {e}")
    return


# Mailing system
def sendEmail(receivers, name, search, out_dir, SMTP_USER):
    # Set report path
    pdf_path = Path(out_dir) / 'report.pdf'
    if not pdf_path.exists():
        print(f"Error: PDF report not found at {pdf_path}")
        return
    
    # Mail message build
    msg = EmailMessage()
    msg['Subject'] = f"Artworks Report: {name}"
    msg['From'] = SMTP_USER

            # If there are more than one receivers
    if isinstance(receivers, list) and len(receivers) > 1:
        msg['To'] = ', '.join(receivers)
    else:
        msg['To'] = receivers[0]
        
    msg.set_content(f"Here is the report of the artworks with the search: {search}")

    # Attach PDF report to email
    with pdf_path.open('rb') as f:
        msg.add_attachment(
            f.read(),
            maintype='application',
            subtype='pdf',
            filename=f"artworks_report_{name}.pdf"
        )

    # Send email using environment secrets and SMTP
    with smtplib.SMTP(os.getenv('SMTP_HOST'), os.getenv('SMTP_PORT')) as server:
        server.starttls()
        server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASS'))
        server.send_message(msg)
    return

def main():
    # Show Banner
    scriptBanner()

    # Initialize parser options
    parser = parserSetup()
    
    # Set Jinja html template
    template = jinjaSetup()
    
    # Load query input
    config = setConfig(parser)

    # Set script input variables
    name = config.get('name')
    search = config.get('search')
    fields = config.get('fields'); fields = ", ".join(fields)
    max_items = config.get('max_items')
    recipients = config.get('recipients')
    
    # Execute the script search command, it also creates json query file output
    search_data = makeSearch(
        search_input=search,
        fields_input=fields,
        max_items_input=max_items,
        parser=parser
    )

    # Create the HTML report
    htmlReportCreation(template, search_data, name, parser)
    html_report_path = os.path.join(parser.out, 'report.html')

    # Create the PDF report based on HTML report
    pdfReportCreation(html_report_path, parser)

    # Mailing but depends on dry run
    return

# Script execution
main()
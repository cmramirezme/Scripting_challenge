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
# Jinja setup for using templates SETUP
env = Environment(loader = FileSystemLoader('templates'))
template = env.get_template('report.html')

def parserSetup():
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
                            required = False) #THIS MUST BE REQUIRED WHEN FINISHED

    args = parser.parse_args()
    return args

# Load the yaml query info to feed the script SETUP
with open(parserSetup().config, 'r') as file:
    config = yaml.safe_load(file)
config = config.get('reports')
config = config[0]

# Extract variables from config dictionary to use them in the script SETUP
name = config.get('name')
search = config.get('search')
fields = config.get('fields'); fields = ", ".join(fields)
max_items = config.get('max_items')
recipients = config.get('recipients')

def searchArtworks(search, fields, artworks): #FUNCTION
    # Define the search URL and parameters
    base_search = 'https://api.artic.edu/api/v1/artworks/search'
    params = {
        'q': search,
        'fields': fields,
        'size': artworks
    }

    # Make the search request
    response = requests.get(base_search, params=params)
    json_data = response.json()

    # Output the json query file with the search results
    with open('out/query.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(json_data))

    data = json_data["data"][:artworks]
    return data

# Make the API fetch query call MAIN
search_data = searchArtworks( 
    search=search,
    fields=fields,
    artworks=max_items,
)

# Timestamp of the report FUNCTION
def getTimestamp():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return timestamp

# HTML report creation MAIN
def htmlReportCreation():
    output = template.render(data=search_data, name=name, created_at=getTimestamp())
    with open('out/report.html', 'w', encoding='utf-8') as f:
        f.write(output)
    return
    
# Convert HTML to PDF MAIN
def pdfCreation(file):
    try:
        pdfkit.from_file(file, 'out/report.pdf', verbose=True, options={'enable-local-file-access': ''})
    except Exception as e:
        print(f"Error creating PDF: {e}")
    return
pdfCreation('out/report.html')

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


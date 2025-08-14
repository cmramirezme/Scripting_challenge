from logging import config
import requests
import fpdf # pyright: ignore[reportMissingModuleSource]
import yaml 
from argparse import ArgumentParser

parser = ArgumentParser(
    prog = 'Artworks Report Script',
    description='Generate a report of artworks from the Art Institute of Chicago API.'
    )

parser.add_argument('--config', 
                    type=str, 
                    help='Input parameters path for the input information of the report: report name, search term, fields, max items, recipients for email.')
args = parser.parse_args()

# Load the yaml query info to feed the script
with open(args.config, 'r') as file:
    config = yaml.safe_load(file)
config = config.get('reports')
config = config[0]

print("INFO ~~~~~ config (yaml.safe_load(file)): ", config)

# Extract variables from config dictionary to use them in the script
name = config.get('name')
search = config.get('search')
fields = config.get('fields')
max_items = config.get('max_items')
recipients = config.get('recipients')

pdf = fpdf.FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Artworks Report", ln=True, align='C')
pdf.ln(10)

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

def search_artworks(search, fields, artworks, email):
    params = {
        'q': search,
        'fields': fields,
        'size': artworks
    }
    response = requests.get('https://api.artic.edu/api/v1/artworks/search', params=params)

    json_data = response.json()
    data = json_data["data"][:artworks]

    #reportFilling(filtered_data)
    print('INFO ~~~~~ The API\'s data is: \n',data)

    return data

def reportFilling(data):
    for element in data:
        pdf.cell(15, 15, txt=str(element), ln=True, align='L')
    pdf.output('artworks_report.pdf')

search_artworks(
    search='war',
    fields='id,title,artist_title,date_display',
    artworks=5,
    email='tean@example.com'
)
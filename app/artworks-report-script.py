import requests
import fpdf
from argparse import ArgumentParser

parser = ArgumentParser(
    prog = 'Artworks Report Script',
    description='Generate a report of artworks from the Art Institute of Chicago API.'
    )

parser.add_argument('--search', type=str, help='Search term for artworks')
parser.add_argument('--fields', type=str, help='list of fields to include in the report separated by a comma')
parser.add_argument('--artworks', type=int, help='Number of artworks to include in the report')
parser.add_argument('-m', '--email', type=str, help='Email address for report delivery')

pdf = fpdf.FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Artworks Report", ln=True, align='C')
pdf.ln(10)

'''
#python3 artworks-report-script.py --search war --fields id,score,title --artworks 5 -m user@company.com
-> --argument is the way to use arguments in the bash command line (called flag or option).

-> https://api.artic.edu/api/v1/artworks/search?q=war

-> reports :
    name: "war-art"
    search: "war"
    fields: ["id", "title", "artist title", "date_display"]
    max items: 25
    recipients: ["tean@example.com" ]
'''

def search_artworks(search, fields, artworks, email):
    response = requests.get('https://api.artic.edu/api/v1/artworks/search?q={}'.format(search),
    params={'search': search})

    json_data = response.json()
    data = json_data["data"][:artworks]
    field_list = fields.split(',')

    filtered_data = []
    for item in data:
        filtered_item = {field: item[field] for field in field_list}
        filtered_data.append(filtered_item)

    reportFilling(filtered_data)
    print('The API\'s data is: \n',filtered_data)

    return filtered_data

def reportFilling(filtered_data):
    for element in filtered_data:
        pdf.cell(15, 15, txt=str(element), ln=True, align='L')
    pdf.output('artworks_report.pdf')

#query = search_artworks('war','id,_score,title',5,'user@company.com')
#print(query)

search_artworks(
    search=parser.parse_args().search,
    fields=parser.parse_args().fields,
    artworks=parser.parse_args().artworks,
    email=parser.parse_args().email
)
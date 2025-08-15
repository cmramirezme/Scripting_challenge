# Artworks Report Script

This script generates a PDF and HTML report of artworks retrieved from the [Art Institute of Chicago API](https://api.artic.edu/docs/), based on search parameters defined in a YAML configuration file.  
It can optionally email the generated report to one or more recipients.

---

## Features
- Fetches artwork data using the Art Institute of Chicago's `/artworks/search` endpoint.
- Uses [Jinja2](https://jinja.palletsprojects.com/) templates to generate an HTML report.
- Converts the HTML report into a PDF using [pdfkit](https://pypi.org/project/pdfkit/).
- Optionally emails the PDF report via SMTP.
- Supports **dry-run mode** to preview results without sending emails.
- Saves API results in a JSON file for reference.

---

## Requirements
- Python 3.8+
- Dependencies:

  `pip install requests pyyaml pdfkit jinja2`

### Configuration
1. YAML Config File

Define your report parameters in a .yml file (e.g. config/queries.yml):

reports:
  - name: "war-art"
    search: "war"
    fields: ["id", "title", "artist_title", "date_display"]
    max_items: 25
    recipients: ["team@example.com"]

name → Report identifier (used in filenames and subject lines)

search → Search keyword for the API

fields → List of fields to retrieve from the API

max_items → Number of artworks to include

recipients → List of email addresses to send the report to

2. SMTP Environment Variables

Set the following environment variables before running the script (or in a .env file you load):

export SMTP_HOST="smtp.yourprovider.com"
export SMTP_PORT="587"
export SMTP_USER="your_email@example.com"
export SMTP_PASS="your_smtp_password"

### Templates

The script uses a Jinja2 HTML template named report.html inside the templates/ directory.

Example templates/report.html:

<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ name }} Report</title>
</head>
<body>
    <h1>{{ name }} - Generated at {{ created_at }}</h1>
    <table border="1">
        <tr>
            {% for key in data[0].keys() %}
            <th>{{ key }}</th>
            {% endfor %}
        </tr>
        {% for item in data %}
        <tr>
            {% for value in item.values() %}
            <td>{{ value }}</td>
            {% endfor %}
        </tr>
        {% endfor %}
    </table>
</body>
</html>

## Usage

First have a python virtual environment created and inside it run 

`pip install -r app/requirements.txt`

Once you have installed the libraries, use `sudo apt-get install wkhtmltopdf` for the
script to be able to use the pdfkit library. After that, you have the script set for use.

### Basic Run

`python3 -m app run --config config/queries.yml --out out`

Fetches data, generates HTML and PDF reports, and sends the email.

### Dry Run (No Email Sent)
`python3 -m app run --config config/queries.yml --out out --dry-run`

Runs everything except sending the email. Useful for testing.

## Output

HTML report: out/report.html

PDF report: out/report.pdf

API JSON results: out/query.json

## Script execution flow

Banner: Displays script info.
Config Parsing: Loads YAML report settings from --config.
Data Fetch: Calls Art Institute API with search term and selected fields.
HTML Generation: Uses Jinja2 template to create a formatted HTML report.
PDF Conversion: Converts HTML to PDF using pdfkit.
Email Sending: Sends the PDF to recipients (unless --dry-run is used).

## Notes

If the output directory specified with --out does not exist, it will be created by the script.
If you plan to send emails, make sure SMTP credentials are correctly set in environment variables.
Dry-run mode is recommended before sending actual reports to see the results.

License

This script is provided under the MIT License.
ChatGPT was used in the creation of this script.
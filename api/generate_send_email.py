import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import requests
from fpdf import FPDF

sender_email = "sittingduckdetector@gmail.com"
sender_password = "1]28$VdiVJGlf@uZqp=!"
recipient_email = "sittingduckdetector@gmail.com"
subject = "Sitting Duck Weekly Report"
body = "Please find the attached PDF generated from JSON data."

def generate_pdf(json_data, pdf_file_name):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add JSON data to the PDF
    for key, value in json_data.items():
        pdf.cell(0, 10, txt=f"{key}: {value}", ln=True)

    # Save PDF
    pdf.output(pdf_file_name)
    print(f"PDF generated: {pdf_file_name}")

def send_email(recipient_email):
    # Attach email body

    response = requests.post(
  		"https://api.mailgun.net/v3/sandbox1c8d1e13f9a344d79b5a4e92db693b3f.mailgun.org/messages",
  		auth=("api", "YOUR_API_KEY"),
  		data={"from": "Excited User <mailgun@sandbox1c8d1e13f9a344d79b5a4e92db693b3f.mailgun.org>",
  			"to": ["bar@example.com", "YOU@sandbox1c8d1e13f9a344d79b5a4e92db693b3f.mailgun.org"],
  			"subject": "Hello",
  			"text": "Testing some Mailgun awesomeness!"})
    print("successfully sent weekly report")
    print(response)


def main(recipent_email):
   send_email(recipent_email)
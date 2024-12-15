import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import requests
from fpdf import FPDF
import 

sender_email = "sittingduckdetector@gmail.com"
sender_password = "1]28$VdiVJGlf@uZqp=!"
recipient_email = "sittingduckdetector@gmail.com"
subject = "Sitting Duck Weekly Report"
body = "Please find the attached PDF generated from JSON data."

def generate_pdf(json, pdf_file_name):
    

def send_email(recipient_email):
    # Attach email body

    response = requests.post(
  		"https://api.mailgun.net/v3/sandbox1c8d1e13f9a344d79b5a4e92db693b3f.mailgun.org/messages",
  		auth=("api", "YOUR_API_KEY"),
  		data={"from": "Excited User <mailgun@sandbox1c8d1e13f9a344d79b5a4e92db693b3f.mailgun.org>",
  			"to": ["bar@example.com", "YOU@sandbox1c8d1e13f9a344d79b5a4e92db693b3f.mailgun.org"],
  			"subject": "Sitting Duck Scan Result",
  			"text": "Testing some Mailgun awesomeness!"})
    print("successfully sent report")
    print(response)


def main(recipent_email):
   send_email(recipent_email)
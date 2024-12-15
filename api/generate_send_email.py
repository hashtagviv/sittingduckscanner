import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import requests
from fpdf import FPDF
from api.json_processor import get_new_subdomain_json
from api.report_pdf_generator import generate_report

sender_email = "sittingduckdetector@gmail.com"
sender_password = ""
recipient_email = "sittingduckdetector@gmail.com"
subject = "Sitting Duck Report"
body = "Please find the attached PDF generated from JSON data."



def generate_pdf(domain):
	new_subdomain_file = get_new_subdomain_json(domain)
	generate_report(new_subdomain_file)

def send_email(recipient_email, domain):
    # Attach email body
	report_pdf = generate_pdf(domain)
    
	server = smtplib.SMTP("smtp.gmail.com", 587)
	server.starttls()
	server.login(sender_email, "secret api key")  # Login securely
	server.sendmail(sender_email, recipient_email, text)
    
	print("successfully sent report")
    
	print(response)


# def main(recipent_email):
#    send_email(recipent_email)
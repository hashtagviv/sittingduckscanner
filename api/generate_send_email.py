import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from api.json_processor import get_new_subdomain_json_and_label_vulnerable_domains
from api.report_pdf_generator import generate_report

sender_email = "sittingduckdetector@gmail.com"
recipient_email = "sittingduckdetector@gmail.com"
subject = "Sitting Duck Report"
body = "Please find the attached PDF generated from JSON data."


def generate_pdf(domain):
    new_subdomain_file, temp_whole_latest_file = get_new_subdomain_json_and_label_vulnerable_domains(domain)
    return generate_report(new_subdomain_file, temp_whole_latest_file, domain)


def send_email(recipient_email, domain):
    # Attach email body
    filename = generate_pdf(domain)
    if recipient_email == "":
        return
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    pdf_file = f'pdf_report/{filename}'

    msg.attach(MIMEText('Sitting Duck Scanning Report PDF File', 'plain'))

    with open(pdf_file, 'rb') as p:
        pdf_attachment = MIMEApplication(p.read(), _subtype='pdf')
        pdf_attachment.add_header(
            'Content-Disposition', f'attachment; filename=report.pdf')
        msg.attach(pdf_attachment)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, "secret api key")
    server.sendmail(sender_email, recipient_email, msg.as_string())

    print("successfully sent report")

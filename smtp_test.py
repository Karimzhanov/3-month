from config import smtp_sender, smtp_sender_password
from email.message import EmailMessage
import smtplib

def send_email(to_email, subject, message):
    sender = smtp_sender
    password = smtp_sender_password
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    
    try:
        server.login(sender, password)
        msg = EmailMessage()
        msg['Subject'] = subject 
        msg['From'] = sender
        msg['To'] = to_email
        msg.set_content(message)
        server.send_message(msg)
        return "200 OK"
    except Exception as error:
        return f"Error: {error}"
    finally:
        server.quit()

def send_emails(emails, subject, message):
    results = {}
    for email in emails:
        result = send_email(email, subject, message)
        results[email] = result
    return results

emails = ['toktorovkurmanbek92@gmail.com', 'geektech.osh1@gmail.com', 'ktoktorov144@gmail.com', 'codexx.studio@gmail.com']
subject = "сообщение"
message = "Добрый вечер! Это тестовое сообщение."

email_results = send_emails(emails, subject, message)
for email, result in email_results.items():
    print(f"Результат отправки на {email}: {result}")

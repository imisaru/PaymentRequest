import smtplib, ssl



def sendmail(params, to, subj, body):
    port = 587  # For starttls
    smtp_server = params.get("smtpserver")#"mail.stokov.ru"
    sender_email = params.get("smtplogin")#"v000529@stokov.ru"
    password = params.get("smtppassword")#"Besikr29"

    if type(to) == list:
        message = f"From: {sender_email}\r\nTo: "+','.join(to)+"\r\n"
    else:
        message = f"From: {sender_email}\r\nTo: {to}\r\n"
    message += "Subject: "+subj+'\r\nContent-Type: text/html; charset=utf-8\r\n\n<html><meta charset="UTF-8">'+body+"</html>"

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, to, message.encode('utf-8'))


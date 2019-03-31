import pprint, requests, json, smtplib, ssl, re, creds
from email.mime.text import MIMEText
from email.header    import Header

def check_status(tracking_id, year):
    url = 'http://clientes.serpost.com.pe/prj_online/Web_Busqueda.aspx/Consultar_Tracking_Detalle_IPS'
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "Anio": year, 
        "Tracking": tracking_id,
    }
    
    # print('checking ' + tracking_id)
    r = requests.post(url, headers=headers, json=payload,)
    if r.status_code == 200:
        x = r.json()
        #print('found tracking ' + str(tracking_id))
        for status in x['d']:
            if research('ENTREGADO', status['RetornoCadena4']):
                # print('delivered ' + str(tracking_id))
                return "delivered"
            elif research('SI DESEA PUEDE RECOGERLO', status['RetornoCadena4']):
                # print('can pick up ' + str(tracking_id))
                return "can_pickup"
            else:
                # print('in transit ' + str(tracking_id))
                return "in_transit"
    else:
        print('not found')
        pass


def research(searchTerm, subject):
    #returns None if can't find target.
    return re.search(searchTerm, subject, flags=0)

def sendEmail(message):
    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    """Send email via smtp_host."""
    smtp_host = 'smtp.migadu.com'  
    login = creds.mailUser
    password = creds.mailPass
    recipients_emails = creds.mailFor
    
    msg = MIMEText(message, 'plain', 'utf-8')
    msg['Subject'] = Header('Serpost', 'utf-8')
    msg['From'] = login
    msg['To'] = recipients_emails
    
    s = smtplib.SMTP(smtp_host, 587, timeout=10)
    s.set_debuglevel(1)
    try:
        s.starttls()
        s.login(login, password)
        s.sendmail(msg['From'], recipients_emails, msg.as_string())
    finally:
        s.quit()


#packages_file = "/home/ppinzon/better_serpost/packages.json"
packages_file = "packages.json"

with open(packages_file, "r") as read_file:
    data = json.load(read_file)


toDelete = []

for package,year in list(data['unchecked'].items()):
    status = check_status(package, year)
    if status == "delivered":
        toDelete.append(package)
        #del data['unchecked'][package]
    elif status == "can_pickup":
        sendEmail(package + " can be picked up")
        toDelete.append(package)
        #del data['unchecked'][package]
    elif status == "in_transit":
        data['in_transit'][package] = year
        sendEmail(package + " is in transit")
        toDelete.append(package)
        #del data['unchecked'][package]

# print(toDelete)

for package in toDelete:
    del data['unchecked'][package]

toDelete = []

for package,year in data['in_transit'].items():
    status = check_status(package, year,)
    if status == "in_transit":
        pass
    elif status == "delivered":
        toDelete.append(package)
        #del data['unchecked'][package]
    elif status == "can_pickup":
        sendEmail(package + " can be picked up")
        toDelete.append(package)
        #del data['in_transit'][package]

# print(toDelete)

for package in toDelete:
    del data['in_transit'][package]

with open(packages_file, "w") as write_file:
    json.dump(data, write_file, indent=4)

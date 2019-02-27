import pprint, requests, json, smtplib, ssl, re, creds
from email.mime.text import MIMEText
from email.header    import Header

def check_destination(tracking_id, year):
	url = 'http://clientes.serpost.com.pe/prj_online/Web_Busqueda.aspx/Consultar_Tracking'
	headers = {
		"Content-Type": "application/json"
	}
	payload = {
		"Anio": year, 
		"Tracking": tracking_id
	}
	
	r = requests.post(url, headers=headers, json=payload,)
	if r.status_code == 200:
		x = r.json()
		if x['d'] == None:
			return False
		else:
			office = x['d'][0]['RetornoCadena6']
			return office

def check_status(tracking_id, year, office):
	url = 'http://clientes.serpost.com.pe/prj_online/Web_Busqueda.aspx/Consultar_Tracking_Detalle'
	headers = {
		"Content-Type": "application/json"
	}
	payload = {
		"Anio": year, 
		"Tracking": tracking_id,
		"Destino": office
	}
	
	r = requests.post(url, headers=headers, json=payload,)
	if r.status_code == 200:
		x = r.json()
		if r.status_code == 200:
			tomatoes = x['d']['ResulQuery']
		if research('>ENTREGADO<', tomatoes) != None:
			return "delivered"
		elif research('SI DESEA PUEDE RECOGERLO', tomatoes):
			return "can_pickup"
		else:
			return "in_transit"
			
	else:
		pass


def research(searchTerm, subject):
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


packages_file = "/home/ppinzon/better_serpost/packages.json"

with open(packages_file, "r") as read_file:
	data = json.load(read_file)

for package,year in list(data['unchecked'].items()):
	office = check_destination(package, year)
	if office == False:
		pass
	else:
		status = check_status(package, year, office)
		if status == "delivered":
			del data['unchecked'][package]
		elif status == "can_pickup":
			sendEmail(package + " can be picked up")
			del data['unchecked'][package]
		elif status == "in_transit":
			data['in_transit'][package] = year
			sendEmail(package + " is in transit")
			del data['unchecked'][package]

for package,year in data['in_transit'].items():
	office = check_destination(package, year)
	status = check_status(package, year, office)
	if status == "in_transit":
		pass
	elif status == "can_pickup":
		sendEmail(package + " can be picked up")
		del data['in_transit'][package]

with open(packages_file, "w") as write_file:
	json.dump(data, write_file, indent=4)

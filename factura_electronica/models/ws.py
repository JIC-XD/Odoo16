# -*- coding: utf-8 -*-

from suds.client import Client
from suds.xsd.doctor import Import, ImportDoctor

def ws_eface(wsdl):
	#client = False
	if not wsdl:
		print("No hay Web Service que Consumir")
	#try:
	#imp = Import('http://www.w3.org/2001/XMLSchema')
	#imp.filter.add('http://microsoft.com/wsdl/types/')
	#doctor = ImportDoctor(imp)
	client = Client(wsdl)
	#res =  client.service.RequestTransaction(xml_string)
	return client
	
#result = ws_eface(wsdl)
#print result
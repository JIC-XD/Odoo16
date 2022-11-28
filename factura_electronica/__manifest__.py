# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Factura Electronica',
    'version': '1.1',
    'category': 'Contabilidad',
	"license":  "Other proprietary",
	#'sequence': 15,
    'summary': 'Factura Electronica EcoFactura',
    'description': """
Factura Electronica
==================================

	* Emision de Factura Electronica
	* Emision de Notas de Credito y Debito
	* Configuracion de Resoluciones de Facturas
	* Parametros para conexion con Web Service EcoFactura
	* Otros
    """,
    'author': 'Xetechs, S.A.',
	'website': 'https://www.xetechs.com',
    'depends': [ 'account'],
    'data': [
		'views/account_journal_view.xml',
		'views/ir_sequence_view.xml',
		'views/account_invoice_view.xml',
		'security/ir.model.access.csv',
		#'views/corte_caja_view.xml',
	],
	
	'demo': [
		#'data/sale_demo.xml',
		#'data/product_product_demo.xml',
	
	],
	#'css': ['static/src/css/sale.css'],
    #"external_dependencies": {"python" : ["zeep"]},
	'installable': True,
	'auto_install': False,
	'application': True,
}

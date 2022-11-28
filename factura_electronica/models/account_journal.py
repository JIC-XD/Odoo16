# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
#from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP

class AccountJournal(models.Model):
	_inherit = "account.journal"
	
	is_eface = fields.Boolean('Factura Electronica', required=False, help="Marque si este diario utilizara emision de facturas electronica")
	



class AccountTax(models.Model):
	_inherit = "account.tax"
	
	type_eface = fields.Selection([
		('IVA', 'Impuesto al Valor Agregado'),
		('IDT', 'Impuesto de Turismo'),
		('TML', '***'),
		('ITP', 'Impuesto Timbre de Prensa'),
		('IDP', 'Impuesto Distribucion de Petroleo'),
		('IBV', 'Impuesto Bomberos Voluntarios'),
		('NA', 'No Aplica')], 'EFACE', required=True, default='NA', help="Impuesto para Factura electronica")


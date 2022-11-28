# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class IrSequence(models.Model):
	_inherit = "ir.sequence"
	
	resolucion = fields.Char('Resolucion No.')
	codigo_sat = fields.Char('Codigo SAT')
	establecimiento = fields.Char('Establecimiento')
	dispositivo  = fields.Char('Dispositivo')
	gui = fields.Char('Gui EFACE')
	cod_cliente = fields.Char('CodCliente')
	user_eface = fields.Char('CodUsuario', required=False, help="Usuario para ingreso al Eface Infile")
	llave_eface = fields.Char('Nit Emisor', required=False, help="LLava para ingreso al Eface Infile")
	url_ws = fields.Char('URL Web Service', required=False, help="Url para ingreso al Web Service WSDL")
	fiscal_position = fields.Selection([
			('PAGO_TRIMESTRAL', 'Sujeto a pagos trimestrales'),
			('RET_DEFINITIVA', 'Sujeto a retención definitiva'),
			('PAGO_CAJAS', 'Pago a Cajas')],"Posicion Fiscal", help="Posicion fiscal de la resolucion", readonly=False, default="RET_DEFINITIVA")
	tipo = fields.Selection([
		('FACE-63', 'Factura Electronica'),
		('NCE-64', 'Nota de Credito'),
		('NDE-65', 'Nota de Debito')],"Tipo", help="Tipo de documento", readonly=False, default='FACE-63')
	resoluciones_ids = fields.One2many('ir.sequence.resolution', 'sequence_id', string="Resoluciones")
	
IrSequence()


class IrSequenceResolution(models.Model):
	_name = "ir.sequence.resolution"
	_description = "Resoluciones de Factura"
	
	sequence_id = fields.Many2one('ir.sequence', 'Secuencia', required=True, ondelete='cascade')
	resolucion = fields.Char("Resolucion No.", readonly=False, required=True, size=100)
	serie = fields.Char("Serie", readonly=False, required=True)
	fecha_emision = fields.Date('Fecha Emision', readonly=False, required=True, select=True)
	fecha_vencimiento = fields.Date('Fecha Vencimiento', readonly=False, required=False, select=True)
	no_del = fields.Integer('Del', required=True, help='Inicio de la secuencia de las factuas')
	no_al = fields.Integer('Al', required=True, help='Fin de la secuencia de las facturas')
	state = fields.Selection([
			('draft', 'Borrador'),
			('uso', 'En Uso'),
			('terminado', 'Terminado'),
			('vencida', 'Vencida')],"Estado", readonly=True, required=False, default='draft')
	fiscal_position = fields.Selection([
			('PAGO_TRIMESTRAL', 'Sujeto a pagos trimestrales'),
			('RET_DEFINITIVA', 'Sujeto a retención definitiva'),
			('PAGO_CAJAS', 'Pago a Cajas')],"Posicion Fiscal", help="Posicion fiscal de la resolucion", readonly=False, default="RET_DEFINITIVA")
	tipo = fields.Selection([
		('FACE-63', 'Factura Electronica'),
		('NCE-64', 'Nota de Credito'),
		('NDE-65', 'Nota de Debito')],"Tipo", help="Tipo de documento", readonly=False, default='FACE-63')
	
	def action_asignar(self):
		sequence_obj = self.env['ir.sequence']
		res = {}
		for sequence in self:
			self.sequence_id.write({
				'resolucion': sequence.resolucion,
				'tipo': sequence.tipo,
				'fiscal_position': sequence.fiscal_position,
				'number_next_actual': sequence.no_del,
				'prefix': "%s-" %(sequence.serie),
				'number_increment': 1,
				'padding': 0,
				'implementation': 'no_gap',
				'user_date_range': False,
			})
			self.write({'state': 'uso',})
		return True
IrSequenceResolution()

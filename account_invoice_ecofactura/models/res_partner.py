# -*- coding: utf-8 -*-

from odoo import models, fields


class ExportacionCliente(models.Model):
    _inherit = 'res.partner'
    nombre_exportacion = fields.Char("Exportacion Nombre")
    direccion_exportacion = fields.Char("Dirección")
    codigo_exportacion = fields.Char("Código")
    referencia_exportacion = fields.Char("Otra referencia")
    incoterm_exportacion = fields.Char("INCOTERM - Lista de Edifcat.")
    exportador_exportacion = fields.Char("Nombre")
    codigo_exportador_exportacion = fields.Char("Exportador Código")

# -*- coding: utf-8 -*-

from odoo import fields, models


class SatdteFrases(models.Model):
    _name = 'satdte.frases'
    _description = 'Frases SAT DTE'

    name = fields.Char(string='Index')
    tipo_frase = fields.Char(string='Codigo Tipo Frase')  # Code Type Phrase
    nombre_frase = fields.Char(string='Nombre de Frase')  # Phrase Name
    descripcion_frase = fields.Text(string='Descripcion Frase')  # Description Phrase
    codigo_escenario = fields.Char(string='Codigo Escenario')  # Scenario Code
    escenario = fields.Char(string='Descripcion Escenario')  # Scenario description
    texto_colocar = fields.Char(string='Texto A Colocar')  # Text A Place


# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    factura_cambiaria = fields.Boolean('Factura Cambiaria')
    is_fel = fields.Boolean('¿Activar FEL?', required=False, default=False)
    no_cliente = fields.Char(string='Código Cliente',  help='Este código debe ser asignado por ecofactura')
    usuario_ecofactura = fields.Char(string='Usuario')
    password_ecofactura = fields.Char(string='Contraseña')
    nit_emisor = fields.Char(string='NIT EMISOR')
    codigo_est = fields.Char(string='Codigo Establecimiento',  # Establishment Code
                             help='Número del establecimiento donde se emite el documento. Es el que aparece asignado por SAT en sus registros.')
    url_webservice = fields.Char(string='URL webservice firma')
    url_webservice_anulacion = fields.Char(string='URL webservice anulación')

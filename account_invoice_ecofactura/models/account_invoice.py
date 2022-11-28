# -*- coding: utf-8 -*-

import random

import datetime
import uuid

from odoo import fields, models, api, _
from suds.client import Client
import xml.etree.ElementTree as ET
from odoo.exceptions import UserError, ValidationError
import base64
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    def _check_balanced(self):
        if self._context.get("force_reset_draft"):
            return
        return super(AccountInvoice,self)._check_balanced()

    uuid_fel = fields.Char(string='No. Factura', readonly=True, default=0, copy=False,
                            states={'draft': [('readonly', False)]}, help='UUID returned by certifier')  # No. Invoice
    fel_serie = fields.Char(string='Serie Fel', readonly=True, states={'draft': [('readonly', False)]}, copy=False,
                            help='Raw Serial number return by GFACE or FEL provider')  # Fel Series
    fel_no = fields.Char(string='Fel No.', readonly=True, states={'draft': [('readonly', False)]}, copy=False,
                        help='Raw Serial number return by GFACE or FEL provider')
    uuid = fields.Char(string='UUID', readonly=True, states={'draft': [('readonly', False)]}, copy=False,
                        help='UUID given to the certifier to register the document')
    no_acceso = fields.Char(string='Numero de Acceso', readonly=True, states={'draft': [('readonly', False)]},
                            copy=False, help='Electronic singnature given sent to FEL')  # Access Number
    frase_ids = fields.Many2many('satdte.frases', 'inv_frases_rel', 'inv_id', 'frases_id', 'Frases')
    frase_id = fields.Many2one('satdte.frases')
    factura_cambiaria = fields.Boolean('Factura Cambiaria', related='journal_id.factura_cambiaria', readonly=True)
    number_of_payments = fields.Integer('Cantidad De Abonos', default=1, copy=False, help='Number Of Payments')
    frecuencia_de_vencimiento = fields.Integer('Frecuencia De Vencimiento', copy=False, help='Due date frequency (calendar days)')
    megaprint_payment_lines = fields.One2many('megaprint.payment.line', 'invoice_id', 'Payment Info', copy=False)
    xml_request = fields.Text(string='XML Request', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    xml_response = fields.Text(string='XML Response', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    xml_notes = fields.Text('XML Children')
    uuid_refund = fields.Char('UUID a rectificar')
    txt_filename = fields.Char('File Archivo', required=False, readonly=True)
    file = fields.Binary('Archivo', required=False, readonly=True)
    fecha_emision = fields.Text('Fecha de Emision', required=False, readonly=True)
    fecha_certificacion = fields.Text('Fecha de Certificacion', required=False, readonly=True)
    numero_autorizacion = fields.Text('Numero de Autorizacion', required=False, readonly=True)
    serie = fields.Text('Serie', required=False, readonly=True)
    numero = fields.Text('Numero', required=False, readonly=True)
    razon_anulacion = fields.Text('Razon de anulacion')

    def init_fields(self):
        self.ExtendModel()

    def calculate_payment_info(self):
        for inv in self:
            if inv.journal_id.factura_cambiaria and inv.number_of_payments and inv.frecuencia_de_vencimiento and inv.invoice_date:
                inv.megaprint_payment_lines.unlink()  # Delete Old Payment Lines
                amount = inv.amount_total / inv.number_of_payments
                new_date = None
                for i in range(inv.number_of_payments):
                    if not new_date:
                        new_date = datetime.datetime.strptime(str(inv.invoice_date), '%Y-%m-%d').date() + datetime.timedelta(days=inv.frecuencia_de_vencimiento)
                    else:
                        new_date = new_date + datetime.timedelta(days=inv.frecuencia_de_vencimiento)
                    self.env['megaprint.payment.line'].create({
                        'invoice_id': inv.id,
                        'serial_no': i + 1,
                        'amount': amount,
                        'due_date': new_date.strftime('%Y-%m-%d')
                    })
    def set_response_data(self):
        dte_atributos = ET.fromstring(self.xml_response).attrib
        _logger.info("====dte_atributos====%r",dte_atributos)
        self.fecha_emision = dte_atributos.get('FechaEmision')
        self.fecha_certificacion = dte_atributos.get('FechaCertificacion')
        self.numero_autorizacion = dte_atributos.get('NumeroAutorizacion')
        self.serie = dte_atributos.get('Serie')
        self.numero = dte_atributos.get('Numero')

    def set_pdf(self):
        response_xml = ET.fromstring(self.xml_response)
        for child in response_xml:
            if child.tag == 'Pdf':
                self.file = base64.encodestring(base64.standard_b64decode(child.text))
                self._create_attachment()
                
    def _create_attachment(self):
        self.ensure_one()
        attachment = {
            'name': str(self.name)+'.pdf',
            'datas': self.file,
            'store_fname': self.name+'.pdf',
            'type': 'binary',
            'res_id':self.id,
            'res_model': self._name
         }
        attach = self.env['ir.attachment'].create(attachment)
        return attach
                
    def message_post_with_template(self, template_id, email_layout_xmlid=None, auto_commit=False, **kwargs):
        template = self.env['mail.template'].browse(template_id)
        attachment_id_list = []
        if self.journal_id.is_fel:
            attachment = self.attachment_ids.filtered(lambda c: c.name == str(self.name)+'.pdf' )
            if not attachment:
               attachment = self._create_attachment()
            attachment_id_list.append(attachment.id)
            self = self.with_context(default_attachment_ids= attachment.ids)
        template.write({'attachment_ids':attachment_id_list})
        return super(AccountInvoice, self).message_post_with_template(template_id=template_id, email_layout_xmlid=email_layout_xmlid, auto_commit=auto_commit, **kwargs)


    # 
    def action_invoice_sent(self):
        self.ensure_one()
        attachment_id_list = []
        if self.journal_id.is_fel:
            attachment = self.attachment_ids.filtered(lambda c: c.name == str(self.name)+'.pdf' )
            if not attachment:
               attachment = self._create_attachment()
            attachment_id_list.append(attachment.id)
        template = self.env.ref('account.email_template_edi_invoice', False)
        compose_form = self.env.ref('account.account_invoice_send_wizard_form', False)
        lang = self.env.context.get('lang')
        if template and template.lang:
            lang = template._render_template(template.lang, 'account.move', [self.id])
        self = self.with_context(lang=lang)
        TYPES = {
            'out_invoice': _('Invoice'),
            'in_invoice': _('Vendor Bill'),
            'out_refund': _('Credit Note'),
            'in_refund': _('Vendor Credit note'),
        }
        template.write({'attachment_ids':attachment_id_list})

        ctx = dict(
            default_model='account.move',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_attachment_ids = attachment_id_list,
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            model_description=TYPES[self.move_type],
            custom_layout="mail.mail_notification_paynow",
            force_email=True
        )
        return {
            'name': _('Send Invoice'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.send',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def validar_errores_en_response(self):
        errores = ""
        response_xml = ET.fromstring(self.xml_response)
        for child in response_xml:
            if child.tag == 'Error':
                if not child.attrib['Codigo'] == '2001':
                    errores += child.text + "\n"
        return errores


    def generate_xml(self):

        uuid_txt = uuid.uuid4()
        self.uuid = uuid_txt
        if self.journal_id.is_fel:
            res_xml = self.GenerateXML_FACT()
            self.xml_request = res_xml
            ws = Client(self.journal_id.url_webservice)
            response = ws.service.Execute(
                self.journal_id.no_cliente,
                self.journal_id.usuario_ecofactura,
                self.journal_id.password_ecofactura,
                self.journal_id.nit_emisor, res_xml
            )

            self.xml_response = response
            errores = self.validar_errores_en_response()
            _logger.info("===Error====%r",errores)

            if not len(errores) > 1:
                self.set_pdf()
                self.set_response_data()
            else:
                if self._context.get('website_force_confirm'):
                    _logger.info("===Error====%r",errores)
                    return 
                raise UserError(('%s') % (errores))

    def _post(self, soft=True):
        res = super(AccountInvoice, self)._post(soft=soft)
        for obj in self:
            if obj.move_type in ('out_invoice', 'out_refund') and obj.journal_id.is_fel == True:
                obj.generate_xml()
        return res

    def button_cancel(self):
        if self.razon_anulacion and self.journal_id.is_fel:
            res = super(AccountInvoice, self).button_cancel()
            for obj in self:
                self.cancel_fel_document()
            return res
        elif not self.journal_id.is_fel:
            res = super(AccountInvoice, self).button_cancel()
            return  res
        else:
            raise UserError(('%s') % ('No existe una razon de anulación'))


    def cancel_fel_document(self):
        ws = Client(self.journal_id.url_webservice_anulacion)
        response = ws.service.Execute(
            self.journal_id.no_cliente,
            self.journal_id.usuario_ecofactura,
            self.journal_id.password_ecofactura,
            self.journal_id.nit_emisor,
            self.numero_autorizacion,
            self.razon_anulacion
        )
        self.xml_response = response
        errores = self.validar_errores_en_response()

        if not len(errores) > 1:
            self.set_pdf()
        else:
            raise UserError(('%s') % (errores))


class MegaprintPaymentLine(models.Model):
    _name = 'megaprint.payment.line'
    _description = 'Megaprint Payment Line'
    _order = 'serial_no'

    invoice_id = fields.Many2one('account.move', 'Inovice')
    serial_no = fields.Integer('#No', readonly=True)
    amount = fields.Float('Monto', readonly=True, help='Amount')
    due_date = fields.Date('Vencimiento', readonly=True, help='Due Date')
    
class AccountMoveLine(models.Model):
    
    _inherit = "account.move.line"
    
    def get_account_id(self):
        for obj in self:
            account_id = obj._get_computed_account().id
            taxes = obj._get_computed_taxes()
            if taxes and obj.move_id.fiscal_position_id:
                taxes = obj.move_id.fiscal_position_id.map_tax(taxes, partner=obj.partner_id)
            price = obj.price_unit
            _logger.info("====taxes=%r",taxes)
            if obj.move_id.move_type == 'out_invoice':
                self.env.cr.execute('update account_move_line set display_type=%s, account_id=%s, price_unit=%s,credit=%s where id=%s', (False, account_id, price,obj.price_total,obj.id))
            if obj.move_id.move_type == 'in_invoice':
                self.env.cr.execute('update account_move_line set display_type=%s, account_id=%s, price_unit=%s,debit=%s where id=%s', (False, account_id, price,obj.price_total,obj.id))
            obj.tax_ids = taxes.ids
            obj.move_id._recompute_dynamic_lines()
        return True

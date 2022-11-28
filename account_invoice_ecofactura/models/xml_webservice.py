# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement

from odoo import models
import re


class AccountInvoice(models.Model):
    _inherit = "account.move"


    def GenerateXML_FACT(self):
        fe = Element('stdTWS')
        fe.set('xmlns', 'FEL')

        TrnEstNum = SubElement(fe, 'TrnEstNum')
        if not self.journal_id.codigo_est:
            TrnEstNum.text = str(1)
        else:
            TrnEstNum.text = str(self.journal_id.codigo_est)


        TipTrnCod = SubElement(fe, 'TipTrnCod')
        if self.move_type == 'out_refund':
            TipTrnCod.text = str('NCRE')
        elif self.journal_id.factura_cambiaria:
            TipTrnCod.text = str('FCAM')
        else:
            TipTrnCod.text = str('FACT')

        TrnNum = SubElement(fe, 'TrnNum')
        TrnNum.text = str(self.sequence_number)

        TrnFec = SubElement(fe, 'TrnFec')
        TrnFec.text = str(self.invoice_date) or str(fields.date.now())

        MonCod = SubElement(fe, 'MonCod')
        MonCod.text = str(self.currency_id.name)

        TrnBenConNIT = SubElement(fe, 'TrnBenConNIT')
        if not self.partner_id.vat or self.frase_id.codigo_escenario == '1':
            TrnBenConNIT.text = str("CF")
        else:
            nit = self.partner_id.vat.replace('-', '')
            
            TrnBenConNIT.text = str(nit.upper())

        TrnExp = SubElement(fe, 'TrnExp')
        if self.frase_id.codigo_escenario == '1':
            TrnExp.text = str("1")
        else:
            TrnExp.text = str("0")

        if self.frase_id and not self.frase_id.codigo_escenario == '1':
            data = {
                'TrnExento': str("1"),
                'TrnFraseTipo': str("4"),
                'TrnEscCod': str(self.frase_id.codigo_escenario)
            }
        else:
            data = {
                'TrnExento': str("0"),
                'TrnFraseTipo': str("0"),
                'TrnEscCod': str("0")
            }

        TrnExento = SubElement(fe, 'TrnExento')
        TrnExento.text = data['TrnExento']

        TrnFraseTipo = SubElement(fe, 'TrnFraseTipo')
        TrnFraseTipo.text = data['TrnFraseTipo']

        TrnEscCod = SubElement(fe, 'TrnEscCod')
        TrnEscCod.text = data['TrnEscCod']

        if self.frase_id.codigo_escenario == '1':
            SubElement(fe, "TrnEFACECliCod").text = self.partner_id.vat
            SubElement(fe, "TrnEFACECliNom").text = self.partner_id.name
            SubElement(fe, "TrnEFACECliDir").text = self.partner_id.street
        elif not self.partner_id.vat:  # ( not NIT)
            SubElement(fe, "TrnEFACECliCod").text = "CF"
            SubElement(fe, "TrnEFACECliNom").text = self.partner_id.name
            SubElement(fe, "TrnEFACECliDir").text = self.partner_id.street or "Ciudad"
        else:
            SubElement(fe, "TrnEFACECliCod").text = ""
            SubElement(fe, "TrnEFACECliNom").text = self.partner_id.name or ""
            SubElement(fe, "TrnEFACECliDir").text = self.partner_id.street or "Ciudad"

        TrnObs = SubElement(fe, 'TrnObs')
        TrnObs.text = self.name or ""

        TrnEmail = SubElement(fe, 'TrnEmail')
        TrnEmail.text = self.partner_id.email

        TrnCampAd01 = SubElement(fe, 'TrnCampAd01').text = ""
        TrnCampAd02 = SubElement(fe, 'TrnCampAd02').text = ""
        TrnCampAd03 = SubElement(fe, 'TrnCampAd03').text = ""
        TrnCampAd04 = SubElement(fe, 'TrnCampAd04').text = ""
        TrnCampAd05 = SubElement(fe, 'TrnCampAd05').text = ""
        TrnCampAd06 = SubElement(fe, 'TrnCampAd06').text = ""
        TrnCampAd07 = SubElement(fe, 'TrnCampAd07').text = ""
        TrnCampAd08 = SubElement(fe, 'TrnCampAd08').text = ""
        TrnCampAd09 = SubElement(fe, 'TrnCampAd09').text = ""
        TrnCampAd10 = SubElement(fe, 'TrnCampAd10').text = ""
        TrnCampAd11 = SubElement(fe, 'TrnCampAd11').text = ""
        TrnCampAd12 = SubElement(fe, 'TrnCampAd12').text = ""
        TrnCampAd13 = SubElement(fe, 'TrnCampAd13').text = ""
        TrnCampAd14 = SubElement(fe, 'TrnCampAd14').text = ""
        TrnCampAd15 = SubElement(fe, 'TrnCampAd15').text = ""
        TrnCampAd16 = SubElement(fe, 'TrnCampAd16').text = ""
        TrnCampAd17 = SubElement(fe, 'TrnCampAd17').text = ""
        TrnCampAd18 = SubElement(fe, 'TrnCampAd18').text = ""
        TrnCampAd19 = SubElement(fe, 'TrnCampAd19').text = ""
        TrnCampAd20 = SubElement(fe, 'TrnCampAd20').text = ""
        TrnCampAd21 = SubElement(fe, 'TrnCampAd21').text = ""
        TrnCampAd22 = SubElement(fe, 'TrnCampAd22').text = ""
        TrnCampAd23 = SubElement(fe, 'TrnCampAd23').text = ""
        TrnCampAd24 = SubElement(fe, 'TrnCampAd24').text = ""
        TrnCampAd25 = SubElement(fe, 'TrnCampAd25').text = ""
        TrnCampAd26 = SubElement(fe, 'TrnCampAd26').text = ""
        TrnCampAd27 = SubElement(fe, 'TrnCampAd27').text = ""
        TrnCampAd28 = SubElement(fe, 'TrnCampAd28').text = ""
        TrnCampAd29 = SubElement(fe, 'TrnCampAd29').text = ""
        TrnCampAd30 = SubElement(fe, 'TrnCampAd30').text = ""

        invoice_line = self.invoice_line_ids
        line_doc = SubElement(fe, "stdTWSD")
        cnt = 0
        for line in invoice_line:
            if not line.product_id:
                continue
            cnt += 1
            p_type = "B"
            desc = 0
            if line.product_id.type == 'service':
                p_type = "S"
            if line.discount > 0:
                desc = ((line.quantity * line.price_unit) * line.discount) / 100.00
            # for tax in line.invoice_line_tax_ids:
            #     if tax.price_include:
            #         tax_in_ex = 0
            # product tag -- <stdTWS.stdTWSCIt.stdTWSDIt>
            product_doc = SubElement(line_doc, "stdTWS.stdTWSCIt.stdTWSDIt")
            SubElement(product_doc, "TrnLiNum").text = str(cnt)
            SubElement(product_doc, "TrnArtCod").text = line.product_id.default_code or "0"
            SubElement(product_doc, "TrnArtNom").text = line.name or " "
            SubElement(product_doc, "TrnCan").text = str(line.quantity)
            SubElement(product_doc, "TrnVUn").text = str(round( line.price_unit, 2))
            SubElement(product_doc, "TrnUniMed").text = line.product_id.uom_name or " "
            SubElement(product_doc, "TrnVDes").text = str( round( desc,2 ) ) or "0"
            SubElement(product_doc, "TrnArtBienSer").text = str(p_type)
            SubElement(product_doc, "TrnArtImpAdiCod").text = "0"
            SubElement(product_doc, "TrnArtImpAdiUniGrav").text = "0"
            SubElement(product_doc, "TrnDetCampAdi01").text = ""
            SubElement(product_doc, "TrnDetCampAdi02").text = ""
            SubElement(product_doc, "TrnDetCampAdi03").text = ""
            SubElement(product_doc, "TrnDetCampAdi04").text = ""
            SubElement(product_doc, "TrnDetCampAdi05").text = ""

        if self.journal_id.factura_cambiaria:
            linea_camb = SubElement(fe, "stdTWSCam")
            for line in self.megaprint_payment_lines:
                linea_camb_subelemento = SubElement(linea_camb, "stdTWS.stdTWSCam.stdTWSCamIt")
                SubElement(linea_camb_subelemento, "TrnAbonoNum").text = str(line.serial_no)
                SubElement(linea_camb_subelemento, "TrnAbonoFecVen").text = str(line.due_date)
                SubElement(linea_camb_subelemento, "TrnAbonoMonto").text = str(line.amount)

        if self.frase_id.codigo_escenario == '1':
            exportacion = SubElement(fe, "stdTWSExp")
            exportacion_sub = SubElement(exportacion, "stdTWS.stdTWSExp.stdTWSExpIt")
            SubElement(exportacion_sub, "NomConsigODest").text = str(self.partner_id.nombre_exportacion)
            SubElement(exportacion_sub, "DirConsigODest").text = str(self.partner_id.direccion_exportacion)
            SubElement(exportacion_sub, "CodConsigODest").text = str(self.partner_id.codigo_exportacion)
            SubElement(exportacion_sub, "OtraRef").text = str(self.partner_id.referencia_exportacion)
            SubElement(exportacion_sub, "INCOTERM").text = str(self.partner_id.incoterm_exportacion)
            SubElement(exportacion_sub, "ExpNom").text = str(self.partner_id.exportador_exportacion)
            SubElement(exportacion_sub, "ExpCod").text = str(self.partner_id.codigo_exportador_exportacion)

        if self.move_type == 'out_refund':
            parent_invoice = self.reversed_entry_id
            nota_credito = SubElement(fe, "stdTWSNota")
            nota_credito_sub = SubElement(nota_credito, "stdTWS.stdTWSNota.stdTWSNotaIt")
            SubElement(nota_credito_sub, "TDFEPRegimenAntiguo").text = str(0)
            SubElement(nota_credito_sub, "TDFEPAutorizacion").text = str(parent_invoice.numero_autorizacion)
            SubElement(nota_credito_sub, "TDFEPSerie").text = str(parent_invoice.serie)
            SubElement(nota_credito_sub, "TDFEPNumero").text = str(parent_invoice.numero)
            SubElement(nota_credito_sub, "TDFEPFecEmision").text = str(parent_invoice.invoice_date)
            

        
        final_data = ET.tostring(fe, encoding='UTF-8', method='xml')
        declare_str = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        f_str = "%s %s" % (declare_str, final_data.decode("utf-8"))
        return f_str


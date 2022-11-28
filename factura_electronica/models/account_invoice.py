# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from suds.client import Client
from odoo.addons.factura_electronica.models.numero_a_texto import Numero_a_Texto
#from odoo.addons.factura_electronica.models.ws import ws_eface
from suds.client import Client
#from suds.xsd.doctor import Import, ImportDoctor
import xml.etree.cElementTree as ET
from lxml import etree
import glob
import os
import base64
#import sys
#reload(sys)  
#sys.setdefaultencoding('utf8')

#Variables del XML
xmlns = "http://www.fact.com.mx/schema/gt"
xsi = "http://www.w3.org/2001/XMLSchema-instance"
schemaLocation = "http://www.fact.com.mx/schema/gt http://www.mysuitemex.com/fact/schema/fx_2013_gt_3.xsd"
version = "1.1"
ns = "{xsi}"


class AccountMove(models.Model):
	_inherit = "account.move"
	
	consumido_eface = fields.Boolean('Consumido', required=False, readonly=True, help="Parametro para indentificar el consumo en el WS")
	id_sat = fields.Char("Id SAT", readonly=True, required=False, help="Identificador asignado en el consumo de la factura en el WS")
	id_serie_sat = fields.Char("Id Serie SAT", readonly=True, required=False, help="Identificador de la serie de la factura electronica")
	cae = fields.Text("CAE", readonly=True, required=False, help="Firma electronica")
	serie = fields.Char("Serie", readonly=True, required=False, help="Serie del documento")
	no_documento = fields.Char("No Documento", readonly=True, required=False, help="Numero del documento")
	txt_filename = fields.Char('File Archivo', required=False, readonly=True)
	file = fields.Binary('Archivo', required=False, readonly=True)
	notas = fields.Text("Notas", readonly=False, required=False, help="Notas")
	
	def action_post(self):
		# Cambiada para procesar los datos devueltos por WS
		res = super(AccountMove, self).action_post()
		self.action_eface()
		return res
	
	def action_eface(self):
		xml = ""
		for invoice in self:
			if (invoice.journal_id.is_eface == True) and (invoice.journal_id.type == 'sale'):
				try:
					RetPDF = 1
					pdf_file = False
					url = invoice.journal_id.sequence_id.url_ws
					codcliente = invoice.journal_id.sequence_id.cod_cliente
					codusuario = invoice.journal_id.sequence_id.user_eface
					nitemisor = invoice.journal_id.sequence_id.llave_eface
					resoluciono = invoice.journal_id.sequence_id.resolucion
					establecimiento = invoice.journal_id.sequence_id.establecimiento
					doc = invoice.journal_id.sequence_id.tipo
					xml = self.create_xml()
					ws = Client(url)
					response = ws.service.Execute(codcliente, codusuario, nitemisor, establecimiento, resoluciono, xml, RetPDF)
					if response:
						if response.Respuesta:
							tree_res = ET.fromstring(response.Respuesta)
							resulta_codigo = tree_res.find('ERROR').attrib['Codigo']
							resulta_descripcion = tree_res.find('ERROR').text
							if not (resulta_codigo=="0"):
								raise UserError(_("No se Puede validad la Factura Electronica\n Error Code:%s\n %s."% (resulta_codigo,resulta_descripcion)))
							if response.Dte:
								tree_dte = ET.fromstring(response.Dte)
								mitree = tree_dte.attrib
								NoDocto = mitree['NoDocto']
								NombreDTE = mitree['NombreDTE']
								Fecha =mitree['Fecha']
								uno = response.Dte
								ab = uno.find('Archivo="')
								bc = uno.find('"/>')
								ab = ab+9
								tres= uno[ab:bc]
								res = base64.standard_b64decode(tres)
								res = res.decode(encoding='utf-8', errors='strict')
								ini = res.find("<ds:SignatureValue>")
								fin = res.find("</ds:SignatureValue>")
								ini = ini+19
								Cae = res[ini:fin]
								for child in tree_dte:
									if child.attrib['Tipo'] == 'PDF':
										pdf_file = child.attrib['Archivo']
								self.write({
									'cae': Cae,
									'consumido_eface': True,
									'serie': NombreDTE,
									'no_documento': NoDocto,
									'txt_filename': '%s.pdf' %(NombreDTE),
									'file': base64.encodestring(base64.standard_b64decode(pdf_file)),
								})
						else:
							raise UserError(('%s')%(res.Respuesta))
				except Exception as e:
					raise UserError(('Error al genera Factura Electronica: %s')%(e))

	def create_xml(self):
		serie, numero = str(self.number).split('-')
		lote = 0
		root = ET.Element("stdTWS", xmlns="GFACE_Web")
		doc = ET.SubElement(root, "stdTWS.stdTWSCIt")
		ET.SubElement(doc, "TipTrnCod").text = self.journal_id.sequence_id.tipo
		ET.SubElement(doc, "TrnNum").text = numero
		ET.SubElement(doc, "TrnFec").text = str(self.date_invoice) or str(fields.date.now())
		ET.SubElement(doc, "TrnBenConNIT").text = self.partner_id.vat
		if self.partner_id.country_id.id != self.company_id.country_id.id:
			ET.SubElement(doc, "TrnEFACECliCod").text = "EXPO"
			ET.SubElement(doc, "TrnEFACECliNom").text = self.partner_id.name
			ET.SubElement(doc, "TrnEFACECliDir").text = self.partner_id.street
		elif not self.partner_id.vat:  # ( not NIT)
			ET.SubElement(doc, "TrnEFACECliCod").text = "CF"
			ET.SubElement(doc, "TrnEFACECliNom").text = self.partner_id.name
			ET.SubElement(doc, "TrnEFACECliDir").text = "Ciudad"
		else:
			ET.SubElement(doc, "TrnEFACECliCod").text = ""
			ET.SubElement(doc, "TrnEFACECliNom").text = ""
			ET.SubElement(doc, "TrnEFACECliDir").text = ""
		ET.SubElement(doc, "TrnObs").text = self.name or ""
		ET.SubElement(doc, "TrnEMail").text = self.partner_id.email
		#Nota de credito
		if self.move_type == 'out_refund':
			inv_num = self.refund_invoice_id.number.split('-')
			ET.SubElement(doc, "TDFEPAutResNum").text = str(self.refund_invoice_id.journal_id.sequence_id.resolucion)
			ET.SubElement(doc, "TDFEPTipTrnCod").text = str(self.refund_invoice_id.journal_id.sequence_id.tipo)
			ET.SubElement(doc, "TDFEPSerie").text = str(inv_num[0])
			ET.SubElement(doc, "TDFEPDispElec").text = str(self.refund_invoice_id.journal_id.sequence_id.dispositivo)
			ET.SubElement(doc, "TDFEPYear").text = str(self.refund_invoice_id.date_invoice.year)
			ET.SubElement(doc, "TDFEPNum").text = str(self.refund_invoice_id.no_documento)
		else:
			ET.SubElement(doc, "TDFEPAutResNum").text = ""		
			ET.SubElement(doc, "TDFEPTipTrnCod").text = ""
			ET.SubElement(doc, "TDFEPSerie").text = ""
			ET.SubElement(doc, "TDFEPDispElec").text = ""
			ET.SubElement(doc, "TDFEPYear").text = "0"
			ET.SubElement(doc, "TDFEPNum").text = "0"
		#Fin Nota de credito
		ET.SubElement(doc, "MonCod").text = self.currency_id.name
		ET.SubElement(doc, "TrnTasCam").text = "1"
		ET.SubElement(doc, "TrnCampAd01").text = ""
		ET.SubElement(doc, "TrnCampAd02").text = ""
		ET.SubElement(doc, "TrnCampAd03").text = ""
		ET.SubElement(doc, "TrnCampAd04").text = ""
		ET.SubElement(doc, "TrnCampAd05").text = ""
		ET.SubElement(doc, "TrnCampAd06").text = ""
		ET.SubElement(doc, "TrnCampAd07").text = ""
		ET.SubElement(doc, "TrnCampAd08").text = ""
		ET.SubElement(doc, "TrnCampAd09").text = ""
		ET.SubElement(doc, "TrnCampAd10").text = ""
		ET.SubElement(doc, "TrnCampAd11").text = ""
		ET.SubElement(doc, "TrnCampAd12").text = ""
		ET.SubElement(doc, "TrnCampAd13").text = ""
		ET.SubElement(doc, "TrnCampAd14").text = ""
		ET.SubElement(doc, "TrnCampAd15").text = ""
		ET.SubElement(doc, "TrnCampAd16").text = ""
		ET.SubElement(doc, "TrnCampAd17").text = ""
		ET.SubElement(doc, "TrnCampAd18").text = ""
		ET.SubElement(doc, "TrnCampAd19").text = ""
		ET.SubElement(doc, "TrnCampAd20").text = ""
		ET.SubElement(doc, "TrnCampAd21").text = ""
		ET.SubElement(doc, "TrnCampAd22").text = ""
		ET.SubElement(doc, "TrnCampAd23").text = ""
		ET.SubElement(doc, "TrnCampAd24").text = ""
		ET.SubElement(doc, "TrnCampAd25").text = ""
		ET.SubElement(doc, "TrnCampAd26").text = ""
		ET.SubElement(doc, "TrnCampAd27").text = ""
		ET.SubElement(doc, "TrnCampAd28").text = ""
		ET.SubElement(doc, "TrnCampAd29").text = ""
		ET.SubElement(doc, "TrnCampAd30").text = ""
		ET.SubElement(doc, "TrnPaisCod").text = self.partner_id.country_id.name and self.partner_id.country_id.name.upper() or ''
		invoice_line = self.invoice_line_ids
		ET.SubElement(doc, "TrnUltLinD").text = str(len(invoice_line.ids))
		line_doc = ET.SubElement(doc, "stdTWSD")
		print (">>>>>>>>", len(invoice_line.ids))
		tax_in_ex = 1
		cnt = 0
		for line in invoice_line:
			cnt += 1
			p_type = 0
			desc=0
			if line.product_id.type == 'service':
				p_type = 1
			if line.discount > 0:
				desc= ((line.quantity * line.price_unit) * line.discount) / 100.00
			for tax in line.invoice_line_tax_ids:
				if tax.price_include:
					tax_in_ex = 0
			# product tag -- <stdTWS.stdTWSCIt.stdTWSDIt>
			product_doc = ET.SubElement(line_doc, "stdTWS.stdTWSCIt.stdTWSDIt")
			ET.SubElement(product_doc, "TrnLiNum").text = str(cnt)
			ET.SubElement(product_doc, "TrnArtCod").text = line.product_id.default_code or "0"
			ET.SubElement(product_doc, "TrnArtNom").text = line.name or " "
			ET.SubElement(product_doc, "TrnCan").text = str(line.quantity)
			ET.SubElement(product_doc, "TrnVUn").text = str(line.price_unit)
			ET.SubElement(product_doc, "TrnUniMed").text = line.uom_id.name or " "
			ET.SubElement(product_doc, "TrnVDes").text = str(desc) or "0"
			ET.SubElement(product_doc, "TrnArtBienSer").text = str(p_type)
			ET.SubElement(product_doc, "TrnArtExcento").text = str(tax_in_ex)
			ET.SubElement(product_doc, "TrnDetCampAd01").text = ""
			ET.SubElement(product_doc, "TrnDetCampAd02").text = ""
			ET.SubElement(product_doc, "TrnDetCampAd03").text = ""
			ET.SubElement(product_doc, "TrnDetCampAd04").text = ""
			ET.SubElement(product_doc, "TrnDetCampAd05").text = ""
		tax_doc = ET.SubElement(doc, "stdTWSIA")
		final_data = ET.tostring(root,encoding='UTF-8',  method='xml')
		declare_str = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
		f_str = "%s %s" % (declare_str, final_data.decode("utf-8"))
		# print (f_str)
		return f_str

	def create_xml_old(self, invoice):
		xml_string = ""
		lista = []
		taxes = {}
		taxes_total = {}
		taxes_lista = []
		ldescuentos = {}
		descuentos = []
		total_neto_SDR = 0.00
		precio_neto = 0.00
		subtotal_neto = 0.00
		#total_neto_SDR = 0.00
		total_impuestos = 0.00
		subtotal_descuento = 0.00
		total_descuento = 0.00
		price = 0.00
		tasa_iva = 12.00
		total_siniva = 0.00
		#try:
		for line in invoice:
			factura = ET.Element("{" + xmlns + "}FactDocGT", nsmap={'xsi': xsi, None: xmlns}, attrib={"{" + xsi + "}schemaLocation" : schemaLocation})
			version = ET.SubElement(factura, 'Version')
			procesamiento = ET.SubElement(factura, 'Procesamiento')
			emcabezado = ET.SubElement(factura, 'Encabezado')
			vendedor = ET.SubElement(factura, 'Vendedor')
			comprador = ET.SubElement(factura, 'Comprador')
			detalles = ET.SubElement(factura, 'Detalles')
			#asignacion de Valores al los tags del XML
			version.text = str(3)
			#Asignacion de envio por correo
			dictionary = ET.SubElement(procesamiento, 'Dictionary', name='email')
			ET.SubElement(dictionary, 'Entry', k='from', v='servicios@efactura.com.gt')
			if line.partner_id.email:
				ET.SubElement(dictionary, 'Entry', k='to', v=line.partner_id.email)
				ET.SubElement(dictionary, 'Entry', k='cc', v=line.company_id.email)
			else:
				ET.SubElement(dictionary, 'Entry', k='to', v=line.company_id.email)
				ET.SubElement(dictionary, 'Entry', k='cc', v=line.company_id.email)
			ET.SubElement(dictionary, 'Entry', k='formats', v='xml pdf')
			#Fin Envio de Correos
			tipo_activo = ET.SubElement(emcabezado, 'TipoActivo')
			tipo_activo.text = str(line.journal_id.sequence_id.tipo)
			moneda = ET.SubElement(emcabezado, 'CodigoDeMoneda')
			moneda.text = str(line.currency_id.name)
			cambio = ET.SubElement(emcabezado, 'TipoDeCambio')
			rate = float(line.currency_id.rate)
			cambio.text = str((1.00/rate))
			regimen = ET.SubElement(emcabezado, 'InformacionDeRegimenIsr')
			regimen.text = str(line.journal_id.sequence_id.fiscal_position)
			#Vendedor
			nit_eface = ET.SubElement(vendedor, 'Nit')
			nit_eface.text = str(line.company_id.vat)
			idioma = ET.SubElement(vendedor, 'Idioma')
			idioma.text = "es"
			establecimiento = ET.SubElement(vendedor, 'CodigoDeEstablecimiento')
			establecimiento.text = str(line.journal_id.sequence_id.establecimiento)
			dispositivo = ET.SubElement(vendedor, 'DispositivoElectronico')
			dispositivo.text = str(line.journal_id.sequence_id.dispositivo)
			#Comprador
			nit_comprador = ET.SubElement(comprador, 'Nit')
			nit_comprador.text = (line.partner_id.vat or "CF")
			nombre_comprador = ET.SubElement(comprador, 'NombreComercial')
			nombre_comprador.text = (line.partner_id.name.encode('ascii', 'ignore') or "")
			direccion_comercial = ET.SubElement(comprador, 'DireccionComercial')
			direccion1 = ET.SubElement(direccion_comercial, 'Direccion1')
			direccion1.text = (line.partner_id.street or ".")
			municipio = ET.SubElement(direccion_comercial, 'Municipio')
			municipio.text = (line.partner_id.street2 or ".")
			departamento = ET.SubElement(direccion_comercial, 'Departamento')
			departamento.text = (line.partner_id.city or ".")
			pais_code = ET.SubElement(direccion_comercial, 'CodigoDePais')
			pais_code.text = (line.partner_id.country_id.code or "GT")
			idioma_comprador = ET.SubElement(comprador, 'Idioma')
			idioma_comprador.text = "es"
			#Detalles de la Factura
			for d in line.invoice_line_ids:
				precio_neto = 0.00
				subtotal_neto = 0.00
				#total_neto_SDR = 0.00
				total_impuestos = 0.00
				subtotal_descuento = 0.00
				#total_descuento = 0.00
				price = 0.00
				cat = ""
				detalle = ET.SubElement(detalles, 'Detalle')
				cadena = d.name.split('\n')
				if len(cadena) > 1:
					descripcion = ET.SubElement(detalle, 'Descripcion')
					descripcion.text = cadena[0]
				else:
					descripcion = ET.SubElement(detalle, 'Descripcion')
					descripcion.text = d.name.decode('utf-8')
				ean = ET.SubElement(detalle, 'CodigoEAN')
				ean.text = (d.product_id.barcode or "00000000000000")
				uom = ET.SubElement(detalle, 'UnidadDeMedida')
				uom.text = ("UNI")
				qty = ET.SubElement(detalle, 'Cantidad')
				qty.text = str(round(d.quantity, 4))
				taxes = d.invoice_line_tax_ids.compute_all(d.price_unit, line.currency_id, d.quantity, d.product_id, line.partner_id)
				precioDR = ((d.price_unit) - ((d.price_unit * d.discount) / 100))
				descuento = (((d.price_unit * d.discount) / 100))
				priceDR = d.invoice_line_tax_ids.compute_all(precioDR, line.currency_id, d.quantity, d.product_id, line.partner_id)
				if not d.invoice_line_tax_ids:
					#taxes = d.invoice_line_tax_ids.compute_all(d.price_unit, line.currency_id, d.quantity, d.product_id, line.partner_id)
					price = round(d.price_unit, 4)
					precioDR = round(precioDR, 4)
					subtotal_descuento = round(((d.quantity * descuento)), 4)
				else:
					preciocompute = d.invoice_line_tax_ids.compute_all(d.price_unit, line.currency_id, 1.00, d.product_id, line.partner_id)
					price = round(preciocompute['total_excluded'], 4)
					preciocomputeDR = d.invoice_line_tax_ids.compute_all(precioDR, line.currency_id, 1.00, d.product_id, line.partner_id)
					precioDR = round(preciocomputeDR['total_excluded'], 4)
					subtotal_descuento = round(((d.quantity * descuento) / 1.12), 4)
					#print (taxes)
				subtotal_neto = taxes['total_excluded']
				total_neto_SDR += subtotal_neto
				subtotal_neto_DR = priceDR['total_excluded']
				valorsindr = ET.SubElement(detalle, 'ValorSinDR')
				precio = ET.SubElement(valorsindr, 'Precio')
				precio.text = str(round(price, 4))
				monto = ET.SubElement(valorsindr, 'Monto')
				monto.text = str(round((subtotal_neto), 4))
				drs = ET.SubElement(detalle, 'DescuentosYRecargos')
				sumdrs = ET.SubElement(drs, 'SumaDeDescuentos')
				#subtotal_descuento = round(((d.quantity * descuento) / 1.12), 4)
				total_descuento += subtotal_descuento
				sumdrs.text = str(round((subtotal_descuento), 4))
				dr = ET.SubElement(drs, 'DescuentoORecargo')
				op = ET.SubElement(dr, 'Operacion')
				op.text = str('DESCUENTO')
				srv = ET.SubElement(dr, 'Servicio')
				srv.text = str('ALLOWANCE_GLOBAL')
				dbase = ET.SubElement(dr, 'Base')
				dbase.text = str(round(price, 4))
				dtasa = ET.SubElement(dr, 'Tasa')
				dtasa.text = str(round(d.discount, 4))
				dmonto = ET.SubElement(dr, 'Monto')
				dmonto.text = str(round(subtotal_descuento, 4))
				ldescuentos = {
					'operacion': 'DESCUENTO',
					'servicio': 'ALLOWANCE_GLOBAL',
					'base': price, 
					'tasa': d.discount,
					'monto': (subtotal_descuento),
				}
				descuentos.append(ldescuentos)
				valorcondr = ET.SubElement(detalle, 'ValorConDR')
				precio2 = ET.SubElement(valorcondr, 'Precio')
				precio2.text = str(round(precioDR, 4))
				monto2 = ET.SubElement(valorcondr, 'Monto')
				monto2.text = str(round((subtotal_neto_DR), 4))
				#Detalle de Impuestos
				impuestos = ET.SubElement(detalle, 'Impuestos')
				total_impu = ET.SubElement(impuestos, 'TotalDeImpuestos')
				total_impuestos = sum([x['amount'] for x in priceDR['taxes']])
				total_impu.text = str(round(total_impuestos, 4))
				gravado = ET.SubElement(impuestos, 'IngresosNetosGravados')
				if not d.invoice_line_tax_ids:
					#subtotal_neto_DR = 0.00
					gravado.text = str(round(0.00, 4))
				else:
					gravado.text = str(round(subtotal_neto_DR, 4))
				iva = ET.SubElement(impuestos, 'TotalDeIVA')
				iva.text = str(round(total_impuestos, 4))
				if priceDR['taxes']:
					for i in priceDR['taxes']:
						impuesto = ET.SubElement(impuestos, 'Impuesto')
						tipo = ET.SubElement(impuesto, 'Tipo')
						tipo.text = str((self.env['account.tax'].browse([i['id']]).type_eface))
						base = ET.SubElement(impuesto, 'Base')
						base.text = str(round(subtotal_neto_DR, 4))
						tasa = ET.SubElement(impuesto, 'Tasa')
						tasa.text = str((self.env['account.tax'].browse([i['id']]).amount))
						monto_impu = ET.SubElement(impuesto, 'Monto')
						monto_impu.text = str(round(i['amount'], 4))
				else:
					impuesto = ET.SubElement(impuestos, 'Impuesto')
					tipo = ET.SubElement(impuesto, 'Tipo')
					tipo.text = str("IVA")
					base = ET.SubElement(impuesto, 'Base')
					base.text = str(round(d.price_subtotal, 4))
					tasa = ET.SubElement(impuesto, 'Tasa')
					tasa.text = str(0.00)
					monto_impu = ET.SubElement(impuesto, 'Monto')
					monto_impu.text = str(0.00)
				categoria = ET.SubElement(detalle, 'Categoria')
				if d.product_id.type == 'service':
					categoria.text = str("SERVICIO")
				else:
					categoria.text = str("BIEN")
				if len(cadena) > 1:
					descri_extra = ET.SubElement(detalle, 'TextosDePosicion')
					for x in range(1, len(cadena)):
						texto_extra = ET.SubElement(descri_extra, 'Texto')
						texto_extra.text = cadena[x]
			#Totales
			totales = ET.SubElement(factura, 'Totales')
			subtotal_sin_dr = ET.SubElement(totales, 'SubTotalSinDR')
			subtotal_sin_dr.text = str(round(total_neto_SDR, 4))
			tdrs = ET.SubElement(totales, 'DescuentosYRecargos')
			tsumdrs = ET.SubElement(tdrs, 'SumaDeDescuentos')
			tsumdrs.text = str(round((total_descuento), 4))
			for des in descuentos:
				tdr = ET.SubElement(tdrs, 'DescuentoORecargo')
				top = ET.SubElement(tdr, 'Operacion')
				top.text = str('DESCUENTO')
				tsrv = ET.SubElement(tdr, 'Servicio')
				tsrv.text = str('ALLOWANCE_GLOBAL')
				tdbase = ET.SubElement(tdr, 'Base')
				tdbase.text = str(round(des['base'], 4))
				tdtasa = ET.SubElement(tdr, 'Tasa')
				tdtasa.text = str(round(des['tasa'], 4))
				tdmonto = ET.SubElement(tdr, 'Monto')
				tdmonto.text = str(round(des['monto'], 4))
			subtotal_con_dr = ET.SubElement(totales, 'SubTotalConDR')
			subtotal_con_dr.text = str(round(line.amount_untaxed, 4))
			impuestos_total = ET.SubElement(totales, 'Impuestos')
			total_iva = ET.SubElement(impuestos_total, 'TotalDeImpuestos')
			total_iva.text = str(round(line.amount_tax, 4))
			total_gravado = ET.SubElement(impuestos_total, 'IngresosNetosGravados')
			total_base = 0.00
			if line.amount_tax == 0.00:
				total_base = line.amount_untaxed
				tasa_iva = 0.00
				total_siniva = 0.00
			else:
				tasa_iva = 12.00
				total_siniva = line.amount_untaxed
			total_gravado.text = str(round(total_siniva, 4))
			total_del_iva = ET.SubElement(impuestos_total, 'TotalDeIVA')
			total_del_iva.text = str(round(line.amount_tax, 4))
			#Impuestos afectos por linea de factura
			#for tax_total in taxes_lista
			total_impuesto = ET.SubElement(impuestos_total, 'Impuesto')
			tipo_total = ET.SubElement(total_impuesto, 'Tipo')
			tipo_total.text = str("IVA")
			base_total = ET.SubElement(total_impuesto, 'Base')
			base_total.text = str(round(total_siniva, 4))
			tasa_total = ET.SubElement(total_impuesto, 'Tasa')
			#if line.amount_tax == 0.00:
				#tasa_iva = 0.00
			tasa_total.text = str(round(tasa_iva, 4))
			monto_total = ET.SubElement(total_impuesto, 'Monto')
			monto_total.text = str(round(line.amount_tax, 4))
			#Total del Documento en letras y monto
			total_total = ET.SubElement(totales, 'Total')
			total_total.text = str(round(line.amount_total, 4))
			total_letras = ET.SubElement(totales, 'TotalLetras')
			total_letras.text = str(Numero_a_Texto(line.amount_total))
			xml_string = ET.tostring(factura, xml_declaration=True, encoding="UTF-8", pretty_print=True)
			#raise osv.except_osv(_('Prueba'), _('%s')%(xml_string))
		return xml_string


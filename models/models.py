# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from requests.structures import CaseInsensitiveDict
import requests, base64

APIURL= "https://api.zippin.com.ar/v2"
ID_CORREO_ARGENTINO = 233
ID_OCA = 208
ID_ANDREANI = 1
ID_STANDARD_DELIVERY = 1
ID_PICKUP_DELIVERY = 9

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _check_carrier_quotation(self, force_carrier_id=None):
        self.ensure_one()
        DeliveryCarrier = self.env['delivery.carrier']

        if self.only_services:
            self.write({'carrier_id': None})
            self._remove_delivery_line()
            return True
        else:
            self = self.with_company(self.company_id)
            # attempt to use partner's preferred carrier
            if not force_carrier_id and self.partner_shipping_id.property_delivery_carrier_id:
                force_carrier_id = self.partner_shipping_id.property_delivery_carrier_id.id

            carrier = force_carrier_id and DeliveryCarrier.browse(force_carrier_id) or self.carrier_id
            available_carriers = self._get_delivery_methods()
            if carrier:
                if carrier not in available_carriers:
                    carrier = DeliveryCarrier
                else:
                    # set the forced carrier at the beginning of the list to be verfied first below
                    available_carriers -= carrier
                    available_carriers = carrier + available_carriers
            if force_carrier_id or not carrier or carrier not in available_carriers:
                for delivery in available_carriers:
                    verified_carrier = delivery._match_address(self.partner_shipping_id)
                    if verified_carrier:
                        carrier = delivery
                        break
                self.write({'carrier_id': carrier.id})
            self._remove_delivery_line()
            if carrier:
                res = carrier.rate_shipment(self)
                if res.get('success'):
                    self.env['zippin.odoo'].search([]).unlink()
                    self.set_delivery_line(carrier, res['price'])
                    self.delivery_rating_success = True
                    self.env['zippin.odoo'].create(res['zippin_pickup'])
                    self.delivery_message = res['warning_message']
                else:
                    self.set_delivery_line(carrier, 0.0)
                    self.delivery_rating_success = False
                    self.delivery_message = res['error_message']

        return bool(carrier)

class ZippinPickupPoints(models.Model):
    _name = 'zippin.odoo'

    carrier_id = fields.Char(string="ID Proveedor")
    point_id = fields.Char(string="ID Sucursal")
    name = fields.Char(string="Nombre/Descripcion")
    address = fields.Char(string="Direccion")

class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    zippin_pickup_view = fields.Boolean()
    zippin_pickup = fields.Many2one('zippin.odoo', string="Sucursales")

    def delete_pickup_points(self):
        res = self.env['zippin.odoo'].search([]).unlink()
        return(res)

    @api.onchange('carrier_id')
    def _onchange_carrier_id(self):
        self.display_price = 0
        self.delivery_price = 0
        self.zippin_pickup = ''
        zippin_pickup_name = str(self.carrier_id.product_id.zippin_shipment_type)
        if 'suc' in zippin_pickup_name:
            self.zippin_pickup_view = True
        else: 
            self.zippin_pickup_view = False

    def _get_shipment_rate(self):
        self.delete_pickup_points()
        vals = self.carrier_id.rate_shipment(self.order_id)
        if vals.get('success'):
            self.delivery_message = vals.get('warning_message', False)
            self.delivery_price = vals['price']
            self.display_price = vals['carrier_price']
            self.env['zippin.odoo'].create(vals['zippin_pickup'])
            return {}
        return {'error_message': vals['error_message']}

    def button_confirm(self):
        if self.delivery_type == 'zippin' and self.display_price > 1 and self.delivery_price > 1:
            self.order_id.set_delivery_line(self.carrier_id, self.delivery_price)
            self.order_id.write({
                'recompute_delivery_price': False,
                'delivery_message': self.delivery_message,
            })
        elif self.delivery_type == 'fixed' and self.display_price < 1 and self.delivery_price < 1:
            self.order_id.set_delivery_line(self.carrier_id, self.delivery_price)
            self.order_id.write({
                'recompute_delivery_price': False,
                'delivery_message': self.delivery_message,
            })
        else:
            raise ValidationError('Primero obtener tarifa')

class ResCompany(models.Model):
    _inherit = 'res.company'

    zippin_id = fields.Char(string='Account ID', help='Ingresar Zippin Account ID. Obligatorio.')
    zippin_key = fields.Char(string='Zippin Key', help='Ingresar Zippin Key. Obligatorio')
    zippin_secret = fields.Char(string='Zippin Secret', help='Ingresar Zippin Secret. Obligatorio.')

class ProductTemplate(models.Model):
    _inherit = "product.template"

    zippin_shipment = fields.Boolean('Conectar con Zippin',help='Conecta el proveedor de envíos con Zippin',index=True)

    zippin_shipment_type = fields.Selection([
            ("zippin_car_suc", "Correo Argentino a Sucursal"), 
            ("zippin_car_dom", "Correo Argentino a Domicilio"),
            ("zippin_oca_suc", "OCA a Sucursal"),
            ("zippin_oca_dom", "OCA a Domicilio"),
            ("zippin_and_suc", "Andreani a Sucursal"),
            ("zippin_and_dom", "Andreani a Domicilio"),
        ],
        string="Seleccionar Proveedor y Tipo de Envío",
    )

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('zippin', 'Zippin')], ondelete={'zippin': 'set default'})
    zippin_pickup = fields.Many2one('zippin.odoo', string="Sucursales")

    def _zippin_api_headers(self, order):

        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"

        zippin_auth = "%s:%s" % (order.company_id.zippin_key, order.company_id.zippin_secret)
        zippin_auth = base64.b64encode(zippin_auth.encode("utf-8")).decode("utf-8")

        headers["Authorization"] = "Basic " + zippin_auth

        return(headers)

    def _zippin_get_origen_id(self, order):

        url = APIURL + "/addresses?account_id=" + order.company_id.zippin_id

        r = requests.get(url, headers=self._zippin_api_headers(order))
        r = r.json()

        for i in r["data"]:
            if i["id"]:
               resp = i["id"]

        return(resp)

    def _zippin_prepare_items(self, order):

        if order.order_line:
            r = []

            for p in order.order_line:
                if p.product_type != 'service' and p.product_type != 'consu':
                    if p.product_id.weight == False or p.product_id.product_height == False or p.product_id.product_width == False or p.product_id.product_length == False:
                        raise ValidationError('Error: El producto ' + p.product_id.name + ' debe tener peso y tamaño asignados.')

                    for i in range(int(p.product_uom_qty)):
                        product_list = {
                          "weight": p.product_id.weight * 1000,
                          "height": p.product_id.product_height,
                          "width": p.product_id.product_width,
                          "length": p.product_id.product_length,
                          "description": p.product_id.name,
                          "classification_id": 1
                        }

                        r.append(product_list)

        return(r)

    def _zippin_to_shipping_data(self, order):

        if order.partner_shipping_id.city == False:
            raise ValidationError('¡El Cliente debe tener Ciudad!')
        elif order.partner_shipping_id.state_id.name == False:
            raise ValidationError('¡El Cliente debe tener Estado/Provincia!')
        elif order.partner_shipping_id.zip == False:
            raise ValidationError('¡El Cliente debe tener Codigo Postal!')
        else:
            r = {
                "city": order.partner_shipping_id.city,
                "state": order.partner_shipping_id.state_id.name,
                "zipcode": order.partner_shipping_id.zip,
            }
        return(r)

    def zippin_rate_shipment(self, order):

        url = APIURL + "/shipments/quote"

        #VALOR DECLARADO EN CERO SI NO SE PONE SEGURO AL ENVIO
        data = {
            "account_id": order.company_id.zippin_id,
            "origin_id": self._zippin_get_origen_id(order),
            "declared_value": 0,
        }

        data["items"] = self._zippin_prepare_items(order)

        data["destination"]= self._zippin_to_shipping_data(order)

        r = requests.post(url, headers=self._zippin_api_headers(order), json=data)

        if r.status_code == 200:
            shipment_price = -1
            r= r.json()
            pickup_res = []
            pickup_address = ''

            for i in r["all_results"]:
                if self.product_id.zippin_shipment_type == 'zippin_car_suc':
                    if i["carrier"]["id"] == ID_CORREO_ARGENTINO and i["service_type"]["id"] == ID_PICKUP_DELIVERY:
                        shipment_price = i["amounts"]["price"]

                elif self.product_id.zippin_shipment_type == 'zippin_car_dom':
                    if i["carrier"]["id"] == ID_CORREO_ARGENTINO and i["service_type"]["id"] == ID_STANDARD_DELIVERY:
                        shipment_price = i["amounts"]["price"]

                elif self.product_id.zippin_shipment_type == 'zippin_oca_suc':
                    if i["carrier"]["id"] == ID_OCA and i["service_type"]["id"] == ID_PICKUP_DELIVERY:
                        shipment_price = i["amounts"]["price"]

                elif self.product_id.zippin_shipment_type == 'zippin_oca_dom':
                    if i["carrier"]["id"] == ID_OCA and i["service_type"]["id"] == ID_STANDARD_DELIVERY:
                        shipment_price = i["amounts"]["price"]

                elif self.product_id.zippin_shipment_type == 'zippin_and_suc':
                    if i["carrier"]["id"] == ID_ANDREANI and i["service_type"]["id"] == ID_PICKUP_DELIVERY:
                        shipment_price = i["amounts"]["price"]

                elif self.product_id.zippin_shipment_type == 'zippin_and_dom':
                    if i["carrier"]["id"] == ID_ANDREANI and i["service_type"]["id"] == ID_STANDARD_DELIVERY:
                        shipment_price = i["amounts"]["price"]

                if i["service_type"]["id"] == ID_PICKUP_DELIVERY:
                    for f in i["pickup_points"]:
                        pickup_points = {
                            "carrier_id": i["carrier"]["id"],
                            "point_id": f["point_id"],
                            "name": f["description"],
                            "address": f["location"]["street"] + ' ' + f["location"]["street_number"] + ' ' + f["location"]["city"] + ' ' + f["location"]["state"]
                        }
                        pickup_res.append(pickup_points)

            if shipment_price != -1:
                return {
                    'success': True,
                    'price': shipment_price,
                    'zippin_pickup': pickup_res,
                    'error_message': False,
                    'warning_message': False
                }
            else:
                return {
                    'success': False,
                    'price': 0,
                    'error_message': 'No disponible'
                }

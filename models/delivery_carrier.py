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

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[('zippin', 'Zippin')], ondelete={'zippin': 'set default'})
    zippin_pickup = fields.Many2one('zippin.shipping', string="Sucursales")
    zippin_shipment = fields.Boolean('Conectar con Zippin',help='Conecta el proveedor de envíos con Zippin',index=True)
    zippin_shipment_type = fields.Selection([
            (str(ID_CORREO_ARGENTINO), "Correo Argentino"), 
            (str(ID_OCA), "OCA"),
            (str(ID_ANDREANI), "Andreani"),
        ],
        string="Seleccionar Proveedor y Tipo de Envío",
    )
    zippin_shipment_type_is_pickup = fields.Boolean('Es envio a Sucursal')

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

        if r.status_code == 403:
            raise ValidationError('Zippin: Error de autorización, revise sus credenciales.')
        else:
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
            zp_phone = ''
            if order.partner_shipping_id.phone:
                zp_phone = zp_phone + order.partner_shipping_id.phone
            elif order.partner_shipping_id.mobile:
                zp_phone = ' - ' + order.partner_shipping_id.mobile
            r = {
                "city": order.partner_shipping_id.city,
                "state": order.partner_shipping_id.state_id.name,
                "zipcode": order.partner_shipping_id.zip,
                "name": order.partner_shipping_id.name,
                "document": order.partner_shipping_id.vat,
                "street": order.partner_shipping_id.street,
                "street_number": order.partner_shipping_id.street2,
                "street_extras": '',
                "phone": zp_phone,
                "email": order.partner_shipping_id.email,
            }
        return(r)

    def zippin_rate_shipment(self, order):

        url = APIURL + "/shipments/quote"

        #VALOR DECLARADO EN CERO SI NO SE PONE SEGURO AL ENVIO
        if order.company_id.zippin_key == False or order.company_id.zippin_id == False or order.company_id.zippin_secret == False:
            raise ValidationError('Debe ingresar las credenciales de Zippin en ajustes de la Empresa')

        data = {
            "account_id": order.company_id.zippin_id,
            "origin_id": self._zippin_get_origen_id(order),
            "declared_value": 0,
        }

        data["items"] = self._zippin_prepare_items(order)

        data["destination"]= self._zippin_to_shipping_data(order)

        r = requests.post(url, headers=self._zippin_api_headers(order), json=data)

        if r.status_code == 200:
            shipment_price = 0
            r= r.json()
            pickup_res = []
            pickup_address = ''
            logistic_type = ''

            for i in r["all_results"]:
                if self.zippin_shipment_type_is_pickup:
                    if i["carrier"]["id"] == int(self.zippin_shipment_type) and i["service_type"]["id"] == ID_PICKUP_DELIVERY:
                        shipment_price = i["amounts"]["price"]
                        logistic_type = i["logistic_type"]
                else:
                    if i["carrier"]["id"] == int(self.zippin_shipment_type) and i["service_type"]["id"] == ID_STANDARD_DELIVERY:
                        shipment_price = i["amounts"]["price"]
                        logistic_type = i["logistic_type"]

                if i["service_type"]["id"] == ID_PICKUP_DELIVERY:
                    for f in i["pickup_points"]:
                        pickup_points = {
                            "order_id": order.id,
                            "carrier_id": i["carrier"]["id"],
                            "point_id": f["point_id"],
                            "name": f["description"],
                            "address": f["location"]["street"] + ' ' + f["location"]["street_number"] + ' ' + f["location"]["city"] + ' ' + f["location"]["state"],
                            "logistic_type": i["logistic_type"]
                        }
                        pickup_res.append(pickup_points)
            return {
                'success': True,
                'price': shipment_price,
                'zippin_pickup': pickup_res,
                'logistic_type': logistic_type,
                'error_message': False,
                'warning_message': False
            }

        elif r.status_code == 408:
            return {
                'success': False,
                'price': 0,
                'error_message': 'Error. La solicitud está tomando demasiado tiempo en procesarse, intente nuevamente.',
                'warning_message': False
            }
        elif r.status_code == 500:
            return {
                'success': False,
                'price': 0,
                'error_message': 'Error interno. Intente nuevamente.',
                'warning_message': False
            }
        elif r.status_code == 503:
            return {
                'success': False,
                'price': 0,
                'error_message': 'Error interno. El servidor se encuentra saturado, espere unos minutos y vuelva a intentarlo.',
                'warning_message': False
            }
        else:
            data = r.json()
            return {
                'success': False,
                'price': 0,
                'error_message': 'No disponible',
                'warning_message': False
            }
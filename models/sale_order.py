from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.zippin.models.delivery_carrier import ID_CORREO_ARGENTINO, ID_OCA, ID_ANDREANI, APIURL
from requests.structures import CaseInsensitiveDict
import requests, base64

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    zippin_pickup_order_id = fields.Char(string="ID Orden")
    zippin_pickup_carrier_id = fields.Char(string="ID Proveedor")
    zippin_pickup_is_pickup = fields.Boolean(string="¿Es envio a Sucursal?")
    zippin_pickup_point_id = fields.Char(string="ID Sucursal")
    zippin_pickup_name = fields.Char(string="Nombre/Descripcion")
    zippin_pickup_address = fields.Char(string="Direccion")
    zippin_logistic_type = fields.Char()

    zippin_shipping_id = fields.Char()
    zippin_shipping_delivery_id = fields.Char()
    zippin_shipping_carrier_tracking_id = fields.Char()
    zippin_shipping_carrier_tracking_id_alt = fields.Char()
    zippin_shipping_tracking = fields.Char()
    zippin_shipping_tracking_external = fields.Char()
    zippin_create_shipping_view = fields.Boolean()
    zippin_create_label_view = fields.Boolean(default='True')
    zippin_shipping_label_bin = fields.Binary()
    zippin_shipping_label_filename = fields.Char(compute='_compute_shipping_label_filename')

    @api.depends('zippin_shipping_label_bin')
    def _compute_shipping_label_filename(self):
        self.ensure_one()
        name = ''
        if self.zippin_shipping_id:
            name = self.zippin_shipping_id
        name = name.replace('/', '_')
        name = name.replace('.', '_')
        name = name + '.pdf'
        self.zippin_shipping_label_filename = name

    def action_zippin_get_label(self):

        url = APIURL + "/shipments/" + self.zippin_shipping_id +"/documentation?what=label&format=pdf"
        #url = APIURL + "/shipments/577722/documentation?what=label&format=pdf"

        r = requests.get(url, headers=self._zippin_api_headers())

        if r.status_code == 403:
            raise ValidationError('Zippin: Error de autorización, revise sus credenciales.')
        else:
            r = r.json()
            self.zippin_shipping_label_bin = r["body"]   
            self.zippin_create_label_view = True

    def _check_carrier_quotation(self, force_carrier_id=None):
        res = super(SaleOrder, self)._check_carrier_quotation(force_carrier_id=None)

        zp_DeliveryCarrier = self.env['delivery.carrier']
        if self.only_services == False:
            zp_carrier = force_carrier_id and zp_DeliveryCarrier.browse(force_carrier_id) or self.carrier_id
            if zp_carrier:
                zp_res = zp_carrier.rate_shipment(self)
                if zp_res.get('success'):
                    self.env['zippin.shipping'].search([]).unlink()
                    self.set_delivery_line(zp_carrier, zp_res['price'])
                    self.delivery_rating_success = True
                    if self.carrier_id.zippin_shipment_type:
                        self.env['zippin.shipping'].create(zp_res['zippin_pickup'])
                        self.zippin_logistic_type = zp_res['logistic_type']
                    self.delivery_message = zp_res['warning_message']
                    self.zippin_pickup_order_id = self._origin.id
                    self.zippin_pickup_carrier_id = self.carrier_id.zippin_shipment_type
                    if self.carrier_id.zippin_shipment_type_is_pickup:
                        self.zippin_pickup_is_pickup = True
                    else: 
                        self.zippin_pickup_is_pickup = False
        return res

    def _zippin_api_headers(self):

        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "application/json"

        zippin_auth = "%s:%s" % (self.company_id.zippin_key, self.company_id.zippin_secret)
        zippin_auth = base64.b64encode(zippin_auth.encode("utf-8")).decode("utf-8")

        headers["Authorization"] = "Basic " + zippin_auth

        return(headers)

    def _zippin_get_origen_id(self):

        url = APIURL + "/addresses?account_id=" + self.company_id.zippin_id

        r = requests.get(url, headers=self._zippin_api_headers())

        if r.status_code == 403:
            raise ValidationError('Zippin: Error de autorización, revise sus credenciales.')
        else:
            r = r.json()
            for i in r["data"]:
                if i["id"]:
                   resp = i["id"]
            return(resp)

    def _zippin_prepare_items(self):

        if self.order_line:
            r = []

            for p in self.order_line:
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

    def _zippin_to_shipping_data(self):

        if self.partner_shipping_id.city == False:
            raise ValidationError('¡El Cliente debe tener Ciudad!')
        elif self.partner_shipping_id.state_id.name == False:
            raise ValidationError('¡El Cliente debe tener Estado/Provincia!')
        elif self.partner_shipping_id.zip == False:
            raise ValidationError('¡El Cliente debe tener Codigo Postal!')
        else:
            zp_phone = ''
            if self.partner_shipping_id.phone:
                zp_phone = zp_phone + self.partner_shipping_id.phone
            elif self.partner_shipping_id.mobile:
                zp_phone = ' - ' + self.partner_shipping_id.mobile
            r = {
                "city": self.partner_shipping_id.city,
                "state": self.partner_shipping_id.state_id.name,
                "zipcode": self.partner_shipping_id.zip,
                "name": self.partner_shipping_id.name,
                "document": self.partner_shipping_id.vat,
                "street": self.partner_shipping_id.street,
                "street_number": self.partner_shipping_id.street2,
                "street_extras": '',
                "phone": zp_phone,
                "email": self.partner_shipping_id.email,
            }
        return(r)

    def action_zippin_create_shipping(self):

        url = APIURL + "/shipments"

        #VALOR DECLARADO EN CERO SI NO SE PONE SEGURO AL ENVIO
        if self.company_id.zippin_key == False or self.company_id.zippin_id == False or self.company_id.zippin_secret == False:
            raise ValidationError('Debe ingresar las credenciales de Zippin en ajustes de la Empresa')

        service_type = 'standard_delivery'
        if self.zippin_pickup_is_pickup:
            service_type = 'pickup_delivery'

        data = {
            "external_id": 'PedidoWeb-OrderID-'+str(self.id),
            "account_id": self.company_id.zippin_id,
            "origin_id": self._zippin_get_origen_id(),
            "service_type": service_type,
            "logistic_type": self.zippin_logistic_type,
            "carrier_id": self.zippin_pickup_carrier_id,
            "declared_value": 0,
        }

        data["items"] = self._zippin_prepare_items()

        data["destination"]= self._zippin_to_shipping_data()

        r = requests.post(url, headers=self._zippin_api_headers(), json=data)

        if r.status_code == 201:
            r= r.json()

            self.zippin_shipping_id = r["id"]
            self.zippin_shipping_delivery_id = r["delivery_id"]
            self.zippin_shipping_carrier_tracking_id = r["carrier_tracking_id"]
            self.zippin_shipping_carrier_tracking_id_alt = r["carrier_tracking_id_alt"]
            self.zippin_shipping_tracking = r["tracking"]
            self.zippin_shipping_tracking_external = r["tracking_external"]
            self.zippin_create_shipping_view = True
            self.zippin_create_label_view = False

        else:
            raise ValidationError('Error')
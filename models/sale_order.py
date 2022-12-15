from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.zippin.models.delivery_carrier import ID_CORREO_ARGENTINO, ID_OCA, ID_ANDREANI, APIURL
from requests.structures import CaseInsensitiveDict
import requests, base64

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def delete_pickup_points(self):
        res = self.env['zippin.shipping'].search([('order_id','=', int(self.order_id.id))]).unlink()
        return(res)

    def delete_zippin_shipping(self):
        self.order_id.zippin_shipping_label_bin = None
        self.order_id.zippin_pickup_order_id = None
        self.order_id.zippin_pickup_carrier_id = None
        self.order_id.zippin_pickup_is_pickup = None
        self.order_id.zippin_pickup_point_id = None 
        self.order_id.zippin_pickup_name = None 
        self.order_id.zippin_pickup_address = None 
        self.order_id.zippin_logistic_type = None 
        self.order_id.zippin_shipping_id = None 
        self.order_id.zippin_shipping_delivery_id = None 
        self.order_id.zippin_shipping_carrier_tracking_id = None 
        self.order_id.zippin_shipping_carrier_tracking_id_alt = None 
        self.order_id.zippin_shipping_tracking = None 
        self.order_id.zippin_shipping_tracking_external = None 
        self.order_id.zippin_create_shipping_view = True
        self.order_id.zippin_create_label_view = True
        self.order_id.zippin_delete_shipping_view = True

    #Borra la informacion de envio cuando aun no se generó la etiqueta de envio.
    def delete_zippin_info(self):
        if self.order_id.zippin_shipping_id:
            raise ValidationError('No se puede borrar o actualizar un envío ya creado, primero cancele el envio.')
        else:
            self.delete_zippin_shipping()

    #Modifico la funcion unlink para que borre sucursales e informacion de envio en sale.order
    def unlink(self):
        for line in self:
            if line.is_delivery:
                self.delete_pickup_points()
                self.delete_zippin_info()
        res = super(SaleOrderLine, self).unlink()
        return res

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
    zippin_create_shipping_view = fields.Boolean(default='True')
    zippin_create_label_view = fields.Boolean(default='True')
    zippin_shipping_label_bin = fields.Binary()
    zippin_shipping_label_filename = fields.Char(compute='_compute_shipping_label_filename')


    zippin_delete_shipping_view = fields.Boolean(default='True')

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

            if self.zippin_pickup_is_pickup:
                r = {
                    "name": self.partner_shipping_id.name,
                    "document": self.partner_shipping_id.vat,
                    "phone": zp_phone,
                    "email": self.partner_shipping_id.email,
                    "point_id": int(self.zippin_pickup_point_id),
                }
            else: 
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
            service_type = 'pickup_point'

        data = {
            "external_id": str(self.company_id.zippin_description_web)+'-N-'+str(self.id),
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
            self.zippin_delete_shipping_view = False

        else:
            r= r.json()
            raise ValidationError('Zippin Error: ' +r["message"])

    def action_zippin_delete_shipping(self):

        url = APIURL + "/shipments/" + self.zippin_shipping_id +"/cancel"
        r = requests.post(url, headers=self._zippin_api_headers())

        if r.status_code == 200:
            r = r.json()
            self.delete_zippin_shipping()
        elif r.status_code == 401:
            raise ValidationError('Zippin: Error, no se pudo cancelar el envío')
        else:
            raise ValidationError(r.status_code)

    def delete_zippin_shipping(self):

        self.zippin_shipping_label_bin = None
        self.zippin_pickup_order_id = None
        self.zippin_pickup_carrier_id = None
        self.zippin_pickup_is_pickup = None
        self.zippin_pickup_point_id = None 
        self.zippin_pickup_name = None 
        self.zippin_pickup_address = None 
        self.zippin_logistic_type = None 
        self.zippin_shipping_id = None 
        self.zippin_shipping_delivery_id = None 
        self.zippin_shipping_carrier_tracking_id = None 
        self.zippin_shipping_carrier_tracking_id_alt = None 
        self.zippin_shipping_tracking = None 
        self.zippin_shipping_tracking_external = None 
        self.zippin_create_shipping_view = True
        self.zippin_create_label_view = True
        self.zippin_delete_shipping_view = True

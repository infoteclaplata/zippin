from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.zippin.models.delivery_carrier import ID_CORREO_ARGENTINO, ID_OCA, ID_ANDREANI

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    zippin_pickup_order_id = fields.Char(string="ID Orden")
    zippin_pickup_carrier_id = fields.Char(string="ID Proveedor")
    zippin_pickup_is_pickup = fields.Boolean(string="¿Es envio a Sucursal?")
    zippin_pickup_point_id = fields.Char(string="ID Sucursal")
    zippin_pickup_name = fields.Char(string="Nombre/Descripcion")
    zippin_pickup_address = fields.Char(string="Direccion")
    zippin_logistic_type = fields.Char()

    def _check_carrier_quotation(self, force_carrier_id=None):
        res = super(SaleOrder, self)._check_carrier_quotation(force_carrier_id=None)

        zp_DeliveryCarrier = self.env['delivery.carrier']
        if self.only_services == False:
            zp_carrier = force_carrier_id and zp_DeliveryCarrier.browse(force_carrier_id) or self.carrier_id
            if zp_carrier:
                zp_res = zp_carrier.rate_shipment(self)
                if zp_res.get('success'):
                    self.env['zippin.pickup.points'].search([]).unlink()
                    self.set_delivery_line(zp_carrier, zp_res['price'])
                    self.delivery_rating_success = True
                    self.env['zippin.pickup.points'].create(zp_res['zippin_pickup'])
                    self.delivery_message = zp_res['warning_message']
                    self.zippin_pickup_order_id = self._origin.id
                    self.zippin_logistic_type = zp_res['logistic_type']

                    zippin_pickup_name = str(self.carrier_id.product_id.zippin_shipment_type)
                    if 'zippin_car_' in zippin_pickup_name:
                        self.zippin_pickup_carrier_id = ID_CORREO_ARGENTINO
                    elif 'zippin_oca_' in zippin_pickup_name:
                        self.zippin_pickup_carrier_id = ID_OCA
                    elif 'zippin_and_' in zippin_pickup_name:
                        self.zippin_pickup_carrier_id = ID_ANDREANI

                    if 'suc' in zippin_pickup_name:
                        self.zippin_pickup_is_pickup = True
                    else: 
                        self.zippin_pickup_is_pickup = False

        return res
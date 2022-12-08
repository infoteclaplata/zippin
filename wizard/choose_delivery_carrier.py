from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.zippin.models.delivery_carrier import ID_CORREO_ARGENTINO, ID_OCA, ID_ANDREANI

class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    zippin_pickup_view_invisible = fields.Boolean()
    zippin_pickup_view_id = fields.Char()
    zippin_logistic_type = fields.Char()
    zippin_pickup = fields.Many2one('zippin.pickup.points', string="Sucursales", domain="[('order_id', '=', order_id)]")

    def delete_pickup_points(self):
        res = self.env['zippin.pickup.points'].search([('order_id','=', int(self.order_id))]).unlink()
        return(res)

    @api.onchange('carrier_id')
    def _onchange_carrier_id(self):
        res = super(ChooseDeliveryCarrier, self)._onchange_carrier_id()
        self.zippin_pickup = ''
        zippin_pickup_name = str(self.carrier_id.product_id.zippin_shipment_type)

        if 'suc' in zippin_pickup_name:
            self.zippin_pickup_view_invisible = False
        else: 
            self.zippin_pickup_view_invisible = True
            
        if 'zippin_car_' in zippin_pickup_name:
            self.zippin_pickup_view_id = ID_CORREO_ARGENTINO
        elif 'zippin_oca_' in zippin_pickup_name:
            self.zippin_pickup_view_id = ID_OCA
        elif 'zippin_and_' in zippin_pickup_name:
            self.zippin_pickup_view_id = ID_ANDREANI

        return res

    def _get_shipment_rate(self):
        res = super(ChooseDeliveryCarrier, self)._get_shipment_rate()
        self.delete_pickup_points()
        zp_vals = self.carrier_id.rate_shipment(self.order_id)
        if zp_vals.get('success'):
            self.zippin_logistic_type = zp_vals['logistic_type']
            self.env['zippin.pickup.points'].create(zp_vals['zippin_pickup'])
        return res

    def button_confirm(self):
        res = super(ChooseDeliveryCarrier, self).button_confirm()

        if self.delivery_type == 'zippin' and self.display_price > 1 and self.delivery_price > 1:

            zippin_pickup_name = str(self.carrier_id.product_id.zippin_shipment_type)

            if 'suc' in zippin_pickup_name:
                self.order_id.write({
                    'zippin_pickup_order_id': self.zippin_pickup['order_id'],
                    'zippin_pickup_carrier_id': self.zippin_pickup['carrier_id'],
                    'zippin_pickup_is_pickup': True,
                    'zippin_pickup_point_id': self.zippin_pickup['point_id'],
                    'zippin_pickup_name': self.zippin_pickup['name'],
                    'zippin_pickup_address': self.zippin_pickup['address'],
                    'zippin_logistic_type': self.zippin_pickup['logistic_type'],
                })
            else: 
                if 'zippin_car_' in zippin_pickup_name:
                    zippin_pickup_carrier_id = ID_CORREO_ARGENTINO
                elif 'zippin_oca_' in zippin_pickup_name:
                    zippin_pickup_carrier_id = ID_OCA
                elif 'zippin_and_' in zippin_pickup_name:
                    zippin_pickup_carrier_id = ID_ANDREANI

                self.order_id.write({
                    'zippin_pickup_order_id': int(self.order_id),
                    'zippin_pickup_carrier_id': zippin_pickup_carrier_id,
                    'zippin_pickup_is_pickup': False,
                    'zippin_pickup_point_id': None,
                    'zippin_pickup_name': None,
                    'zippin_pickup_address': None,
                    'zippin_logistic_type': self.zippin_logistic_type,
                })
        else:
            raise ValidationError('Primero obtener tarifa')

        return res
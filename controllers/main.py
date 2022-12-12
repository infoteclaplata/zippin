from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale_delivery.controllers.main import WebsiteSaleDelivery
from odoo.addons.zippin.models.delivery_carrier import ID_CORREO_ARGENTINO, ID_OCA, ID_ANDREANI

class ZippinPickupPoints(WebsiteSale):

    @http.route(['/shop/zippin_odoo'], type='json', auth="public", methods=['POST'], website=True)
    def zippin_pickup_points(self, **post):

        if post.get('point_id'):
            order = request.website.sale_get_order()
            redirection = self.checkout_redirection(order)
            if redirection:
                return redirection

            if order and order.id and order.zippin_pickup_carrier_id == post.get('carrier_id') and order.zippin_pickup_is_pickup == True:
                order.write({
                    'zippin_pickup_order_id': order.id,
                    'zippin_pickup_carrier_id': post.get('carrier_id'),
                    'zippin_pickup_point_id': post.get('point_id'),
                    'zippin_pickup_name': post.get('name'),
                    'zippin_pickup_address': post.get('address')
                })
            else:
                order.write({
                    'zippin_pickup_point_id': None,
                    'zippin_pickup_name': None,
                    'zippin_pickup_address': None
                })

        return True

class ZippinWebsiteSale(WebsiteSaleDelivery):

    def _get_shop_payment_values(self, order, **kwargs):
        zp_values = super(ZippinWebsiteSale, self)._get_shop_payment_values(order, **kwargs)

        zp_values['zippin_car_suc'] = request.env['zippin.shipping'].sudo().search([('carrier_id','=', ID_CORREO_ARGENTINO), ('order_id','=', order.id)])
        zp_values['zippin_oca_suc'] = request.env['zippin.shipping'].sudo().search([('carrier_id','=', ID_OCA), ('order_id','=', order.id)])
        zp_values['zippin_and_suc'] = request.env['zippin.shipping'].sudo().search([('carrier_id','=', ID_ANDREANI), ('order_id','=', order.id)])

        return zp_values
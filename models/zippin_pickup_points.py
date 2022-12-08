from odoo import models, fields, api

class ZippinPickupPoints(models.Model):
    _name = 'zippin.pickup.points'

    order_id = fields.Char(string="ID Orden")
    carrier_id = fields.Char(string="ID Proveedor")
    point_id = fields.Char(string="ID Sucursal")
    name = fields.Char(string="Nombre/Descripcion")
    address = fields.Char(string="Direccion")
    logistic_type = fields.Char()
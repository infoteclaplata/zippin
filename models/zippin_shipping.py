from odoo import models, fields, api

class ZippinShipping(models.Model):
    _name = 'zippin.shipping'

    order_id = fields.Char(string="ID Orden")
    carrier_id = fields.Char(string="ID Proveedor")
    point_id = fields.Char(string="ID Sucursal")
    name = fields.Char(string="Nombre/Descripcion")
    address = fields.Char(string="Direccion")
    logistic_type = fields.Char()
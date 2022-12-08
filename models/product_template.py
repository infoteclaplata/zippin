from odoo import models, fields, api

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
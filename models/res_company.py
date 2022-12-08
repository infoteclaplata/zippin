from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = 'res.company'

    zippin_id = fields.Char(string='Account ID', help='Ingresar Zippin Account ID. Obligatorio.')
    zippin_key = fields.Char(string='Zippin Key', help='Ingresar Zippin Key. Obligatorio')
    zippin_secret = fields.Char(string='Zippin Secret', help='Ingresar Zippin Secret. Obligatorio.')
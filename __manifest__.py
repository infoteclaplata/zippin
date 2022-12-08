# -*- coding: utf-8 -*-
{
    'name': "Zippin Odoo Connector",

    'summary': """
        Connector Odoo-Zippin for Shipping Payment""",

    'description': """
        Connector Odoo-Zippin for Shipping Payment
    """,

    'author': "InfotecLaPlata",
    'website': "https://www.InfotecLaPlata.com.ar",

    'category': 'Sales',
    'version': '0.1',

    'depends': ['base', 'sale', 'delivery', 'product_dimension'],

    'data': [
        'security/ir.model.access.csv',
        'views/res_company.xml',
        'views/product_template_views.xml',
        'views/website_sale_delivery_templates.xml',
        'views/zippin_pickup_views.xml',
        'views/sale_views.xml',
        'wizard/choose_delivery_carrier_views.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'zippin/static/src/js/zippin_odoo.js',
            'zippin/static/src/scss/zippin_odoo.scss'
        ],
    },
}

# -*- coding: utf-8 -*-
{
    'name': "Flexible Printing",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Azkatech",
    'website': "http://www.azka.tech",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Printing',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'mrp', 'sale_management'],

    # always loaded
    'data': [
        'data/layer_types_data.xml',
        'data/handle_types_data.xml',
        'data/seal_types_data.xml',
        'data/workcenter_types_data.xml',
        'data/products_data.xml',
        'data/module_data.xml',
        
        'security/flexibleprinting_security.xml',
        'security/ir.model.access.csv',
        
        'reports/flexibleprinting_mo.xml',
        'reports/flexibleprinting_mo_report.xml',
        'reports/flexibleprinting_inquiry_report.xml',
        
        'views/flexibleprinting_templates.xml',
        'views/res_config_settings_views.xml',
        'views/flexibleprinting_views.xml',
        'views/flexibleprinting_inquiry_views.xml',
        'views/flexibleprinting_workcenter.xml',
        'views/flexibleprinting_workcenter_rounting.xml',
        'views/flexibleprinting_manufacture_order.xml',
        'views/flexibleprinting_product_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    "css": [],
    'installable': True,
    'application': False,
}
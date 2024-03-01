# -*- coding: utf-8 -*-
{
    'name': "realestate",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
                'web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/account_security.xml',
        'views/views.xml',
        'views/templates.xml',
        'report/estate_reports.xml',
        'report/estate_report_views.xml',
        'data/demo.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'data/demo.xml',
    ],
    "application": True,
}
# -*- coding: utf-8 -*-
#   Copyright (C) 2017 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "SMS Client Core",
    "version": "1.0",
    "depends": ["base",
                "email_template",
                'base_phone',
                'keychain',
                ],
    "author": "Julius Network Solutions,SYLEAM,OpenERP SA,Akretion,"
              "Odoo Community Association (OCA)",
    'images': [
        'images/sms.jpeg',
        'images/gateway.jpeg',
        'images/gateway_access.jpeg',
        'images/client.jpeg',
        'images/send_sms.jpeg'
    ],
    "summary": """
Sending SMSs very easily, individually or collectively.

    """,
    "website": "http://julius.fr",
    "category": "Phone",
    "demo": [],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/smsclient_view.xml",
        "views/serveraction_view.xml",
        "views/smsclient_data.xml",
        "wizard/mass_sms_view.xml",
        "views/partner_sms_send_view.xml",
        "views/smstemplate_view.xml"
    ],
    "active": False,
    "installable": True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

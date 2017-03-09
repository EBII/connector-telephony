# -*- coding: utf-8 -*-
#   Copyright (C) 2017 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class email_template(models.Model):
    _inherit = "email.template"

    sms_template = fields.Boolean(string='SMS Template')
    mobile_to = fields.Char(string='To (Mobile)', size=256)
    gateway_id = fields.Many2one(comodel_name='sms.smsclient',
                                 string='SMS Gateway')

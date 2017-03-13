# -*- coding: utf-8 -*-
#   Copyright (C) 2017 Akretion (http://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import Warning
import urllib
import logging
#from odoo.addons.server_tools.keychain import
_logger = logging.getLogger(__name__)


PRIORITY_LIST = [
    ('0', '0'),
    ('1', '1'),
    ('2', '2'),
    ('3', '3')
]

CLASSES_LIST = [
    ('0', 'Flash'),
    ('1', 'Phone display'),
    ('2', 'SIM'),
    ('3', 'Toolkit')
]

class SmsAccount(models.Model):
    _inherit = 'keychain.account'

    namespace = fields.Selection(
        selection_add=[('SMS_CLIENT', 'SMS')])

    def _sms_client_init_data(self):
        return {
            "url_service": "",
            "sms_account": "",
            "login": "",
            "password": "",
            "from": "",
        }

    def _sms_client_validate_data(self, data):

        return len(data.get("agencyCode") > 3)


class partner_sms_send(models.Model):
    _name = "partner.sms.send"

    @api.model
    def _default_get_mobile(self):
        partner_pool = self.env['res.partner']
        active_ids = self._context.get('active_ids')
        res = {}
        if len(active_ids) > 1:
            raise Warning(_('You can only select one partner'))
        for partner in partner_pool.browse(active_ids):
            res = partner.mobile
        return res

    @api.model
    def _default_get_gateway(self):
        sms_obj = self.env['sms.smsclient']
        gateways = sms_obj.search([], limit=1)
        return gateways or False

    mobile_to = fields.Char(string='To', required=True,
                            default=_default_get_mobile)
    app_id = fields.Char(string='API ID')
    user = fields.Char(string='Login')
    password = fields.Char(string='Password')
    text = fields.Text(string='SMS Message', required=True)
    gateway = fields.Many2one(comodel_name='sms.smsclient',
                              string='SMS Gateway', required=True,
                              default=_default_get_gateway
                              )
    validity = fields.Integer(string='Validity',
                              help='the maximum time -in minute(s)-'
                                   'before the message is dropped')
    classes = fields.Selection(selection=CLASSES_LIST, string='Class',
        help='the sms class: flash(0), phone display(1), SIM(2), toolkit(3)')
    deferred = fields.Integer(string='Deferred',
                              help='the time -in minute(s)- '
                                   'to wait before sending the message')
    priority = fields.Selection(selection=PRIORITY_LIST, string='Priority',
                                help='The priority of the message')
    coding = fields.Selection(selection=[('1', '7 bit'), ('2', 'Unicode')],
        string='Coding', help='The SMS coding: 1 for 7 bit or 2 for unicode')
    tag = fields.Char(string='Tag', help='an optional tag')
    nostop = fields.Boolean(string='NoStop',
                            help='Do not display STOP clause in the message,'
                                 'this requires that this is not an '
                                 'advertising message')

    @api.multi
    def onchange_gateway(self, gateway_id):
        sms_obj = self.env['sms.smsclient']
        if not gateway_id:
            return {}
        gateway = sms_obj.browse(gateway_id)
        return {
            'value': {
                'validity': gateway.validity,
                'classes': gateway.classes,
                'deferred': gateway.deferred,
                'priority': gateway.priority,
                'coding': gateway.coding,
                'tag': gateway.tag,
                'nostop': gateway.nostop,
            }
        }

    @api.multi
    def sms_send(self):
        client_obj = self.env['sms.smsclient']
        for data in self:
            if not data.gateway:
                raise Warning(_('No Gateway Found'))
            else:
                client_obj._send_message(data)
        return {}


class SMSClient(models.Model):
    _name = 'sms.smsclient'
    _description = 'SMS Client'

    name = fields.Char(string='Gateway Name', required=True)
    url = fields.Char(string='Gateway URL',
                      help='Base url for message',
                      compute='_get_provider_conf'
                      )
    url_visible = fields.Boolean(default=False)
    history_line = fields.One2many(comodel_name='sms.smsclient.history',
                                   inverse_name='gateway_id',
                                   string='History')
    method = fields.Selection(string='API Method',
                              selection='get_method',
                              index=True, )
    state = fields.Selection(
        selection=[('new', 'Not Verified'),
                   ('waiting', 'Waiting for Verification'),
                   ('confirm', 'Verified'), ],
        string='Gateway Status', index=True, readonly=True, default='new')
    users_id = fields.Many2many(comodel_name='res.users',
                                relation='res_smsserver_group_rel',
                                column1='sid',
                                column2='uid',
                                string='Users Allowed')
    sms_account = fields.Char(compute='_get_provider_conf')
    sms_account_visible = fields.Boolean(default=False)
    login_provider = fields.Char(compute='_get_provider_conf')
    login_provider_visible = fields.Boolean(default=False)
    password_provider = fields.Char(compute='_get_provider_conf')
    password_provider_visible = fields.Boolean(default=False)
    from_provider = fields.Char(compute='_get_provider_conf')
    from_provider_visible = fields.Boolean(default=False)

    code = fields.Char(string='Verification Code')
    code_visible = fields.Boolean(default=False)
    body = fields.Text(string='Message',
                       help="The message text that will be send along with the"
                            " email which is send through this server")
    validity = fields.Integer(string='Validity',
                              help='The maximum time - in minute(s) - '
                                   'before the message is dropped',
                              default=10
                              )
    validity_visible = fields.Boolean(default=False)
    classes = fields.Selection(selection=CLASSES_LIST, string='Class',
        help='The SMS class: flash(0),phone display(1),SIM(2),toolkit(3)',
        default='1')
    classes_visible = fields.Boolean(default=False)
    deferred = fields.Integer(string='Deferred',
        help='The time -in minute(s)- to wait before sending the message',
        default=0)
    deferred_visible = fields.Boolean(default=False)

    priority = fields.Selection(selection=PRIORITY_LIST, string='Priority',
                                help='The priority of the message ',
                                default='3')
    priority_visible = fields.Boolean(default=False)
    coding = fields.Selection(
        selection=[('1', '7 bit'), ('2', 'Unicode')],
        string='Coding',
        help='The SMS coding: 1 for 7 bit (160 chracters max'
             'lenght) or 2 for unicode (70 characters max'
             'lenght)',
        default='1')
    coding_visible = fields.Boolean(default=False)
    tag = fields.Char(string='Tag', help='an optional tag')
    tag_visible = fields.Boolean(default=False)
    nostop = fields.Boolean(string='NoStop',
                            help='Do not display STOP clause in the message,'
                                 'this requires that this is not an'
                                 'advertising message',
                            default=True
                            )
    nostop_visible = fields.Boolean(default=False)
    char_limit = fields.Boolean(string='Character Limit', default=True)
    char_limit_visible = fields.Boolean(default=False)
    default_gateway = fields.Boolean(default=False)

    @api.model
    def get_method(self):
        return []

    @api.multi
    def _get_provider_conf(self):
        for sms_provider in self:
            global_section_name = 'sms_provider'
            # default vals
            config_vals = {}
            if serv_config.has_section(global_section_name):
                config_vals.update((serv_config.items(global_section_name)))
                custom_section_name = '.'.join((global_section_name,
                                                sms_provider.name
                                                ))
                if serv_config.has_section(custom_section_name):
                    config_vals.update(serv_config.items(custom_section_name))
                    if config_vals.get('url_service'):
                        sms_provider.url = config_vals['url_service']
                    if config_vals.get('sms_account'):
                        sms_provider.sms_account = config_vals['sms_account']
                    if config_vals.get('login'):
                        sms_provider.login_provider = config_vals['login']
                    if config_vals.get('password'):
                        sms_provider.password_provider = config_vals[
                            'password']
                    if config_vals.get('from'):
                        sms_provider.from_provider = config_vals['from']

    @api.onchange('method')
    def onchange_method(self):
        if not self.method:
            self.url_visible = False
            self.sms_account_visible = False
            self.login_provider_visible = False
            self.password_provider_visible = False
            self.from_provider_visible = False
            self.validity_visible = False
            self.classes_visible = False
            self.deferred_visible = False
            self.nostop_visible = False
            self.priority_visible = False
            self.coding_visible = False
            self.tag_visible = False
            self.char_limit_visible = False

    @api.model
    def _check_permissions(self, gateway):
        # cr = self.env.cr
        # cr.execute('select * from res_smsserver_group_rel'
        #            ' where sid= %s and uid= %s' % (gateway.id, self.env.uid))
        # data = cr.fetchall()
        data = self.env['res.smsserver.group.rel'].search(
            [('sid', '=', gateway.id),('uid', '=', self.env.uid)])
        if len(data) <= 0:
            return False
        return True

    @api.model
    def _prepare_smsclient_queue(self, data, name):
        return {
            'name': name,
            'gateway_id': data.gateway.id,
            'state': 'draft',
            'mobile': data.mobile_to,
            'msg': data.text,
            'validity': data.validity,
            'classes': data.classes,
            'deffered': data.deferred,
            'priority': data.priority,
            'coding': data.coding,
            'tag': data.tag,
            'nostop': data.nostop,
        }

    # This method must be inherit to forming the url according to the provider
    @api.model
    def _send_message(self, data):
        return True

    @api.model
    def _check_queue(self):
        queue_obj = self.env['sms.smsclient.queue']
        history_obj = self.env['sms.smsclient.history']
        sids = queue_obj.search([
            ('state', '!=', 'send'),
            ('state', '!=', 'sending')
            ], limit=30)
        error_ids = []
        sent_ids = []
        for sms in sids:
            sms.state = 'sending'
            if sms.gateway_id.char_limit:
                if len(sms.msg) > 160:
                    error_ids.append(sms.id)
                    continue
            if 'http' in sms.gateway_id.method:
                try:
                    answer = urllib.urlopen(sms.name)
                    _logger.info(answer.read())
                except Exception, e:
                    raise Warning(e)
            history_obj.create({
                'name': _('SMS Sent'),
                'gateway_id': sms.gateway_id.id,
                'sms': sms.msg,
                'to': sms.mobile,
                })
            sent_ids.append(sms.id)
        rec_sent_ids = queue_obj.browse(sent_ids)
        rec_sent_ids.write({'state': 'send'})
        rec_error_ids = queue_obj.browse(error_ids)
        rec_error_ids.write({
            'state': 'error',
            'error': 'Size of SMS should not be more then 160 char'
            })
        return True


class SMSQueue(models.Model):
    _name = 'sms.smsclient.queue'
    _description = 'SMS Queue'

    name = fields.Text(string='SMS Request', size=256,
                       required=True, readonly=True,
                       states={'draft': [('readonly', False)]})
    msg = fields.Text(string='SMS Text', size=256,
                      required=True, readonly=True,
                      states={'draft': [('readonly', False)]})
    mobile = fields.Char(string='Mobile No', size=256,
                         required=True, readonly=True,
                         states={'draft': [('readonly', False)]})
    gateway_id = fields.Many2one(comodel_name='sms.smsclient',
                                 string='SMS Gateway', readonly=True,
                                 states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Queued'),
        ('sending', 'Waiting'),
        ('send', 'Sent'),
        ('error', 'Error'),
    ], 'Message Status', select=True, readonly=True, default='draft')
    error = fields.Text(string='Last Error', size=256,
                        readonly=True,
                        states={'draft': [('readonly', False)]})
    date_create = fields.Datetime(string='Date', readonly=True,
                                  default=fields.Datetime.now)
    validity = fields.Integer(
        string='Validity',
        help='The maximum time -in minute(s)- before the message is dropped')

    classes = fields.Selection(
        selection=CLASSES_LIST,
        string='Class',
        help='The sms class: flash(0), phone display(1), SIM(2), toolkit(3)')
    deferred = fields.Integer(
        string='Deferred',
        help='The time -in minute(s)- to wait before sending the message')

    priority = fields.Selection(selection=PRIORITY_LIST, string='Priority',
                                help='The priority of the message ')
    coding = fields.Selection(
        selection=[('1', '7 bit'), ('2', 'Unicode'), ],
        string='Coding', help='The sms coding: 1 for 7 bit or 2 for unicode')
    tag = fields.Char('Tag', size=256,
                      help='An optional tag')
    nostop = fields.Boolean(
        string= 'NoStop',
        help='Do not display STOP clause in the message, this requires that'
             'this is not an advertising message')


class Properties(models.Model):
    _name = 'sms.smsclient.parms'
    _description = 'SMS Client Properties'

    name = fields.Char(string='Property name', size=256,
                       help='Name of the property whom appear on the URL')
    value = fields.Char(string='Property value', size=256,
                        help='Value associate on the property for the URL')
    gateway_id = fields.Many2one(comodel_name='sms.smsclient',
                                 string='SMS Gateway')
    type = fields.Selection(
        selection=[('user', 'User'), ('password', 'Password'),
                   ('sender', 'Sender Name'), ('to', 'Recipient No'),
                   ('sms', 'SMS Message'), ('extra', 'Extra Info')],
        string='API Method', select=True,
        help='If parameter concern a value to substitute, indicate it')


class HistoryLine(models.Model):
    _name = 'sms.smsclient.history'
    _description = 'SMS Client History'

    @api.model
    def _get_default_user(self):
        return self.env.uid

    name = fields.Char(string='Description', size=160, required=True,
                       readonly=True)
    date_create = fields.Datetime(
        string='Date',
        readonly=True,
        default=fields.Datetime.now)
    user_id = fields.Many2one(comodel_name='res.users', string='Username',
                              readonly=True, select=True,
                              default=_get_default_user)
    gateway_id = fields.Many2one(
        comodel_name='sms.smsclient', string='SMS Gateway',
        help='Do not display STOP clause in the message, this requires that'
             ' this is not an advertising message',
        ondelete='set null', required=True)
    to = fields.Char(string='Mobile No', size=15, readonly=True)
    sms = fields.Text(string='SMS', size=160, readonly=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

import requests

from odoo import http
from odoo.http import request
from odoo.addons.kbt_api_base.controllers.main import KBTApiBase


class JournalController(KBTApiBase):

    @KBTApiBase.api_wrapper(['kbt.journal'])
    @http.route('/journal/create', type='json', auth='user')
    def journal_create_api(self, **params):
        try:
            self._create_journal(**params)
            return self._response_api(isSuccess=True)
        except requests.HTTPError as http_err:
            return self._response_api(message=str(http_err))
        except Exception as error:
            return self._response_api(message=str(error))

    def _create_journal(self, **params):
        AccountMove = request.env['account.move']
        AccountJour = request.env['account.journal']
        ResCurrency = request.env['res.currency']
        User = request.env.user

        currency_id = ResCurrency.search([('name', '=', params['currency'])])
        journal_id = AccountJour.search([
            ('code', '=', params['journal_code']),
            ('company_id', '=', User.company_id.id)])

        vals = {
            'ref': params['x_so_orderreference'],
            'date': params['account_date'],
            'move_type': 'entry',
            'currency_id': currency_id.id or False,
            'journal_id': journal_id.id or False,
            'x_is_interface': True,
        }
        line_vals_lst = [(0, 0, self._prepare_line_ids(order_line, User))
                         for order_line in params.get('lineItems')]
        vals['line_ids'] = line_vals_lst
        journal_entry = AccountMove.create(vals)
        journal_entry.action_post()

    def _prepare_line_ids(self, line, user_id):
        account_id = request.env['account.account'].search([
            ('code', '=', line['account_code']),
            ('deprecated', '=', False),
            ('company_id', '=', user_id.company_id.id)])
        return {
            'sequence': line['seq_line'],
            'account_id': account_id.id or False,
            'debit': line['debit_amount'],
            'credit': line['credit_amount']
        }

from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    commission_ids = fields.One2many(
        'nil.sales.commission',
        'lead_id',
        string='Sales Commissions',
    )

    commission_count = fields.Integer(
        string='Commission Count',
        compute='_compute_commission_count',
    )

    @api.depends('commission_ids')
    def _compute_commission_count(self):
        for lead in self:
            lead.commission_count = len(lead.commission_ids)

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        leads._nil_sync_invoice_commissions_from_lead()
        return leads

    def write(self, vals):
        result = super().write(vals)

        # IMPORTANT:
        # Every Lead edit refreshes its invoice-based commission rows.
        #
        # The invoice itself remains unchanged. The current CRM Lead is
        # the source of truth for salesperson/customer assignment.
        self._nil_sync_invoice_commissions_from_lead()

        return result

    def _nil_get_related_commission_invoices(self):
        """
        Return every invoice that belongs to these CRM Leads.

        We collect invoices in two ways:
        1. Through Sale Orders linked to the CRM Lead.
        2. Through existing commission rows already linked to the Lead.

        This lets the sync both update existing rows and recreate a pending
        row if the salesperson becomes eligible again.
        """
        if not self:
            return self.env['account.move']

        SaleOrder = self.env['sale.order'].sudo()
        Commission = self.env['nil.sales.commission'].sudo()

        sale_orders = SaleOrder.search([
            ('opportunity_id', 'in', self.ids),
        ])

        invoices_from_orders = sale_orders.mapped('invoice_ids')

        existing_commissions = Commission.search([
            ('lead_id', 'in', self.ids),
            ('invoice_id', '!=', False),
        ])

        invoices_from_commissions = existing_commissions.mapped('invoice_id')

        return (
            invoices_from_orders
            | invoices_from_commissions
        )

    def _nil_sync_invoice_commissions_from_lead(self):
        """
        Refresh commission rows from the CURRENT CRM Lead values.

        What changes dynamically from the Lead:
        - Salesperson
        - Customer
        - Commission rate
        - Commission amount

        What stays fixed from the Invoice:
        - Invoice reference
        - Invoice date
        - Invoice untaxed value
        - Currency

        Rates:
        - Ruba Khattam = 1.5%
        - Loudy Abdo = 5%
        - Baraa Abo Saleh = 2%

        If the Lead salesperson is changed to someone outside the approved
        list, an unpaid commission row is removed.

        Paid commission rows are NOT modified because their accounting
        journal entry is already posted.
        """
        invoices = self._nil_get_related_commission_invoices()

        if invoices:
            invoices._nil_sync_sales_commission()

        return True

    def action_view_sales_commission(self):
        self.ensure_one()

        action = self.env['ir.actions.actions']._for_xml_id(
            'nil_sales_commission.action_sales_commission'
        )

        action['domain'] = [
            ('lead_id', '=', self.id)
        ]

        action['context'] = {
            'default_lead_id': self.id,
            'default_salesperson_id':
                self.user_id.id if self.user_id else False,
            'default_customer_id':
                self.partner_id.id if self.partner_id else False,
        }

        commissions = self.commission_ids

        if len(commissions) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = commissions.id

        return action

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

    def action_view_sales_commission(self):
        self.ensure_one()

        action = self.env['ir.actions.actions']._for_xml_id(
            'nil_sales_commission.action_sales_commission'
        )
        action['domain'] = [('lead_id', '=', self.id)]
        action['context'] = {
            'default_lead_id': self.id,
            'default_salesperson_id': self.user_id.id if self.user_id else False,
            'default_customer_id': self.partner_id.id if self.partner_id else False,
        }

        commissions = self.commission_ids
        if len(commissions) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = commissions.id

        return action

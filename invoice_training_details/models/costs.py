# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from datetime import datetime
from odoo.exceptions import ValidationError

class TrainingCosts(models.Model):
    _name = "training.costs"
    _description = 'Training Costs'

    name = fields.Float(string='Cisco Cost',)
    price = fields.Float(string='Selling Price')
    move_id = fields.Many2one('account.move', string='Move')
    lead_id = fields.Many2one('crm.lead', string='Lead')
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order')

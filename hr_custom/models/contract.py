# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class HrContract(models.Model):
    _inherit = "hr.contract"
    
    basic_salary = fields.Float(string="Basic Salary")
    mobile_allowance = fields.Float(string="Mobile Allowance")
    transport_allowance = fields.Float(string="Transportation Allowance")
    housing_allowance = fields.Float(string="Housing allowance")
    schooling_allowance = fields.Float(string="Schooling Allowance")
    other_allowance = fields.Float(string="Other Allowance")
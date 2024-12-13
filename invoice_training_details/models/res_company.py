# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Company(models.Model):
    _inherit = "res.company"

    stamp = fields.Binary(string="Company Stamp", readonly=False)
    signature = fields.Binary(string="Company Signature", readonly=False)

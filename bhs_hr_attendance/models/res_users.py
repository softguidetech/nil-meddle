# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging


_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    restrict_attendance = fields.Boolean('Restrict attendance')

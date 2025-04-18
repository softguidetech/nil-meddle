# -*- coding: utf-8 -*-

from odoo import models, fields, tools, api, _
from datetime import datetime, timedelta
import pytz
from odoo.http import request
from odoo.exceptions import AccessError

class BHResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    hour_from = fields.Float(string='Work from', required=True, index=True,
                             help="Start and End time of working.\n"
                                  "A specific value of 24:00 is interpreted as 23:59:59.999999.")
    hour_to = fields.Float(string='Work to', required=True)
    break_from = fields.Float(string='Morning End Time', required=True)
    break_to = fields.Float(string='Afternoon Start Time', required=True)

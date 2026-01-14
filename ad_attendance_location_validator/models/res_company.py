from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    attendance_latitude = fields.Char(string="Attendance Latitude")
    attendance_longitude = fields.Char(string="Attendance Longitude")
    attendance_radius_km = fields.Float(string="Allowed Radius (km)", default=0.2)

    def update_coordinates(self, lat, lon):
        for company in self:
            company.attendance_latitude = str(lat)
            company.attendance_longitude = str(lon)

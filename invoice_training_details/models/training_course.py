from odoo import api, fields, models
from odoo.exceptions import ValidationError

class TrainingCourse(models.Model):
    _name = "training.course"
    _description = 'Training Course'

    name = fields.Char(string='Training Name')
    no_of_student = fields.Integer(string='# of Students')
    duration = fields.Integer(string='Duration (Days)', compute='_compute_date', store=True)
    training_date_start = fields.Date(string='Start Date')
    training_date_end = fields.Date(string='End Date')
    price = fields.Float(string='Selling Price')
    
    # Your other fields...

    @api.depends('training_date_start', 'training_date_end')
    def _compute_date(self):
        for rec in self:
            # Debugging logs
            if rec.training_date_start and rec.training_date_end:
                try:
                    # Check if both dates are valid date fields
                    start_date = fields.Date.from_string(rec.training_date_start)
                    end_date = fields.Date.from_string(rec.training_date_end)
                    rec.duration = (end_date - start_date).days
                except Exception as e:
                    rec.duration = 0
                    # Log the error for debugging
                    _logger.error(f"Error computing duration: {str(e)}")
            else:
                rec.duration = 0

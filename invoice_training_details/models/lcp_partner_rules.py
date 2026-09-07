# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import api, fields, models


class TrainingCourse(models.Model):
    _inherit = 'training.course'

    # Cash partner input is a per-seat amount.
    lcp_partner_cash_cost = fields.Monetary(
        string='Cost / Seat',
        currency_field='lcp_currency_id',
        default=0.0,
    )

    lcp_koenig_discount_pct = fields.Float(
        string='Koenig Discount %',
        compute='_compute_lcp_partner_breakdown',
    )
    lcp_koenig_discounted_seat_cost = fields.Monetary(
        string='Koenig Discounted Seat Cost',
        currency_field='lcp_currency_id',
        compute='_compute_lcp_partner_breakdown',
    )
    lcp_koenig_nil_return = fields.Monetary(
        string='NIL ME Return from Koenig Seats',
        currency_field='lcp_currency_id',
        compute='_compute_lcp_partner_breakdown',
    )

    def _koenig_cash_discount_pct(self):
        self.ensure_one()
        seats = max(self.no_of_student or 0, 0)
        if seats <= 0:
            return 0.0
        if seats <= 2:
            return 25.0
        if seats <= 5:
            return 30.0
        return 45.0

    @api.depends(
        'payment_method',
        'lcp_cost_learning_partner',
        'lcp_clcs_per_seat',
        'no_of_student',
        'lcp_instructor_source',
    )
    def _compute_lcp_partner_breakdown(self):
        for line in self:
            line.lcp_koenig_discount_pct = 0.0
            line.lcp_koenig_discounted_seat_cost = 0.0
            line.lcp_koenig_nil_return = 0.0

            if (
                line.payment_method != 'cash'
                or line.lcp_cost_learning_partner != 'Koenig'
            ):
                continue

            discount_pct = line._koenig_cash_discount_pct()
            discounted_seat_cost = (
                (line.lcp_clcs_per_seat or 0.0)
                * (1.0 - (discount_pct / 100.0))
            )
            total_discounted_seats = (
                discounted_seat_cost
                * max(line.no_of_student or 0, 0)
            )

            nil_return = 0.0
            if line.lcp_instructor_source == 'nil_me':
                nil_return = total_discounted_seats * 0.55

            line.lcp_koenig_discount_pct = discount_pct
            line.lcp_koenig_discounted_seat_cost = discounted_seat_cost
            line.lcp_koenig_nil_return = nil_return

    @api.depends(
        'training_date_start',
        'training_date_end',
        'duration',
        'no_of_student',
        'price',
        'payment_method',
        'location',
        'lcp_vat_rate',
        'lcp_clcs_per_seat',
        'lcp_rate_card_per_seat',
        'lcp_instructor_source',
        'lcp_instructor_md_rate',
        'lcp_vendor_instructor_day',
        'lcp_uber_day_rate',
        'lcp_per_diem_rate',
        'lcp_per_diem_days',
        'lcp_cost_learning_partner',
        'lcp_partner_share_pct',
        'lcp_partner_cash_cost',
        'lcp_venue_cost',
        'lcp_catering_cost',
        'lead_id.training_course_ids',
        'lead_id.ticket_ids.price',
        'lead_id.ticket_ids.lcp_training_course_id',
        'lead_id.hotel_ids.price',
        'lead_id.hotel_ids.lcp_training_course_id',
    )
    def _compute_lcp_per_training(self):
        # Keep every existing LCP calculation first, then replace only the
        # Cash partner portion requested here.
        super()._compute_lcp_per_training()

        for line in self:
            if line.payment_method != 'cash':
                continue

            seats = max(line.no_of_student or 0, 0)
            revenue = line.price or 0.0

            # Remove the old partner-share part calculated by the parent,
            # preserving instructor/logistics/venue/catering costs exactly.
            operational_costs = (
                (line.lcp_total_costs or 0.0)
                - (line.lcp_partner_share or 0.0)
            )

            partner_share = line.lcp_partner_share or 0.0

            if line.lcp_cost_learning_partner == 'EnterOne':
                # Cash + EnterOne: partner gives one Cost / Seat.
                # Partner invoice/share = Cost / Seat x number of seats.
                partner_share = (
                    (line.lcp_partner_cash_cost or 0.0)
                    * seats
                )

            elif line.lcp_cost_learning_partner == 'Koenig':
                # Cash + Koenig discount tiers:
                # 1-2 seats = 25%, 3-5 = 30%, 6+ = 45%.
                discount_pct = line._koenig_cash_discount_pct()
                discounted_seat_cost = (
                    (line.lcp_clcs_per_seat or 0.0)
                    * (1.0 - (discount_pct / 100.0))
                )
                discounted_total = discounted_seat_cost * seats

                if line.lcp_instructor_source == 'nil_me':
                    # 55% of the discounted seat cost returns to NIL ME.
                    # Therefore Koenig's payable share is the remaining 45%.
                    partner_share = discounted_total * 0.45
                else:
                    partner_share = discounted_total

            total_costs = operational_costs + partner_share
            profit = revenue - total_costs

            line.lcp_partner_share = partner_share
            line.lcp_total_costs = total_costs
            line.lcp_nilme_profit = profit
            line.lcp_profit_margin = (
                profit / revenue
                if revenue
                else 0.0
            )


class TicketTicket(models.Model):
    _inherit = 'ticket.ticket'

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.ref('base.USD'),
    )

    def _apply_training_defaults(self, vals):
        vals = dict(vals)
        usd = self.env.ref('base.USD')
        vals['currency_id'] = usd.id

        training_id = vals.get('lcp_training_course_id')
        lead_id = vals.get('ticket_lead_id')

        if not training_id and lead_id:
            lead = self.env['crm.lead'].browse(lead_id)
            onsite = lead.training_course_ids.filtered(
                lambda course: course.location == 'On site'
            )
            if len(onsite) == 1:
                training_id = onsite.id
                vals['lcp_training_course_id'] = training_id

        if training_id and 'date' not in vals:
            training = self.env['training.course'].browse(training_id)
            if training.training_date_start:
                vals['date'] = (
                    training.training_date_start - timedelta(days=1)
                )

        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([
            self._apply_training_defaults(vals)
            for vals in vals_list
        ])

    def write(self, vals):
        vals = dict(vals)
        vals['currency_id'] = self.env.ref('base.USD').id
        if 'lcp_training_course_id' in vals and vals['lcp_training_course_id']:
            training = self.env['training.course'].browse(
                vals['lcp_training_course_id']
            )
            if training.training_date_start:
                vals['date'] = (
                    training.training_date_start - timedelta(days=1)
                )
        return super().write(vals)

    @api.onchange('lcp_training_course_id')
    def _onchange_lcp_training_course_id_dates(self):
        for ticket in self:
            ticket.currency_id = self.env.ref('base.USD')
            training = ticket.lcp_training_course_id
            if training and training.training_date_start:
                ticket.date = (
                    training.training_date_start - timedelta(days=1)
                )


class HotelHotel(models.Model):
    _inherit = 'hotel.hotel'

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.ref('base.USD'),
    )

    def _apply_training_defaults(self, vals):
        vals = dict(vals)
        usd = self.env.ref('base.USD')
        vals['currency_id'] = usd.id

        training_id = vals.get('lcp_training_course_id')
        lead_id = vals.get('hotel_lead_id')

        if not training_id and lead_id:
            lead = self.env['crm.lead'].browse(lead_id)
            onsite = lead.training_course_ids.filtered(
                lambda course: course.location == 'On site'
            )
            if len(onsite) == 1:
                training_id = onsite.id
                vals['lcp_training_course_id'] = training_id

        if training_id:
            training = self.env['training.course'].browse(training_id)
            if training.training_date_start and 'date_from' not in vals:
                vals['date_from'] = (
                    training.training_date_start - timedelta(days=1)
                )
            if training.training_date_end and 'date_to' not in vals:
                vals['date_to'] = training.training_date_end

        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([
            self._apply_training_defaults(vals)
            for vals in vals_list
        ])

    def write(self, vals):
        vals = dict(vals)
        vals['currency_id'] = self.env.ref('base.USD').id
        if 'lcp_training_course_id' in vals and vals['lcp_training_course_id']:
            training = self.env['training.course'].browse(
                vals['lcp_training_course_id']
            )
            if training.training_date_start:
                vals['date_from'] = (
                    training.training_date_start - timedelta(days=1)
                )
            if training.training_date_end:
                vals['date_to'] = training.training_date_end
        return super().write(vals)

    @api.onchange('lcp_training_course_id')
    def _onchange_lcp_training_course_id_dates(self):
        for hotel in self:
            hotel.currency_id = self.env.ref('base.USD')
            training = hotel.lcp_training_course_id
            if not training:
                continue
            if training.training_date_start:
                hotel.date_from = (
                    training.training_date_start - timedelta(days=1)
                )
            if training.training_date_end:
                hotel.date_to = training.training_date_end

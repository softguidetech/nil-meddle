# -*- coding: utf-8 -*-

import math

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # =========================================================
    # LCP PRICING SETUP - MANUAL INPUTS
    # =========================================================

    lcp_vat_rate = fields.Float(
        string='VAT %',
        default=0.0,
        help='Enter VAT as a percentage, e.g. 15 for 15%.',
    )

    # IMPORTANT:
    # CLCs / Seat is a MANUAL LCP input.
    # It is NOT taken from Training, Extra Information, or any other field.
    lcp_clcs_per_seat = fields.Float(
        string='CLCs / Seat',
        default=0.0,
    )

    lcp_instructor_source = fields.Selection(
        [
            ('nil_me', 'NIL ME'),
            ('vendor', 'Vendor'),
        ],
        string='Instructor From',
        default='nil_me',
    )

    lcp_uber_day_rate = fields.Monetary(
        string='Uber / Day',
        currency_field='currency_id',
        default=33.0,
    )

    lcp_per_diem_rate = fields.Monetary(
        string='Per Diem / Day',
        currency_field='currency_id',
        default=35.0,
    )

    # IMPORTANT:
    # User enters the exact number of Per Diem days manually.
    lcp_per_diem_days = fields.Integer(
        string='Per Diem Days',
        default=0,
    )

    # =========================================================
    # TRAINING TOTALS
    # =========================================================

    lcp_total_days = fields.Integer(
        string='Total Training Days',
        compute='_compute_lcp_training_totals',
    )

    lcp_total_seats = fields.Integer(
        string='Total Seats',
        compute='_compute_lcp_training_totals',
    )

    lcp_total_clcs = fields.Float(
        string='Total CLCs',
        compute='_compute_lcp_training_totals',
    )

    lcp_total_clcs_with_vat = fields.Integer(
        string='Total CLCs + VAT',
        compute='_compute_lcp_training_totals',
    )

    lcp_total_rate_card = fields.Monetary(
        string='Total Rate Card',
        currency_field='currency_id',
        compute='_compute_lcp_training_totals',
    )

    lcp_total_instructor_cost = fields.Monetary(
        string='Total Instructor Cost',
        currency_field='currency_id',
        compute='_compute_lcp_training_totals',
    )

    lcp_total_per_diem = fields.Monetary(
        string='Total Per Diem',
        currency_field='currency_id',
        compute='_compute_lcp_training_totals',
    )

    lcp_total_uber_estimate = fields.Monetary(
        string='Uber Logistics',
        currency_field='currency_id',
        compute='_compute_lcp_training_totals',
    )

    # =========================================================
    # EXISTING LOGISTICS + COST DETAILS RESULTS
    # =========================================================

    lcp_ticket_total = fields.Monetary(
        string='Tickets',
        currency_field='currency_id',
        compute='_compute_lcp_existing_results',
    )

    lcp_hotel_total = fields.Monetary(
        string='Hotels',
        currency_field='currency_id',
        compute='_compute_lcp_existing_results',
    )

    lcp_total_logistics = fields.Monetary(
        string='Total Logistics',
        currency_field='currency_id',
        compute='_compute_lcp_existing_results',
    )

    lcp_cost_learning_partner = fields.Char(
        string='Learning Partner',
        compute='_compute_lcp_existing_results',
    )

    lcp_partner_share = fields.Monetary(
        string='Partner Share',
        currency_field='currency_id',
        compute='_compute_lcp_existing_results',
    )

    lcp_total_costs = fields.Monetary(
        string='Total Costs',
        currency_field='currency_id',
        compute='_compute_lcp_existing_results',
    )

    lcp_nilme_profit = fields.Monetary(
        string='NIL ME Profit',
        currency_field='currency_id',
        compute='_compute_lcp_existing_results',
    )

    lcp_profit_margin = fields.Float(
        string='Profit Margin',
        compute='_compute_lcp_existing_results',
    )

    lcp_cost_detail_count = fields.Integer(
        string='Cost Details Count',
        compute='_compute_lcp_existing_results',
    )

    @api.depends(
        'training_course_ids.training_date_start',
        'training_course_ids.training_date_end',
        'training_course_ids.duration',
        'training_course_ids.no_of_student',
        'training_course_ids.location',
        'training_course_ids.lcp_rate_card',
        'training_course_ids.lcp_instructor_rate_day',
        'payment_method',
        'lcp_clcs_per_seat',
        'lcp_vat_rate',
        'lcp_per_diem_rate',
        'lcp_per_diem_days',
        'lcp_uber_day_rate',
    )
    def _compute_lcp_training_totals(self):
        for lead in self:
            lines = lead.training_course_ids

            total_days = sum(
                line._lcp_get_days()
                for line in lines
            )

            total_seats = sum(
                max(line.no_of_student or 0, 0)
                for line in lines
            )

            # =====================================================
            # CLC CALCULATION
            #
            # CLCs / Seat is entered MANUALLY in LCP Pricing Setup.
            # It is NOT read from training.course.clcs_qty.
            #
            # Total CLCs = Manual CLCs / Seat x Total Seats
            #
            # Total CLCs + VAT:
            # 1) Calculate the GRAND TOTAL CLCs.
            # 2) Apply VAT to that GRAND TOTAL.
            # 3) ROUND UP ONCE at the very end.
            # =====================================================

            total_clcs = (
                (lead.lcp_clcs_per_seat or 0.0)
                * total_seats
                if lead.payment_method == 'clc'
                else 0.0
            )

            total_clcs_with_vat_raw = (
                total_clcs
                * (
                    1.0
                    + ((lead.lcp_vat_rate or 0.0) / 100.0)
                )
            )

            total_rate_card = sum(
                (line.lcp_rate_card or 0.0)
                * max(line.no_of_student or 0, 0)
                for line in lines
            )

            total_instructor_cost = sum(
                (line.lcp_instructor_rate_day or 0.0)
                * line._lcp_get_days()
                for line in lines
            )

            # =====================================================
            # PER DIEM
            #
            # User enters Per Diem Days manually.
            # Total Per Diem = Per Diem / Day x Manual Per Diem Days
            # It is NOT automatically multiplied by all training days.
            # =====================================================

            total_per_diem = (
                (lead.lcp_per_diem_rate or 0.0)
                * max(lead.lcp_per_diem_days or 0, 0)
            )

            # =====================================================
            # UBER
            #
            # Uber = Uber / Day x (TOTAL Training Days + 2)
            # Result is synchronized to existing CRM Logistics -> Uber.
            # =====================================================

            has_onsite_training = any(
                line.location == 'On site'
                for line in lines
            )

            total_uber = (
                (lead.lcp_uber_day_rate or 0.0)
                * (total_days + 2)
                if has_onsite_training and total_days > 0
                else 0.0
            )

            lead.lcp_total_days = total_days
            lead.lcp_total_seats = total_seats
            lead.lcp_total_clcs = total_clcs
            lead.lcp_total_clcs_with_vat = (
                int(math.ceil(total_clcs_with_vat_raw))
                if total_clcs_with_vat_raw > 0
                else 0
            )
            lead.lcp_total_rate_card = total_rate_card
            lead.lcp_total_instructor_cost = total_instructor_cost
            lead.lcp_total_per_diem = total_per_diem
            lead.lcp_total_uber_estimate = total_uber

    def _get_lcp_uber_amount(self):
        self.ensure_one()

        total_days = sum(
            line._lcp_get_days()
            for line in self.training_course_ids
        )

        has_onsite_training = any(
            line.location == 'On site'
            for line in self.training_course_ids
        )

        if not has_onsite_training or total_days <= 0:
            return 0.0

        return (
            (self.lcp_uber_day_rate or 0.0)
            * (total_days + 2)
        )

    def _sync_lcp_uber_to_logistics(self):
        """Write the calculated LCP Uber amount into the existing CRM Uber field."""
        for lead in self:
            amount = lead._get_lcp_uber_amount()

            if (lead.uber or 0.0) != amount:
                lead.with_context(
                    skip_lcp_uber_sync=True
                ).write({
                    'uber': amount,
                })

    @api.onchange(
        'lcp_uber_day_rate',
        'training_course_ids',
        'training_course_ids.training_date_start',
        'training_course_ids.training_date_end',
        'training_course_ids.duration',
        'training_course_ids.location',
    )
    def _onchange_lcp_uber(self):
        for lead in self:
            lead.uber = lead._get_lcp_uber_amount()

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        leads._sync_lcp_uber_to_logistics()
        return leads

    def write(self, vals):
        result = super().write(vals)

        if (
            not self.env.context.get('skip_lcp_uber_sync')
            and 'lcp_uber_day_rate' in vals
        ):
            self._sync_lcp_uber_to_logistics()

        return result

    @api.depends(
        'ticket_ids.price',
        'hotel_ids.price',
        'total_price_all',
        'venue',
        'ctrng',
        'uber',
        'cost_details_ids.learning_partner',
        'cost_details_ids.training_vendor',
        'cost_details_ids.total_price_all',
        'cost_details_ids.clc_cost',
        'cost_details_ids.ins_time',
        'cost_details_ids.margin1',
        'cost_details_ids.nilme_share',
        'cost_details_ids.margin',
        'total_training_price',
    )
    def _compute_lcp_existing_results(self):
        for lead in self:
            lead.lcp_ticket_total = sum(
                lead.ticket_ids.mapped('price')
            )

            lead.lcp_hotel_total = sum(
                lead.hotel_ids.mapped('price')
            )

            lead.lcp_total_logistics = (
                lead.total_price_all or 0.0
            )

            lead.lcp_cost_detail_count = len(
                lead.cost_details_ids
            )

            # Cost Details is lead-wide.
            # Mirror one existing Cost Details result to avoid duplication.
            cost_line = lead.cost_details_ids[:1]

            if cost_line:
                lead.lcp_cost_learning_partner = (
                    cost_line.learning_partner or ''
                )

                # IMPORTANT:
                # Partner Share comes from the EXISTING Cost Details engine.
                # LCP does not invent or duplicate the Partner Share formula.
                lead.lcp_partner_share = (
                    cost_line._get_effective_partner_share()
                )

                lead.lcp_total_costs = (
                    cost_line.margin1 or 0.0
                )

                lead.lcp_nilme_profit = (
                    cost_line.nilme_share or 0.0
                )

                lead.lcp_profit_margin = (
                    cost_line.margin or 0.0
                )

            else:
                lead.lcp_cost_learning_partner = ''
                lead.lcp_partner_share = 0.0
                lead.lcp_total_costs = 0.0
                lead.lcp_nilme_profit = 0.0
                lead.lcp_profit_margin = 0.0

    @api.constrains(
        'lcp_vat_rate',
        'lcp_clcs_per_seat',
        'lcp_uber_day_rate',
        'lcp_per_diem_rate',
        'lcp_per_diem_days',
    )
    def _check_lcp_setup_values(self):
        for lead in self:
            if lead.lcp_vat_rate < 0:
                raise ValidationError(
                    'VAT % cannot be negative.'
                )

            if lead.lcp_clcs_per_seat < 0:
                raise ValidationError(
                    'CLCs / Seat cannot be negative.'
                )

            if lead.lcp_uber_day_rate < 0:
                raise ValidationError(
                    'Uber / Day cannot be negative.'
                )

            if lead.lcp_per_diem_rate < 0:
                raise ValidationError(
                    'Per Diem / Day cannot be negative.'
                )

            if lead.lcp_per_diem_days < 0:
                raise ValidationError(
                    'Per Diem Days cannot be negative.'
                )


class TrainingCourse(models.Model):
    _inherit = 'training.course'

    lcp_currency_id = fields.Many2one(
        'res.currency',
        string='LCP Currency',
        related='lead_id.currency_id',
        readonly=True,
    )

    # =========================================================
    # LCP MANUAL PRICING INPUTS PER EXISTING TRAINING LINE
    # =========================================================

    lcp_rate_card = fields.Monetary(
        string='Rate Card / Seat',
        currency_field='lcp_currency_id',
    )

    lcp_instructor_rate_day = fields.Monetary(
        string='Instructor Rate / Day',
        currency_field='lcp_currency_id',
    )

    # =========================================================
    # LCP LINE RESULTS
    # CLC IS NOT HERE. CLCs / Seat is manual at CRM LCP Pricing Setup.
    # =========================================================

    lcp_days = fields.Integer(
        string='Days',
        compute='_compute_lcp_line_results',
    )

    lcp_total_rate_card = fields.Monetary(
        string='Total Rate Card',
        currency_field='lcp_currency_id',
        compute='_compute_lcp_line_results',
    )

    lcp_total_instructor_cost = fields.Monetary(
        string='Instructor Cost',
        currency_field='lcp_currency_id',
        compute='_compute_lcp_line_results',
    )

    def _lcp_get_days(self):
        self.ensure_one()

        if (
            self.training_date_start
            and self.training_date_end
        ):
            return max(
                (
                    self.training_date_end
                    - self.training_date_start
                ).days + 1,
                0,
            )

        if self.duration:
            first_token = (
                str(self.duration)
                .strip()
                .split(' ')[0]
            )

            try:
                return max(
                    int(float(first_token)),
                    0,
                )
            except (TypeError, ValueError):
                return 0

        return 0

    @api.depends(
        'training_date_start',
        'training_date_end',
        'duration',
        'no_of_student',
        'lcp_rate_card',
        'lcp_instructor_rate_day',
    )
    def _compute_lcp_line_results(self):
        for line in self:
            days = line._lcp_get_days()
            seats = max(line.no_of_student or 0, 0)

            line.lcp_days = days

            line.lcp_total_rate_card = (
                (line.lcp_rate_card or 0.0)
                * seats
            )

            line.lcp_total_instructor_cost = (
                (line.lcp_instructor_rate_day or 0.0)
                * days
            )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)

        lines.mapped(
            'lead_id'
        )._sync_lcp_uber_to_logistics()

        return lines

    def write(self, vals):
        leads_before = self.mapped('lead_id')

        result = super().write(vals)

        uber_fields = {
            'training_date_start',
            'training_date_end',
            'duration',
            'location',
            'lead_id',
        }

        if uber_fields.intersection(vals):
            (
                leads_before
                | self.mapped('lead_id')
            )._sync_lcp_uber_to_logistics()

        return result

    def unlink(self):
        leads = self.mapped('lead_id')
        result = super().unlink()
        leads._sync_lcp_uber_to_logistics()
        return result

    @api.constrains(
        'lcp_rate_card',
        'lcp_instructor_rate_day',
    )
    def _check_lcp_line_values(self):
        for line in self:
            if line.lcp_rate_card < 0:
                raise ValidationError(
                    'Rate Card / Seat cannot be negative.'
                )

            if line.lcp_instructor_rate_day < 0:
                raise ValidationError(
                    'Instructor Rate / Day cannot be negative.'
                )

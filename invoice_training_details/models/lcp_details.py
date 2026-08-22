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
    )

    # MANUAL ONLY.
    # This value is NOT taken from Training, Extra Information,
    # clcs_qty, cost_clc, or any other existing field.
    lcp_clcs_per_seat = fields.Float(
        string='CLCs / Seat',
        default=0.0,
    )

    # MANUAL ONLY inside LCP Pricing Setup.
    lcp_rate_card_per_seat = fields.Monetary(
        string='Rate Card / Seat',
        currency_field='currency_id',
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

    # NIL ME ONLY.
    # Manual daily MD amount, multiplied by TOTAL TRAINING DAYS.
    lcp_instructor_md_rate = fields.Monetary(
        string='Instructor MD',
        currency_field='currency_id',
        default=0.0,
    )

    # VENDOR ONLY.
    # Manual vendor instructor amount per training day.
    lcp_vendor_instructor_day = fields.Monetary(
        string='Vendor Instructor / Day',
        currency_field='currency_id',
        default=0.0,
    )

    lcp_uber_day_rate = fields.Monetary(
        string='Uber / Day',
        currency_field='currency_id',
        default=0.0,
    )

    # NIL ME ONLY.
    lcp_per_diem_rate = fields.Monetary(
        string='Per Diem / Day',
        currency_field='currency_id',
        default=0.0,
    )

    # NIL ME ONLY.
    # Manual number of Per Diem days, independent from training days.
    lcp_per_diem_days = fields.Integer(
        string='Per Diem Days',
        default=0,
    )

    # =========================================================
    # LCP CALCULATED TOTALS
    # =========================================================

    lcp_total_days = fields.Integer(
        string='Total Training Days',
        compute='_compute_lcp_totals',
    )

    lcp_total_seats = fields.Integer(
        string='Total Seats',
        compute='_compute_lcp_totals',
    )

    lcp_total_clcs = fields.Float(
        string='Total CLCs',
        compute='_compute_lcp_totals',
    )

    lcp_total_clcs_with_vat = fields.Integer(
        string='Total CLCs + VAT',
        compute='_compute_lcp_totals',
    )

    lcp_total_rate_card = fields.Monetary(
        string='Total Rate Card',
        currency_field='currency_id',
        compute='_compute_lcp_totals',
    )

    # Generic total instructor cost. This equals:
    # NIL ME -> Instructor MD x training days
    # Vendor -> Vendor Instructor / Day x training days
    lcp_total_instructor_cost = fields.Monetary(
        string='Instructor Cost',
        currency_field='currency_id',
        compute='_compute_lcp_totals',
    )

    lcp_total_instructor_md = fields.Monetary(
        string='Total Instructor MD',
        currency_field='currency_id',
        compute='_compute_lcp_totals',
    )

    lcp_total_vendor_instructor = fields.Monetary(
        string='Total Vendor Instructor',
        currency_field='currency_id',
        compute='_compute_lcp_totals',
    )

    lcp_total_per_diem = fields.Monetary(
        string='Total Per Diem',
        currency_field='currency_id',
        compute='_compute_lcp_totals',
    )

    lcp_total_uber_estimate = fields.Monetary(
        string='Uber Logistics',
        currency_field='currency_id',
        compute='_compute_lcp_totals',
    )

    # =========================================================
    # EXISTING LOGISTICS / COST DETAILS RESULTS
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

    # =========================================================
    # HELPERS
    # =========================================================

    def _lcp_training_days(self):
        self.ensure_one()

        total_days = 0

        for line in self.training_course_ids:
            if (
                line.training_date_start
                and line.training_date_end
            ):
                total_days += max(
                    (
                        line.training_date_end
                        - line.training_date_start
                    ).days + 1,
                    0,
                )
                continue

            if line.duration:
                first_token = (
                    str(line.duration)
                    .strip()
                    .split(' ')[0]
                )

                try:
                    total_days += max(
                        int(float(first_token)),
                        0,
                    )
                except (TypeError, ValueError):
                    pass

        return total_days

    @api.depends(
        'training_course_ids.training_date_start',
        'training_course_ids.training_date_end',
        'training_course_ids.duration',
        'training_course_ids.no_of_student',
        'lcp_vat_rate',
        'lcp_clcs_per_seat',
        'lcp_rate_card_per_seat',
        'lcp_instructor_source',
        'lcp_instructor_md_rate',
        'lcp_vendor_instructor_day',
        'lcp_uber_day_rate',
        'lcp_per_diem_rate',
        'lcp_per_diem_days',
    )
    def _compute_lcp_totals(self):
        for lead in self:
            total_days = lead._lcp_training_days()

            total_seats = sum(
                max(line.no_of_student or 0, 0)
                for line in lead.training_course_ids
            )

            # =====================================================
            # CLCs
            #
            # MANUAL CLCs / Seat x Total Seats
            #
            # Total CLCs + VAT:
            # 1) Calculate grand total CLCs.
            # 2) Apply VAT to the grand total.
            # 3) Round UP ONCE at the very end.
            # =====================================================

            total_clcs = (
                (lead.lcp_clcs_per_seat or 0.0)
                * total_seats
            )

            clcs_with_vat_raw = (
                total_clcs
                * (
                    1.0
                    + ((lead.lcp_vat_rate or 0.0) / 100.0)
                )
            )

            # =====================================================
            # RATE CARD
            # Manual Rate Card / Seat x Total Seats
            # =====================================================

            total_rate_card = (
                (lead.lcp_rate_card_per_seat or 0.0)
                * total_seats
            )

            # =====================================================
            # INSTRUCTOR COST
            #
            # NIL ME:
            #   Total Instructor MD =
            #   Instructor MD x Total Training Days
            #
            # Vendor:
            #   Total Vendor Instructor =
            #   Vendor Instructor / Day x Total Training Days
            # =====================================================

            if lead.lcp_instructor_source == 'nil_me':
                total_instructor_md = (
                    (lead.lcp_instructor_md_rate or 0.0)
                    * total_days
                )
                total_vendor_instructor = 0.0
                total_instructor_cost = total_instructor_md

                # Per Diem is ONLY for NIL ME.
                # Days are entered manually and are independent
                # from Total Training Days.
                total_per_diem = (
                    (lead.lcp_per_diem_rate or 0.0)
                    * max(lead.lcp_per_diem_days or 0, 0)
                )

            else:
                total_instructor_md = 0.0
                total_per_diem = 0.0

                total_vendor_instructor = (
                    (lead.lcp_vendor_instructor_day or 0.0)
                    * total_days
                )
                total_instructor_cost = total_vendor_instructor

            # =====================================================
            # UBER
            # Uber / Day x (Total Training Days + 2)
            # =====================================================

            total_uber = (
                (lead.lcp_uber_day_rate or 0.0)
                * (total_days + 2)
                if total_days > 0
                else 0.0
            )

            lead.lcp_total_days = total_days
            lead.lcp_total_seats = total_seats
            lead.lcp_total_clcs = total_clcs
            lead.lcp_total_clcs_with_vat = (
                int(math.ceil(clcs_with_vat_raw))
                if clcs_with_vat_raw > 0
                else 0
            )
            lead.lcp_total_rate_card = total_rate_card
            lead.lcp_total_instructor_md = total_instructor_md
            lead.lcp_total_vendor_instructor = total_vendor_instructor
            lead.lcp_total_instructor_cost = total_instructor_cost
            lead.lcp_total_per_diem = total_per_diem
            lead.lcp_total_uber_estimate = total_uber

    # =========================================================
    # UBER SYNC TO EXISTING LOGISTICS -> UBER
    # =========================================================

    def _get_lcp_uber_amount(self):
        self.ensure_one()

        total_days = self._lcp_training_days()

        if total_days <= 0:
            return 0.0

        return (
            (self.lcp_uber_day_rate or 0.0)
            * (total_days + 2)
        )

    def _sync_lcp_uber_to_logistics(self):
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

    # =========================================================
    # EXISTING COST DETAILS RESULT
    # =========================================================

    @api.depends(
        'ticket_ids.price',
        'hotel_ids.price',
        'cost_details_ids.learning_partner',
        'cost_details_ids.training_vendor',
        'cost_details_ids.margin1',
        'cost_details_ids.nilme_share',
        'cost_details_ids.margin',
        'cost_details_ids.ins_time',
        'total_training_price',
        'uber',
    )
    def _compute_lcp_existing_results(self):
        for lead in self:
            lead.lcp_ticket_total = sum(
                lead.ticket_ids.mapped('price')
            )

            lead.lcp_hotel_total = sum(
                lead.hotel_ids.mapped('price')
            )

            lead.lcp_cost_detail_count = len(
                lead.cost_details_ids
            )

            cost_line = lead.cost_details_ids[:1]

            if cost_line:
                # Learning Partner is taken ONLY from Cost Details.
                lead.lcp_cost_learning_partner = (
                    cost_line.learning_partner or ''
                )

                # Partner Share is taken from the SAME Cost Details engine.
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
        'lcp_rate_card_per_seat',
        'lcp_instructor_md_rate',
        'lcp_vendor_instructor_day',
        'lcp_uber_day_rate',
        'lcp_per_diem_rate',
        'lcp_per_diem_days',
    )
    def _check_lcp_values(self):
        for lead in self:
            values = [
                ('VAT %', lead.lcp_vat_rate),
                ('CLCs / Seat', lead.lcp_clcs_per_seat),
                ('Rate Card / Seat', lead.lcp_rate_card_per_seat),
                ('Instructor MD', lead.lcp_instructor_md_rate),
                ('Vendor Instructor / Day', lead.lcp_vendor_instructor_day),
                ('Uber / Day', lead.lcp_uber_day_rate),
                ('Per Diem / Day', lead.lcp_per_diem_rate),
                ('Per Diem Days', lead.lcp_per_diem_days),
            ]

            for label, value in values:
                if value < 0:
                    raise ValidationError(
                        '%s cannot be negative.' % label
                    )


class TrainingCourse(models.Model):
    _inherit = 'training.course'

    # =========================================================
    # BACKWARD-COMPATIBILITY FIELDS
    # Kept only so old stored LCP child views cannot break upgrade.
    # They are NOT used by the current CRM LCP calculation.
    # =========================================================

    lcp_currency_id = fields.Many2one(
        'res.currency',
        string='LCP Currency',
        related='lead_id.currency_id',
        readonly=True,
    )

    lcp_rate_card = fields.Monetary(
        string='Rate Card / Seat',
        currency_field='lcp_currency_id',
    )

    lcp_instructor_rate_day = fields.Monetary(
        string='Instructor Rate / Day',
        currency_field='lcp_currency_id',
    )

    lcp_days = fields.Integer(
        string='Days',
        compute='_compute_lcp_legacy_results',
    )

    lcp_total_rate_card = fields.Monetary(
        string='Total Rate Card',
        currency_field='lcp_currency_id',
        compute='_compute_lcp_legacy_results',
    )

    lcp_total_instructor_cost = fields.Monetary(
        string='Instructor Cost',
        currency_field='lcp_currency_id',
        compute='_compute_lcp_legacy_results',
    )

    @api.depends(
        'training_date_start',
        'training_date_end',
        'duration',
        'no_of_student',
        'lcp_rate_card',
        'lcp_instructor_rate_day',
    )
    def _compute_lcp_legacy_results(self):
        for line in self:
            days = 0

            if (
                line.training_date_start
                and line.training_date_end
            ):
                days = max(
                    (
                        line.training_date_end
                        - line.training_date_start
                    ).days + 1,
                    0,
                )

            elif line.duration:
                first_token = (
                    str(line.duration)
                    .strip()
                    .split(' ')[0]
                )

                try:
                    days = max(
                        int(float(first_token)),
                        0,
                    )
                except (TypeError, ValueError):
                    days = 0

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
        lines.mapped('lead_id')._sync_lcp_uber_to_logistics()
        return lines

    def write(self, vals):
        leads_before = self.mapped('lead_id')
        result = super().write(vals)

        if {
            'training_date_start',
            'training_date_end',
            'duration',
            'lead_id',
        }.intersection(vals):
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

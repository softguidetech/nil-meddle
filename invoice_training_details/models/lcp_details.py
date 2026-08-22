# -*- coding: utf-8 -*-

import math

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # =========================================================
    # LCP SETUP
    # =========================================================

    lcp_vat_rate = fields.Float(
        string='VAT %',
        default=0.0,
        help='Enter VAT as a normal percentage, e.g. 15 for 15%.',
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

    # =========================================================
    # LCP TRAINING TOTALS
    # =========================================================

    lcp_total_days = fields.Integer(
        string='Total Training Days',
        compute='_compute_lcp_training_totals',
    )

    lcp_total_seats = fields.Integer(
        string='Total Seats',
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
        string='Uber Estimate',
        currency_field='currency_id',
        compute='_compute_lcp_training_totals',
    )

    # =========================================================
    # EXISTING LOGISTICS
    # =========================================================

    lcp_ticket_total = fields.Monetary(
        string='Tickets',
        currency_field='currency_id',
        compute='_compute_lcp_existing_costs',
    )

    lcp_hotel_total = fields.Monetary(
        string='Hotels',
        currency_field='currency_id',
        compute='_compute_lcp_existing_costs',
    )

    # =========================================================
    # CURRENT COST DETAILS RESULT
    # =========================================================

    lcp_cost_learning_partner = fields.Char(
        string='Learning Partner',
        compute='_compute_lcp_existing_costs',
    )

    lcp_partner_share = fields.Monetary(
        string='Partner Share',
        currency_field='currency_id',
        compute='_compute_lcp_existing_costs',
    )

    lcp_total_costs = fields.Monetary(
        string='Total Costs',
        currency_field='currency_id',
        compute='_compute_lcp_existing_costs',
    )

    lcp_nilme_profit = fields.Monetary(
        string='NIL ME Profit',
        currency_field='currency_id',
        compute='_compute_lcp_existing_costs',
    )

    lcp_profit_margin = fields.Float(
        string='Profit Margin',
        compute='_compute_lcp_existing_costs',
    )

    lcp_cost_detail_count = fields.Integer(
        string='Cost Details Count',
        compute='_compute_lcp_existing_costs',
    )

    @api.depends(
        'training_course_ids.lcp_days',
        'training_course_ids.no_of_student',
        'training_course_ids.payment_method',
        'training_course_ids.clcs_qty',
        'training_course_ids.location',
        'training_course_ids.lcp_total_rate_card',
        'training_course_ids.lcp_total_instructor_cost',
        'training_course_ids.lcp_per_diem_total',
        'lcp_vat_rate',
        'lcp_uber_day_rate',
    )
    def _compute_lcp_training_totals(self):
        for lead in self:
            lines = lead.training_course_ids

            lead.lcp_total_days = sum(
                lines.mapped('lcp_days')
            )

            lead.lcp_total_seats = sum(
                lines.mapped('no_of_student')
            )

            # TOTAL CLCs + VAT:
            # VAT is applied to the GRAND TOTAL CLC quantity first,
            # then the final result is rounded UP once.
            #
            # Example:
            # 36 CLC / Seat × 6 Seats = 216
            # 216 × 1.15 = 248.4
            # Rounded UP = 249
            base_total_clcs = sum(
                (line.clcs_qty or 0.0)
                * max(line.no_of_student or 0, 0)
                for line in lines
                if line.payment_method == 'clc'
            )

            vat_multiplier = (
                1.0
                + ((lead.lcp_vat_rate or 0.0) / 100.0)
            )

            grand_total_clcs_with_vat = (
                base_total_clcs
                * vat_multiplier
            )

            lead.lcp_total_clcs_with_vat = (
                int(math.ceil(grand_total_clcs_with_vat))
                if grand_total_clcs_with_vat > 0
                else 0
            )

            lead.lcp_total_rate_card = sum(
                lines.mapped('lcp_total_rate_card')
            )

            lead.lcp_total_instructor_cost = sum(
                lines.mapped('lcp_total_instructor_cost')
            )

            lead.lcp_total_per_diem = sum(
                lines.mapped('lcp_per_diem_total')
            )

            # Uber is a deal-level logistics estimate:
            # Uber / Day × (Total Training Days + 2)
            #
            # The extra 2 days represent the travel days around the training.
            has_onsite_training = any(
                line.location == 'On site'
                for line in lines
            )

            lead.lcp_total_uber_estimate = (
                (lead.lcp_uber_day_rate or 0.0)
                * ((lead.lcp_total_days or 0) + 2)
                if has_onsite_training
                and lead.lcp_total_days
                else 0.0
            )

    def _get_lcp_uber_logistics_amount(self):
        self.ensure_one()

        days = sum(
            line._lcp_get_days()
            for line in self.training_course_ids
        )

        has_onsite_training = any(
            line.location == 'On site'
            for line in self.training_course_ids
        )

        if (
            not has_onsite_training
            or not days
        ):
            return 0.0

        return (
            (self.lcp_uber_day_rate or 0.0)
            * (days + 2)
        )

    def _sync_lcp_uber_to_logistics(self):
        """
        Keep the existing CRM Logistics -> Uber field synchronized
        with the LCP Uber / Day estimate.

        Uber = Uber / Day × (Total Training Days + 2)
        """
        for lead in self:
            amount = lead._get_lcp_uber_logistics_amount()

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
    def _onchange_lcp_uber_logistics(self):
        for lead in self:
            lead.uber = (
                lead._get_lcp_uber_logistics_amount()
            )

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)

        leads._sync_lcp_uber_to_logistics()

        return leads

    def write(self, vals):
        result = super().write(vals)

        if (
            not self.env.context.get(
                'skip_lcp_uber_sync'
            )
            and 'lcp_uber_day_rate' in vals
        ):
            self._sync_lcp_uber_to_logistics()

        return result

    @api.depends(
        'ticket_ids.price',
        'hotel_ids.price',
        'cost_details_ids.learning_partner',
        'cost_details_ids.training_vendor',
        'cost_details_ids.margin1',
        'cost_details_ids.nilme_share',
        'cost_details_ids.margin',
    )
    def _compute_lcp_existing_costs(self):
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

            # The current cost.details model calculates lead-wide logistics
            # inside each cost row. Summing multiple rows would therefore
            # duplicate the same costs. For the LCP summary we safely mirror
            # the first current Cost Details result and warn in the view if
            # more than one row exists.
            cost_line = lead.cost_details_ids[:1]

            if cost_line:
                lead.lcp_cost_learning_partner = (
                    cost_line.learning_partner or ''
                )

                lead.lcp_partner_share = (
                    cost_line.training_vendor or 0.0
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
        'lcp_uber_day_rate',
        'lcp_per_diem_rate',
    )
    def _check_lcp_setup_values(self):
        for lead in self:
            if lead.lcp_vat_rate < 0:
                raise ValidationError(
                    'VAT % cannot be negative.'
                )

            if lead.lcp_uber_day_rate < 0:
                raise ValidationError(
                    'Uber / Day cannot be negative.'
                )

            if lead.lcp_per_diem_rate < 0:
                raise ValidationError(
                    'Per Diem / Day cannot be negative.'
                )


class TrainingCourse(models.Model):
    _inherit = 'training.course'

    # Currency is inherited from the CRM Lead so all LCP money stays in the
    # same currency as the opportunity. Your CRM currently defaults it to USD.
    lcp_currency_id = fields.Many2one(
        'res.currency',
        string='LCP Currency',
        related='lead_id.currency_id',
        readonly=True,
    )

    # =========================================================
    # LCP INPUTS
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
    # LCP CALCULATIONS
    # =========================================================

    lcp_days = fields.Integer(
        string='Days',
        compute='_compute_lcp_values',
    )

    lcp_total_clcs_with_vat = fields.Integer(
        string='Total CLCs + VAT',
        compute='_compute_lcp_values',
        help=(
            'For CLC courses: '
            'ceil((CLCs / Seat × Seats) × (1 + VAT %)).'
        ),
    )

    lcp_total_rate_card = fields.Monetary(
        string='Total Rate Card',
        currency_field='lcp_currency_id',
        compute='_compute_lcp_values',
    )

    lcp_total_instructor_cost = fields.Monetary(
        string='Instructor Cost',
        currency_field='lcp_currency_id',
        compute='_compute_lcp_values',
    )

    lcp_per_diem_total = fields.Monetary(
        string='Per Diem',
        currency_field='lcp_currency_id',
        compute='_compute_lcp_values',
    )

    lcp_uber_total = fields.Monetary(
        string='Uber',
        currency_field='lcp_currency_id',
        compute='_compute_lcp_values',
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
            # Keeps compatibility with the existing Char field:
            # "5 days", "5", "5.0 days", etc.
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
        'clcs_qty',
        'lcp_rate_card',
        'lcp_instructor_rate_day',
        'location',
        'payment_method',
        'lead_id.lcp_vat_rate',
        'lead_id.lcp_instructor_source',
        'lead_id.lcp_per_diem_rate',
        'lead_id.lcp_uber_day_rate',
    )
    def _compute_lcp_values(self):
        for line in self:
            days = line._lcp_get_days()
            seats = max(
                line.no_of_student or 0,
                0,
            )

            line.lcp_days = days

            # -----------------------------------------------------
            # CLC + VAT
            # -----------------------------------------------------
            # IMPORTANT:
            # VAT is applied on the TOTAL CLC quantity, not per seat.
            #
            # Example:
            # 36 CLC / Seat × 6 Seats = 216 CLC
            # 216 × 1.15 = 248.4
            # Rounded UP = 249 CLC
            # -----------------------------------------------------
            if line.payment_method == 'clc':
                base_total_clcs = (
                    (line.clcs_qty or 0.0)
                    * seats
                )

                vat_multiplier = (
                    1.0
                    + (
                        (
                            line.lead_id.lcp_vat_rate
                            or 0.0
                        )
                        / 100.0
                    )
                )

                total_with_vat = (
                    base_total_clcs
                    * vat_multiplier
                )

                line.lcp_total_clcs_with_vat = (
                    int(math.ceil(total_with_vat))
                    if total_with_vat > 0
                    else 0
                )

            else:
                line.lcp_total_clcs_with_vat = 0

            # -----------------------------------------------------
            # RATE CARD
            # -----------------------------------------------------
            line.lcp_total_rate_card = (
                (line.lcp_rate_card or 0.0)
                * seats
            )

            # -----------------------------------------------------
            # INSTRUCTOR
            # -----------------------------------------------------
            line.lcp_total_instructor_cost = (
                (line.lcp_instructor_rate_day or 0.0)
                * days
            )

            onsite = (
                line.location == 'On site'
            )

            nil_me_instructor = (
                line.lead_id.lcp_instructor_source
                == 'nil_me'
            )

            # Per diem is an LCP estimate only for on-site delivery
            # with a NIL ME instructor. It does not change the current
            # cost.details engine at this stage.
            line.lcp_per_diem_total = (
                (
                    line.lead_id.lcp_per_diem_rate
                    or 0.0
                )
                * days
                if onsite and nil_me_instructor
                else 0.0
            )

            # Uber is calculated once at Lead / deal level as:
            # Uber / Day × (Total Training Days + 2)
            # and synchronized to the existing CRM Logistics -> Uber field.
            line.lcp_uber_total = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)

        lines.mapped('lead_id')._sync_lcp_uber_to_logistics()

        return lines

    def write(self, vals):
        leads_before = self.mapped('lead_id')

        result = super().write(vals)

        sync_fields = {
            'training_date_start',
            'training_date_end',
            'duration',
            'location',
            'lead_id',
        }

        if sync_fields.intersection(vals):
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

# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # =========================================================
    # LCP CONFIGURATION
    # =========================================================

    lcp_vat_rate = fields.Float(
        string='VAT %',
        default=0.0,
        help='Enter the VAT percentage as a normal number, e.g. 15 for 15%.',
    )

    lcp_instructor_source = fields.Selection(
        [
            ('nil_me', 'NIL ME'),
            ('vendor', 'Vendor'),
        ],
        string='Instructor From',
        default='nil_me',
    )

    lcp_uber_day_rate = fields.Float(
        string='Uber / Day',
        default=33.0,
    )

    lcp_per_diem_rate = fields.Float(
        string='Per Diem / Day',
        default=35.0,
    )

    # =========================================================
    # LCP COURSE TOTALS
    # =========================================================

    lcp_total_days = fields.Integer(
        string='Total Training Days',
        compute='_compute_lcp_course_totals',
    )

    lcp_total_clcs_with_vat = fields.Float(
        string='Total CLCs With VAT',
        compute='_compute_lcp_course_totals',
    )

    lcp_total_rate_card = fields.Float(
        string='Total Rate Card',
        compute='_compute_lcp_course_totals',
    )

    lcp_total_instructor_cost = fields.Float(
        string='Instructor Cost',
        compute='_compute_lcp_course_totals',
    )

    lcp_total_per_diem = fields.Float(
        string='Per Diem',
        compute='_compute_lcp_course_totals',
    )

    lcp_total_uber_estimate = fields.Float(
        string='Uber Estimate',
        compute='_compute_lcp_course_totals',
    )

    # =========================================================
    # EXISTING ODOO COST DATA
    # =========================================================

    lcp_ticket_total = fields.Float(
        string='Tickets',
        compute='_compute_lcp_existing_costs',
    )

    lcp_hotel_total = fields.Float(
        string='Hotel',
        compute='_compute_lcp_existing_costs',
    )

    lcp_learning_partner = fields.Char(
        string='Learning Partner',
        compute='_compute_lcp_existing_costs',
    )

    lcp_partner_share = fields.Float(
        string='Partner Share',
        compute='_compute_lcp_existing_costs',
    )

    lcp_total_costs = fields.Float(
        string='Total Costs',
        compute='_compute_lcp_existing_costs',
    )

    lcp_nilme_profit = fields.Float(
        string='NIL ME Profit',
        compute='_compute_lcp_existing_costs',
    )

    lcp_profit_margin = fields.Float(
        string='Profit Margin',
        compute='_compute_lcp_existing_costs',
    )

    lcp_sales_commission = fields.Float(
        string='Sales Commission',
        compute='_compute_lcp_existing_costs',
    )

    lcp_cost_detail_count = fields.Integer(
        string='Cost Detail Count',
        compute='_compute_lcp_existing_costs',
    )

    @api.depends(
        'training_course_ids.lcp_days',
        'training_course_ids.lcp_total_clcs_with_vat',
        'training_course_ids.lcp_total_rate_card',
        'training_course_ids.lcp_total_instructor_cost',
        'training_course_ids.lcp_per_diem_total',
        'training_course_ids.lcp_uber_total',
    )
    def _compute_lcp_course_totals(self):
        for lead in self:
            lines = lead.training_course_ids

            lead.lcp_total_days = sum(
                lines.mapped('lcp_days')
            )

            lead.lcp_total_clcs_with_vat = sum(
                lines.mapped('lcp_total_clcs_with_vat')
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

            lead.lcp_total_uber_estimate = sum(
                lines.mapped('lcp_uber_total')
            )

    @api.depends(
        'ticket_ids.price',
        'hotel_ids.price',
        'cost_details_ids.learning_partner',
        'cost_details_ids.training_vendor',
        'cost_details_ids.margin1',
        'cost_details_ids.nilme_share',
        'cost_details_ids.margin',
        'cost_details_ids.sales_commission',
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

            # Current Cost Details logic is lead-wide, so using the first
            # costing row is safer than summing multiple rows and duplicating
            # the same lead-level logistics/cost basis.
            cost_line = lead.cost_details_ids[:1]

            if cost_line:
                lead.lcp_learning_partner = (
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
                lead.lcp_sales_commission = (
                    cost_line.sales_commission or 0.0
                )
            else:
                lead.lcp_learning_partner = ''
                lead.lcp_partner_share = 0.0
                lead.lcp_total_costs = 0.0
                lead.lcp_nilme_profit = 0.0
                lead.lcp_profit_margin = 0.0
                lead.lcp_sales_commission = 0.0


class TrainingCourse(models.Model):
    _inherit = 'training.course'

    # =========================================================
    # LCP INPUTS
    # =========================================================

    lcp_rate_card = fields.Float(
        string='Rate Card / Seat',
        help='Commercial rate card per seat.',
    )

    lcp_instructor_rate_day = fields.Float(
        string='Instructor Rate / Day',
    )

    # =========================================================
    # LCP CALCULATIONS
    # =========================================================

    lcp_days = fields.Integer(
        string='Days',
        compute='_compute_lcp_values',
    )

    lcp_clcs_with_vat = fields.Float(
        string='CLCs / Seat With VAT',
        compute='_compute_lcp_values',
    )

    lcp_total_clcs_with_vat = fields.Float(
        string='Total CLCs With VAT',
        compute='_compute_lcp_values',
    )

    lcp_total_rate_card = fields.Float(
        string='Total Rate Card',
        compute='_compute_lcp_values',
    )

    lcp_total_instructor_cost = fields.Float(
        string='Instructor Cost',
        compute='_compute_lcp_values',
    )

    lcp_per_diem_total = fields.Float(
        string='Per Diem',
        compute='_compute_lcp_values',
    )

    lcp_uber_total = fields.Float(
        string='Uber',
        compute='_compute_lcp_values',
    )

    @api.depends(
        'training_date_start',
        'training_date_end',
        'duration',
        'no_of_student',
        'clcs_qty',
        'lcp_rate_card',
        'lcp_instructor_rate_day',
        'location',
        'lead_id.lcp_vat_rate',
        'lead_id.lcp_instructor_source',
        'lead_id.lcp_per_diem_rate',
        'lead_id.lcp_uber_day_rate',
    )
    def _compute_lcp_values(self):
        for line in self:
            days = 0

            if (
                line.training_date_start
                and line.training_date_end
            ):
                days = (
                    line.training_date_end
                    - line.training_date_start
                ).days + 1

            elif line.duration:
                # Keeps compatibility with the current Char field
                # such as "5 days".
                first_token = str(line.duration).strip().split(' ')[0]
                try:
                    days = int(float(first_token))
                except (TypeError, ValueError):
                    days = 0

            vat_rate = (
                (line.lead_id.lcp_vat_rate or 0.0)
                / 100.0
            )

            clcs_per_seat = (
                line.clcs_qty or 0.0
            )

            clcs_with_vat = (
                clcs_per_seat
                * (1.0 + vat_rate)
            )

            line.lcp_days = days

            line.lcp_clcs_with_vat = (
                clcs_with_vat
            )

            line.lcp_total_clcs_with_vat = (
                clcs_with_vat
                * (line.no_of_student or 0)
            )

            line.lcp_total_rate_card = (
                (line.lcp_rate_card or 0.0)
                * (line.no_of_student or 0)
            )

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

            line.lcp_per_diem_total = (
                (line.lead_id.lcp_per_diem_rate or 0.0)
                * days
                if onsite and nil_me_instructor
                else 0.0
            )

            line.lcp_uber_total = (
                (line.lead_id.lcp_uber_day_rate or 0.0)
                * days
                if onsite
                else 0.0
            )

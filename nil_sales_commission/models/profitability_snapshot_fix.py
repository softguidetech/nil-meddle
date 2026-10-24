# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SalesCommission(models.Model):
    _inherit = 'nil.sales.commission'

    # Read-only presentation fields. All financial numbers below come from
    # the existing LCP results; nothing is recomputed or written to LCP.
    profit_total_rate_card = fields.Float(
        string='Total Rate Card',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )
    profit_partner_share = fields.Float(
        string='Partner Share',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )
    profit_instructor_cost = fields.Float(
        string='Instructor Cost',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )
    profit_logistics_cost = fields.Float(
        string='Total Logistics',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )
    profit_ticket_cost = fields.Float(
        string='Tickets',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )
    profit_hotel_cost = fields.Float(
        string='Hotels',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )
    profit_per_diem_cost = fields.Float(
        string='Per Diem',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )
    profit_uber_cost = fields.Float(
        string='Uber',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )
    profit_venue_cost = fields.Float(
        string='Venue',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )
    profit_catering_cost = fields.Float(
        string='Catering',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )

    profit_lcp_source = fields.Char(
        string='LCP Source',
        compute='_compute_profit_margin_summary',
        compute_sudo=True,
    )

    @api.depends(
        'invoice_id',
        'invoice_id.training_course_ids',
        'invoice_id.training_course_ids.source_training_course_id',
        'invoice_id.training_course_ids.snapshot_lcp_total_costs',
        'invoice_id.training_course_ids.snapshot_lcp_profit',
        'invoice_id.training_course_ids.snapshot_lcp_revenue',
        'lead_id',
        'lead_id.cost_details_ids.margin1',
        'lead_id.cost_details_ids.nilme_share',
        'lead_id.cost_details_ids.margin',
        'lead_id.cost_details_ids.learning_partner',
        'lead_id.training_course_ids',
        'lead_id.training_course_ids.lcp_total_rate_card',
        'lead_id.training_course_ids.lcp_cost_learning_partner',
        'lead_id.training_course_ids.lcp_total_costs',
        'lead_id.training_course_ids.lcp_nilme_profit',
        'lead_id.training_course_ids.lcp_profit_margin',
        'lead_id.training_course_ids.lcp_partner_share',
        'lead_id.training_course_ids.lcp_total_instructor_cost',
        'lead_id.training_course_ids.lcp_total_logistics',
        'lead_id.training_course_ids.lcp_ticket_total',
        'lead_id.training_course_ids.lcp_hotel_total',
        'lead_id.training_course_ids.lcp_total_per_diem',
        'lead_id.training_course_ids.lcp_total_uber_estimate',
        'lead_id.training_course_ids.lcp_venue_cost',
        'lead_id.training_course_ids.lcp_catering_cost',
        'lead_id.training_course_ids.price',
    )
    def _compute_profit_margin_summary(self):
        """
        Prefer the original CRM training LCP results, linked from the invoice
        snapshots. Older snapshots may have frozen zero costs, so they must
        never mask complete, up-to-date source LCP figures.

        If an invoice has no course link, use its CRM lead LCP values. The
        underlying LCP calculations remain untouched.
        """
        for rec in self:
            invoice_courses = (
                rec.invoice_id.sudo().training_course_ids
                if rec.invoice_id
                else self.env['training.course']
            )
            source_courses = invoice_courses.mapped(
                'source_training_course_id'
            ).exists()
            lead = (
                rec.lead_id.sudo()
                if rec.lead_id
                else rec.invoice_id._nil_get_commission_lead().sudo()
                if rec.invoice_id
                else self.env['crm.lead']
            )
            lead_courses = (
                lead.training_course_ids.sudo()
                if lead
                else self.env['training.course']
            )
            courses = source_courses or lead_courses or invoice_courses
            source_label = (
                'Original CRM LCP'
                if source_courses
                else 'CRM LCP'
                if lead_courses
                else 'Invoice LCP'
                if invoice_courses
                else 'No linked LCP'
            )

            if courses:
                partners = sorted(set(
                    courses.mapped('lcp_cost_learning_partner')
                ) - {False, ''})
                revenue = sum(courses.mapped('price'))
                costs = sum(courses.mapped('lcp_total_costs'))
                profit = sum(courses.mapped('lcp_nilme_profit'))
                rate_card = sum(courses.mapped('lcp_total_rate_card'))
                partner_share = sum(courses.mapped('lcp_partner_share'))
                instructor = sum(courses.mapped('lcp_total_instructor_cost'))
                logistics = sum(courses.mapped('lcp_total_logistics'))
                tickets = sum(courses.mapped('lcp_ticket_total'))
                hotels = sum(courses.mapped('lcp_hotel_total'))
                per_diem = sum(courses.mapped('lcp_total_per_diem'))
                uber = sum(courses.mapped('lcp_total_uber_estimate'))
                venue = sum(courses.mapped('lcp_venue_cost'))
                catering = sum(courses.mapped('lcp_catering_cost'))
                # Single-training: display the original LCP margin verbatim.
                # Multi-training: preserve the existing aggregate margin.
                margin = (
                    courses.lcp_profit_margin
                    if len(courses) == 1
                    else (profit / revenue if revenue else 0.0)
                )
                # Pre-per-training LCP leads may hold the populated results
                # at the CRM lead level, while legacy training copies are 0.
                if lead and not costs and lead.lcp_total_costs:
                    costs = lead.lcp_total_costs
                    profit = lead.lcp_nilme_profit
                    margin = lead.lcp_profit_margin
                    partner_share = lead.lcp_partner_share
                    instructor = lead.lcp_total_instructor_cost
                    logistics = lead.lcp_total_logistics
                    tickets = lead.lcp_ticket_total
                    hotels = lead.lcp_hotel_total
                    per_diem = lead.lcp_total_per_diem
                    uber = lead.lcp_total_uber_estimate
                    if not rate_card:
                        rate_card = lead.lcp_total_rate_card
                    if not partners and lead.lcp_cost_learning_partner:
                        partners = [lead.lcp_cost_learning_partner]
            elif lead:
                partners = [lead.lcp_cost_learning_partner] if lead.lcp_cost_learning_partner else []
                costs = lead.lcp_total_costs
                profit = lead.lcp_nilme_profit
                rate_card = lead.lcp_total_rate_card
                partner_share = lead.lcp_partner_share
                instructor = lead.lcp_total_instructor_cost
                logistics = lead.lcp_total_logistics
                tickets = lead.lcp_ticket_total
                hotels = lead.lcp_hotel_total
                per_diem = lead.lcp_total_per_diem
                uber = lead.lcp_total_uber_estimate
                venue = 0.0
                catering = 0.0
                margin = lead.lcp_profit_margin
            else:
                partners = []
                costs = profit = rate_card = partner_share = 0.0
                instructor = logistics = tickets = hotels = 0.0
                per_diem = uber = venue = catering = margin = 0.0

            # Recover frozen invoice financials only when the chosen live
            # LCP source has no expenses. Never overwrite a nonzero live LCP.
            frozen = invoice_courses.filtered(
                lambda course: (
                    bool(course.snapshot_lcp_total_costs)
                    or bool(course.snapshot_lcp_rate_card)
                    or bool(course.snapshot_lcp_profit)
                )
            )
            if frozen and not costs and any(
                course.snapshot_lcp_total_costs for course in frozen
            ):
                costs = sum(frozen.mapped('snapshot_lcp_total_costs'))
                profit = sum(frozen.mapped('snapshot_lcp_profit'))
                partner_share = sum(frozen.mapped('snapshot_lcp_partner_share'))
                logistics = sum(frozen.mapped('snapshot_lcp_logistics'))
                frozen_rate = sum(frozen.mapped('snapshot_lcp_rate_card'))
                if frozen_rate:
                    rate_card = frozen_rate
                frozen_revenue = sum(frozen.mapped('snapshot_lcp_revenue'))
                margin = profit / frozen_revenue if frozen_revenue else 0.0
                frozen_partners = sorted(set(
                    frozen.mapped('snapshot_lcp_learning_partner')
                ) - {False, ''})
                if frozen_partners:
                    partners = frozen_partners
                source_label = 'Invoice LCP snapshot'

            # Older LCP versions stored the completed margin in cost.details.
            # This fallback reads its already computed values, never sums
            # duplicate lead-wide cost rows or changes their formulas.
            if lead and not costs and lead.cost_details_ids:
                legacy = lead.sudo().cost_details_ids.filtered(
                    lambda detail: bool(detail.margin1)
                )[:1]
                if legacy:
                    costs = legacy.margin1
                    profit = legacy.nilme_share
                    margin = legacy.margin
                    partner_share = legacy.training_vendor
                    instructor = legacy.ins_time
                    logistics = legacy.total_price_all
                    if legacy.learning_partner:
                        partners = [legacy.learning_partner]
                    source_label = 'Legacy LCP cost details'

            rec.profit_lcp_source = source_label
            rec.profit_learning_partner = ', '.join(partners)
            rec.profit_total_costs = costs
            rec.profit_nilme_share = profit
            rec.profit_margin_pct = margin
            rec.profit_total_rate_card = rate_card
            rec.profit_partner_share = partner_share
            rec.profit_instructor_cost = instructor
            rec.profit_logistics_cost = logistics
            rec.profit_ticket_cost = tickets
            rec.profit_hotel_cost = hotels
            rec.profit_per_diem_cost = per_diem
            rec.profit_uber_cost = uber
            rec.profit_venue_cost = venue
            rec.profit_catering_cost = catering

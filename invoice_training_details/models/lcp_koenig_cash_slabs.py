# -*- coding: utf-8 -*-

from odoo import models


class TrainingCourse(models.Model):
    _inherit = 'training.course'

    def _koenig_cash_discount_pct(self):
        """Koenig Cash discount is chosen by total seat count and applies to every seat.

        Exactly 2 seats: 25% discount on every seat.
        3 to 5 seats: 30% discount on every seat.
        6+ seats: 45% discount on every seat.
        1 seat: no automatic discount.
        """
        self.ensure_one()
        seats = max(self.no_of_student or 0, 0)
        if seats == 2:
            return 25.0
        if 3 <= seats <= 5:
            return 30.0
        if seats >= 6:
            return 45.0
        return 0.0

    def _koenig_cash_discounted_total(self):
        self.ensure_one()
        seats = max(self.no_of_student or 0, 0)
        seat_rate = self.lcp_clcs_per_seat or 0.0
        discount_pct = self._koenig_cash_discount_pct()
        return seat_rate * seats * (1.0 - discount_pct / 100.0)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def _lcp_koenig_po_terms(self, courses):
        blocks = []
        for course in courses:
            seats = max(course.no_of_student or 0, 0)
            seat_rate = course.lcp_clcs_per_seat or 0.0
            discount_pct = course._koenig_cash_discount_pct()
            discounted_total = course._koenig_cash_discounted_total()
            nil_return = (
                discounted_total * 0.55
                if course.lcp_instructor_source == 'nil_me'
                else 0.0
            )
            koenig_invoice = (
                discounted_total * 0.45
                if course.lcp_instructor_source == 'nil_me'
                else discounted_total
            )

            rows = [
                ('USD / Seat', self._lcp_money(seat_rate), False),
                ('Seats', str(seats), False),
                ('Discount', '{:.0f}% on every seat'.format(discount_pct), True),
                ('Discounted Total', self._lcp_money(discounted_total), True),
            ]
            if course.lcp_instructor_source == 'nil_me':
                rows.append((
                    'NIL ME Return 55%',
                    self._lcp_money(nil_return),
                    False,
                ))
            rows.append((
                'Koenig Invoice',
                self._lcp_money(koenig_invoice),
                True,
            ))

            blocks.append(self._lcp_html_table('', rows))
        return ''.join(blocks)

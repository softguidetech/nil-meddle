# -*- coding: utf-8 -*-

from odoo import models


class TrainingCourse(models.Model):
    _inherit = 'training.course'

    def _koenig_cash_discounted_total(self):
        self.ensure_one()
        seats = max(self.no_of_student or 0, 0)
        seat_rate = self.lcp_clcs_per_seat or 0.0

        first_two = min(seats, 2)
        seats_3_to_5 = min(max(seats - 2, 0), 3)
        seats_6_plus = max(seats - 5, 0)

        return (
            first_two * seat_rate * 0.75
            + seats_3_to_5 * seat_rate * 0.70
            + seats_6_plus * seat_rate * 0.55
        )

    def _koenig_cash_discount_pct(self):
        """Effective discount equivalent to the Koenig seat slabs.

        First 2 seats: 25% discount (pay 75%).
        Seats 3-5: 30% discount (pay 70%).
        Seat 6 onward: 45% discount (pay 55%).

        Returning the weighted/effective percentage keeps the existing
        downstream calculations correct without flattening the actual slabs.
        """
        self.ensure_one()
        seats = max(self.no_of_student or 0, 0)
        seat_rate = self.lcp_clcs_per_seat or 0.0
        gross = seat_rate * seats
        if gross <= 0:
            return 0.0
        discounted_total = self._koenig_cash_discounted_total()
        return max(0.0, min(100.0, (1.0 - discounted_total / gross) * 100.0))


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def _lcp_koenig_po_terms(self, courses):
        blocks = []
        for course in courses:
            seats = max(course.no_of_student or 0, 0)
            seat_rate = course.lcp_clcs_per_seat or 0.0
            discounted_total = course._koenig_cash_discounted_total()
            nil_return = discounted_total * 0.55 if course.lcp_instructor_source == 'nil_me' else 0.0
            koenig_invoice = discounted_total * 0.45 if course.lcp_instructor_source == 'nil_me' else discounted_total

            rows = [
                ('USD / Seat', self._lcp_money(seat_rate), False),
                ('Seats', str(seats), False),
            ]
            if seats:
                rows.append(('First 2 Seats', '25% discount', False))
            if seats > 2:
                rows.append(('Seats 3-5', '30% discount', False))
            if seats > 5:
                rows.append(('Seats 6+', '45% discount', False))
            rows.extend([
                ('Discounted Total', self._lcp_money(discounted_total), True),
            ])
            if course.lcp_instructor_source == 'nil_me':
                rows.append(('NIL ME Return 55%', self._lcp_money(nil_return), False))
            rows.append(('Koenig Invoice', self._lcp_money(koenig_invoice), True))

            blocks.append(self._lcp_html_table('', rows))
        return ''.join(blocks)

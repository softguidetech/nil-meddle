{
    'name': 'NIL Sales Commission',
    'version': '17.0.2.1.1',
    'category': 'CRM',
    'summary': 'Invoice-based sales commission ledger',
    'description': """
NIL Sales Commission
====================
- Creates one commission record per posted customer invoice dated after 31-May-2026.
- Automatically backfills existing eligible invoices on module install/upgrade.
- Commission is calculated on the LCP Total Rate Card, not invoice revenue.
- Pending commissions have no accounting entry.
- Marking a commission as Paid creates and posts the accounting journal entry.
- Ruba is excluded from new commission rows and all commission views.
- LCP profit margin and expense breakdown is shown read-only in the ledger.
- Detailed commission ledger and pivot analysis.
- Access is restricted to the dedicated NIL Commission Manager group.
    """,
    'author': 'NIL ME',
    'license': 'LGPL-3',
    'depends': [
        'crm',
        'sale_crm',
        'account',
        'invoice_training_details',
    ],
    'data': [
        'security/commission_security.xml',
        'security/ir.model.access.csv',
        'data/commission_sequence.xml',
        'data/commission_backfill.xml',
        'views/sales_commission_views.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

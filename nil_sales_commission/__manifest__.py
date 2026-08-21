{
    'name': 'NIL Sales Commission',
    'version': '17.0.1.1.0',
    'category': 'CRM',
    'summary': 'Sales commission ledger linked to CRM opportunities',
    'description': """
NIL Sales Commission
====================
- Creates one commission record per CRM opportunity only after a customer invoice is posted.
- Commission is 5% of the opportunity total training value.
- Pending commissions have no accounting entry.
- Marking a commission as Paid creates and posts the accounting journal entry.
- Detailed commission ledger and pivot analysis.
- Access is restricted to the dedicated NIL Commission Manager group.
    """,
    'author': 'NIL ME',
    'license': 'LGPL-3',
    'depends': [
        'crm',
        'sale_crm',
        'account',
    ],
    'data': [
        'security/commission_security.xml',
        'security/ir.model.access.csv',
        'data/commission_sequence.xml',
        'views/sales_commission_views.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

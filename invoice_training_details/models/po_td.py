from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    training_course_ids = fields.One2many(
        'training.course', 'purchase_id', string="Training Courses"
    )
<odoo>
    <record id="view_purchase_order_form_training" model="ir.ui.view">
        <field name="name">purchase.order.form.training</field>
        <field name="model">purchase.order</field>
        <field name="inherit_id" ref="purchase.purchase_order_form"/>
        <field name="arch" type="xml">
            <xpath expr="//sheet" position="inside">
                <group>
                    <field name="training_course_ids">
                        <tree editable="bottom">
                            <field name="name"/>
                            <field name="training_date_start"/>
                            <field name="training_date_end"/>
                            <field name="duration"/>
                            <field name="price"/>
                        </tree>
                    </field>
                </group>
            </xpath>
        </field>
    </record>
</odoo>

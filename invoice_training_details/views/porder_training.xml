<?xml version="1.0"?>
<odoo>
    <record id="purchase_order_form_inherit_training" model="ir.ui.view">
        <field name="name">purchase.order.form.inherit.training</field>
        <field name="model">purchase.order</field>
        <field name="inherit_id" ref="purchase.view_purchase_order_form"/>
        <field name="arch" type="xml">
            <page name="order_lines" position="after">
                <page id="training" name="Training">
                    <group>
                        <!-- Add instructor field and sync button -->
                        <field name="instructor_id"/> 
                        <button name="synch_order" string="Synch Order" class="oe_highlight" type="object"/>
                    </group>

                    <!-- Tree view for training courses -->
                    <field name="training_ids">
                        <tree editable="bottom">
                            <field name="training_id"/>
                            <field name="cost_clc"/>
                            <field name="hyperlink"/>
                            <field name="instructor_id"/>
                            <field name="train_language"/>
                            <field name="location"/>
                            <field name="where_location2"/>
                            <field name="payment_method"/>
                            <field name="no_of_student"/>
                            <field name="duration"/>
                            <field name="training_date_start"/>
                            <field name="training_date_end"/>
                            <field name="price"/>
                        </tree>
                    </field>

                    <!-- Group for additional details -->
                    <group>
                        <group>
                            <field name="total_training_price"/>
                        </group>
                        <group>
                            <field name="bank_details"/>
                            <field name="term_and_cond"/>
                        </group>
                    </group>

                    <!-- Group for report-related fields -->
                    <group>
                        <group string="Report PDF Element Display">
                            <field name="display_training_table"/>
                            <field name="display_signature"/>
                            <field name="display_stamp"/>
                        </group>
                        <group string="Column Display">
                            <field name="display_instructor"/>
                            <field name="display_location"/>
                            <field name="display_downpayment"/>
                            <field name="display_total"/>
                            <field name="display_due_amount"/>
                            <field name="display_where"/>
                            <field name="display_description"/>
                        </group>
                    </group>
                </page>
            </page>
        </field>
    </record>
</odoo>

from odoo import models, fields, api, _
from odoo.exceptions import Warning
import logging

log = logging.getLogger(__name__)

class HandleType(models.Model):
    _name = 'flex_print.handle_type'
    _description = "Product handle type"
    _order = 'name ASC'
    
    name = fields.Char()
    handle_attributes_ids = fields.One2many('flex_print.handle_atts', 'handle_type_id', 'Handle Attributes')

class SealType(models.Model):
    _name = 'flex_print.seal_type'
    _description = "Product seal type"
    _order = 'name ASC'
    
    name = fields.Char()    

class HandleAttributes(models.Model):
    _name = 'flex_print.handle_atts'
    _description = "Product handle type attributes"
    _order = 'name ASC'
    
    name = fields.Char()    
    handle_type_id = fields.Many2one('flex_print.handle_type', 'Handle Type')

class LayerType(models.Model):
    _name = 'flex_print.layer_type'
    _description = "Product layer type"
    _order = 'name ASC'
    
    name = fields.Char()   
    thickness = fields.Float(string='Thickness')
    density = fields.Float(string='Density')

class OppotunityHandleAttributesVals(models.Model):
    _name = 'flex_print.opp_h_values'
    _description = "Opportunity product handle type attributes values"
    
    opp_id = fields.Many2one('crm.lead', 'Opportunity')
    handle_attribute_id = fields.Many2one('flex_print.handle_atts', 'Handle Attributes Ids')
    value = fields.Char()

class ProductPrinting(models.Model):
    _name = "flex_print.product_printing_params"  
    _description = "Product printing parameters"
    
    print_direction_values = [('top_print', 'Top Print'), ('reverse_print', 'Reverse print')]
    
    name = fields.Char(required=True) 
    cylinder_size = fields.Float()
    cylinder_width = fields.Float()
    cylinder_length = fields.Float()
    resolution = fields.Float()
    thickness = fields.Float()
    color = fields.Char()
    hash_color = fields.Char()
    direction = fields.Selection(print_direction_values)
    barcode = fields.Char()
    location = fields.Char()
    repeated_print_direction_number = fields.Integer()
    cylinder_line_number = fields.Integer()
    supplier = fields.Many2one('res.partner', string='Supplier')
    
    product_id = fields.Many2one('product.template', 'Product', ondelete="cascade")

class ProductOption(models.Model):
    _name = "flex_print.product_option"
    _description = "Product options"
    
    name = fields.Char(required=True) 
    
class CrmLeadInherited(models.Model):
    _inherit = 'crm.lead'
     
    @api.multi
    def create_new_product(self):
        """
        Create a new product if not repeated
        """
        self.ensure_one()
        
        active_lead = self.env['crm.lead'].browse(self._context.get('active_id'))
        if active_lead.repeated_product:
            raise Warning(_("You can't create a new product (Please select from the repeated one's)."))
            
        return {'type': 'ir.actions.act_window',
                'res_model': 'product.template',
                'view_mode': 'form',
                'view_id': self.env.ref('flexible_printing.inherit_product_template').id,
                'target': 'new', 
                'res_id': active_lead.inquiry_product.id, 
                'context': {'default_name': self.name, 
                            'default_purchase_ok': False,
                            'default_route_ids': self.env['stock.location.route'].search([('name', 'in', ['Make To Order', 'Manufacture'])]).mapped('id'),
                            'default_printed': self.printed,
                            'default_customer_id': self.partner_id.id,
                            'default_product_type': self.product_type,
                            'default_printing_form': self.printing_form.upper(),
                            'default_width': self.width,
                            'default_length': self.length,
                            'default_thickness': self.thickness,
                            'default_side_gusset': self.side_gusset,
                            'default_side_gusset_width': self.side_gusset_width,
                            'default_bottom_gusset': self.bottom_gusset,
                            'default_bottom_gusset_width': self.bottom_gusset_width,
                            'default_handle_type': self.handle_type.id,
                            'default_handle_attributes_vals': self.handle_attributes_vals.ids,
                            'default_seal_type': self.seal_type.id,
                            'default_lip_and_tape': self.lip_and_tape,
                            'default_lip_size': self.lip_size,
                            'default_options': self.options.ids,
                            'default_delivery_date': self.delivery_date,
                            'default_destination_remarks': self.destination_remarks,
                            'default_package_type_values':self.package_type_values,
                            'default_package_type': self.package_type,
                            'default_package_specs': self.package_specs,
                            'default_package_size': self.package_size,
                            'default_package_quantity': self.package_quantity,
                            'default_package_quantity_uom': self.package_quantity_uom.id,
                            'default_pallet': self.pallet,
                            'default_sticker': self.sticker,
                            'default_layer_1': self.layer_1.id,
                            'default_layer_2': self.layer_2.id,
                            'default_layer_3': self.layer_3.id,
                            'default_layer_4': self.layer_4.id,
                            'default_has_d2w': self.has_d2w,
                            'default_ink_type': self.ink_type,
                            'default_layer_1_thickness': self.layer_1_thickness,
                            'default_layer_2_thickness': self.layer_2_thickness,
                            'default_layer_3_thickness': self.layer_3_thickness,
                            'default_layer_4_thickness': self.layer_4_thickness,
                            'default_layer_1_density': self.layer_1_density,
                            'default_layer_2_density': self.layer_2_density,
                            'default_layer_3_density': self.layer_3_density,
                            'default_layer_4_density': self.layer_4_density
                        },
                }
           
    @api.multi
    def open_handle_attributes(self):
        """ 
        Returns the handle attributes of the handle type selected
        with values if already saved else empty values
        """
        self.ensure_one()
       
        handle_type = self._context.get('handle_type')
        active_lead = self.env['crm.lead'].browse(self._context.get('active_id'))
        handle_attrs_ids = (self.env['flex_print.handle_atts'].search([("handle_type_id.id", "=", handle_type)])).mapped('id')
       
        opp_attrs_vals = self.env['flex_print.opp_h_values'].search([("opp_id", "=", active_lead.id)])
       
        if opp_attrs_vals:
            for att_val in opp_attrs_vals:
                if att_val.handle_attribute_id.id not in handle_attrs_ids:
                    opp_attrs_vals.unlink()
                    break
               
        opp_attrs_vals = self.env['flex_print.opp_h_values'].search([("opp_id", "=", active_lead.id)])    
        if not opp_attrs_vals:
            for att_id in handle_attrs_ids:
                created_val = self.env['flex_print.opp_h_values'].create({'opp_id': active_lead.id, 'handle_attribute_id': att_id, 'value': ''})
        
        action = self.env.ref('flexible_printing.open_handle_attributes').read()[0]
        action['domain'] = [('opp_id', '=', active_lead.id)]
       
        return action
    
    @api.onchange('partner_id')
    def _onchange_partner(self):
        products_domain = {'domain': {'customer_products': [('id', 'in', [])]}}
        
        if self.partner_id:
            products_ids = (self.env["sale.order"].search([("partner_id.id", "=", self.partner_id.id)])).mapped('product_id')
            if products_ids:
                products_domain = {'domain': {'customer_products': [('id', 'in', products_ids.ids)]}}
            
        return products_domain
        
    @api.depends('partner_id')
    def _compute_customer_products(self):
        for record in self:
            products_ids = (self.env["sale.order"].search([("partner_id.id", "=", self.partner_id.id)])).mapped('order_line.product_id')
             
            if products_ids:
                record.customer_products_prev = (self.env["product.template"].search([("id", "in", products_ids.ids)]))
             
            if not self.partner_id:
                record.customer_products = False

    @api.multi
    def print_report(self):
        """
        @return : return report
        """
        self.ensure_one() #ensure that only one record is being passed on.
        action = self.env.ref('flexible_printing.action_report_opportunity_order').report_action(self)
        
        return action 
    
    @api.onchange('repeated_product')
    def _onchange_repeated_product(self):
        #reset Product
        if not self.repeated_product:
            self.customer_products = None
        else:    
            self.inquiry_product = None
            self.new_product = None
            
    @api.onchange('new_product')       
    def _onchange_new_product(self):
        """
        On change of new_product flag, set repeated product to False
        """
        self.inquiry_product = None
        self.product_artwork = None
        
        if self.new_product:
            self.customer_products = None
            self.repeated_product = None
            
    @api.onchange('printed')
    def _onchange_printed(self):
        #reset Print Form
        self.ensure_one()
        if self.printed == self.UNPRINTED:
            self.printing_form = None
            
    @api.onchange('side_gusset')
    def _onchange_side_gusset(self):
        #reset Side Gusset Width
        self.ensure_one()
        if not self.side_gusset:
            self.side_gusset_width = None
        
    @api.onchange('bottom_gusset')
    def _onchange_bottom_gusset(self):
        #reset Bottom Gusset Width
        self.ensure_one()
        if not self.bottom_gusset:
            self.bottom_gusset_width = None

    @api.onchange('lip_and_tape')
    def _onchange_lip_and_tape(self):
        #reset Lip size
        self.ensure_one()
        if not self.lip_and_tape:
            self.lip_size = None
       
    ROTO = "ROTO"
    FLEXO = "FLEXO"
    
    UNPRINTED = "UNPRINTED"
    ONE_SIDE = "ONE_SIDE"
    TWO_SIDES = "TWO_SIDES"
    
    printing_form_values = [(FLEXO.lower(), 'Flexo'), (ROTO.lower(), 'Roto')]
    printed_values = [(UNPRINTED, 'Unprinted'), (ONE_SIDE, 'Printed One Side'), (TWO_SIDES, 'Printed Two Sides')]
    
    printed = fields.Selection(printed_values)
    printing_form = fields.Selection(printing_form_values)
    
    product_type_values = [('bag', 'Bag'), ('roll', 'Roll'), ('sheet', 'Sheet'), ('sleeve', 'Sleeve')]
    product_type = fields.Selection(product_type_values, string="Product MO Type")
    
    repeated_product = fields.Boolean()
    
    product_artwork_values = [('cd_ready', 'CD Ready'), ('in_house_design', 'In House Design')]
    new_product = fields.Boolean()
    product_artwork = fields.Selection(product_artwork_values)
    
    customer_products = fields.Many2one(comodel_name='product.template')
    customer_products_prev = fields.One2many(comodel_name='product.template', compute='_compute_customer_products')
    
    inquiry_product = fields.Many2one(comodel_name='product.template')
    
    layer_1 = fields.Many2one('flex_print.layer_type')
    layer_1_thickness = fields.Float(related='layer_1.thickness', string="Layer 1 Thickness", store=True, readonly=False)
    layer_1_density = fields.Float(related='layer_1.density', string="Layer 1 Density", store=True, readonly=False)
    
    layer_2 = fields.Many2one('flex_print.layer_type')
    layer_2_thickness = fields.Float(related='layer_2.thickness', string="Layer 2 Thickness", store=True, readonly=False)
    layer_2_density = fields.Float(related='layer_2.density', string="Layer 2 Density", store=True, readonly=False)
    
    layer_3 = fields.Many2one('flex_print.layer_type')
    layer_3_thickness = fields.Float(related='layer_3.thickness', string="Layer 3 Thickness", store=True, readonly=False)
    layer_3_density = fields.Float(related='layer_3.density', string="Layer 3 Density", store=True, readonly=False)
    
    layer_4 = fields.Many2one('flex_print.layer_type')
    layer_4_thickness = fields.Float(related='layer_4.thickness', string="Layer 4 Thickness", store=True, readonly=False)
    layer_4_density = fields.Float(related='layer_4.density', string="Layer 4 Density", store=True, readonly=False)
    
    modifications_remarks = fields.Text()
    destination_remarks = fields.Text()
    
    side_gusset = fields.Boolean()
    side_gusset_width = fields.Float()
    
    bottom_gusset = fields.Boolean()
    bottom_gusset_width = fields.Float()
    
    width = fields.Float()
    length = fields.Float()
    thickness = fields.Float()
    
    handle_type = fields.Many2one('flex_print.handle_type')
    
    seal_type = fields.Many2one('flex_print.seal_type')
    
    lip_and_tape = fields.Boolean()
    lip_size = fields.Float()
    
    options = fields.Many2many('flex_print.product_option')
    
    attached_type_values = [('sample_attached', 'Sample Attached'), ('layout_attached', 'Layout Attached')]
    attached_type = fields.Selection(attached_type_values)
    
    delivery_date = fields.Integer(help="Delivery days after sales order date")
    
    package_type_values = [('bag', 'Bag'), ('box', 'Box')]
    package_type = fields.Selection(package_type_values)
    package_specs = fields.Text()
    
    package_size = fields.Char()
    package_quantity = fields.Float()
    package_quantity_uom = fields.Many2one('uom.uom', string='Package Unit', store=True, domain=[('name','in',['kg', 'Unit(s)', 't'])])
    pallet = fields.Boolean()
    sticker = fields.Boolean()
    
    handle_attributes_vals = fields.One2many('flex_print.opp_h_values', 'opp_id', 'Handle Type Attributes Values')
    
    has_d2w = fields.Boolean() 
    ink_type = fields.Char()
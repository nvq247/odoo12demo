from odoo import models, fields, api, _
import logging
from odoo.exceptions import ValidationError

log = logging.getLogger(__name__)

class ProductPrinting(models.Model):
    _name = "flex_print.product_printing_params"  
    _description = "Product printing params"
    
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
    
class CrmLeadProductTemplate(models.Model):
    _inherit = 'product.template'
    
    CLICHE = "CLICHE"
    CYLINDER = "CYLINDER"
    
    ROTO = "ROTO"
    FLEXO = "FLEXO"
    
    UNPRINTED = "UNPRINTED"
    ONE_SIDE = "ONE_SIDE"
    TWO_SIDES = "TWO_SIDES"
    
    product_printing_types = ((CLICHE, 'Cliche'), (CYLINDER, 'Cylinder'))
    
    printing_form_values = [(FLEXO, 'Flexo'), (ROTO, 'Roto')]
    printed_values = [(UNPRINTED, 'Unprinted'), (ONE_SIDE, 'Printed One Side'), (TWO_SIDES, 'Printed Two Sides')]
    
    printed = fields.Selection(printed_values)
    printing_form = fields.Selection(printing_form_values)
    printing_form_type = fields.Char()
    
    product_type_values = [('bag', 'Bag'), ('roll', 'Roll'), ('sheet', 'Sheet'), ('sleeve', 'Sleeve')]
    product_type = fields.Selection(product_type_values, string="Product MO Type")
    
    side_gusset = fields.Boolean()
    side_gusset_width = fields.Float()
    
    bottom_gusset = fields.Boolean()
    bottom_gusset_width = fields.Float()
    
    width = fields.Float()
    length = fields.Float()
    thickness = fields.Float()
    
    handle_type = fields.Many2one('flex_print.handle_type')
    handle_attributes_vals = fields.One2many('flex_print.opp_h_values', 'opp_id', 'Handle Type Attributes Values')
    seal_type = fields.Many2one('flex_print.seal_type')
    lip_and_tape = fields.Boolean()
    lip_size = fields.Float()
    options = fields.Many2many('flex_print.product_option')
    
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
    
    delivery_date = fields.Integer(help="Delivery days after sales order date")
    destination_remarks = fields.Text()
    
    package_type_values = [('bag', 'Bag'), ('box', 'Box')]
    package_type = fields.Selection(package_type_values)
    package_specs = fields.Text()
    
    package_size = fields.Char()
    package_quantity = fields.Float()
    package_quantity_uom = fields.Many2one('uom.uom', string='Package Unit', store=True, domain=[('name','in',['kg', 'Unit(s)', 't'])])
    pallet = fields.Boolean()
    sticker = fields.Boolean()
    
    customer_id = fields.Many2one('res.partner', string='Customer')
    
    product_printing_id = fields.One2many('flex_print.product_printing_params', 'product_id', 'Cliche/Cylinder Parameters')
        
    has_d2w = fields.Boolean()
    ink_type = fields.Char()
    
    @api.model
    def create(self, vals): 
        """
        Overwrite create product function to check if there is active_id in context, get active_lead by active_id and if found then update active_lead inquiry product
        by the product id (result.id)
        """
        result = super(CrmLeadProductTemplate, self).create(vals)
        active_lead = self.env['crm.lead'].browse(self._context.get('active_id'))
        
        if active_lead:
            active_lead.inquiry_product = result.id

        return result
    
    @api.constrains('product_printing_id')
    @api.one
    def _check_product_printing_id_count(self):
        if len(self.product_printing_id) > 1:
            raise ValidationError(_('A Product should only have one Cliche/Cylinder item.'))
      
    @api.onchange('printing_form')  
    def _onchange_printing_form(self):
        """
        Update type of printing form e.g. if roto => Cylinder, if flexo => Cliche
        """
        if self.printing_form == self.ROTO:
            self.printing_form_type = "%s - %s" % (dict(self.product_printing_types).get(self.CYLINDER), self.name)
        elif self.printing_form == self.FLEXO:
            self.printing_form_type = "%s - %s" % (dict(self.product_printing_types).get(self.CLICHE), self.name)
       
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
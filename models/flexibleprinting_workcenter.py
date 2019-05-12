from odoo import models, fields, api, tools

import logging

log = logging.getLogger(__name__)

class WorkcenterType(models.Model):
    _name = "flex_print.workcenter_type"
    _description = "Workcenter type"
    
    name = fields.Char()
    code = fields.Char(required=True, help="Codes are used to read data from the product onto the printed manufacturing order")
    parameters = fields.One2many('flex_print.workcenter_parameters', 'workcenter_type_id')
    
class WorkcenterParameters(models.Model): 
    _name = "flex_print.workcenter_parameters"
    _description = "Workcenter parameters"
    
    workcenter_type_id = fields.Many2one('flex_print.workcenter_type', ondelete="cascade")
    name = fields.Char(required=True)
    arabic_name = fields.Char()
    code = fields.Char(required=True)
    is_proportional = fields.Boolean()
    
    _sql_constraints = [
        ('code_unique', 'unique(workcenter_type_id, code)', 'Make sure code is unique')
    ]
    
class ManufacturingWorkcenterInherited(models.Model):
    _inherit = 'mrp.workcenter'
    
    work_center_type = fields.Many2one('flex_print.workcenter_type', string='Work Center Type')
    
class ManufacturingRountingWorkcenterInherited(models.Model):
    _inherit = 'mrp.routing.workcenter'
             
    @api.multi        
    @api.onchange('workcenter_id')
    def _workcenter_change(self):
        """
        On workcenter change check if has parameters then display options field else hide it
        
        Get list of created workcenter type params ids, and list of initial workcenter params ids. Check if length of 
        created_workcenter_type_params is less than initial_workcenter_params then create missing parameters
        """
        self.ensure_one()
        self.hide_workcenter_parameter = True if len(self.workcenter_id.work_center_type.parameters) == 0 else False
     
    hide_workcenter_parameter = fields.Boolean(string='Hide Work Center Parameter', compute="_workcenter_change") 
    workcenter_type_parameters = fields.One2many('flex_print.routing_workcenter_parameters', 'routing_workcenter_id', string='Parameter')
    workcenter_image_ids = fields.One2many('flex_print.routing_workcenter_image', 'routing_workcenter_id', string='Images')
    
class RoutingWorkcenterParameters(models.Model):
    _name = 'flex_print.routing_workcenter_parameters'
    _description = "Routing Workcenter parameters"
    
    @api.onchange('value')
    def value_change(self): 
        """
        On value change, check if the value is empty and the parameter is not selected then make sure to get params 
        for the selected workcenter
        """
        if self.value == "":
            parameter_ids_list = self.get_workcenter_params()
            param_domain = {'domain': {'parameter': [('id', 'in', parameter_ids_list)]}}
              
            return param_domain
     
    def get_workcenter_params(self):
        """
        From workcenter id, get workcenter params
        @return workcenter params ids list
        """    
        parameter_ids_list = []
              
        if self._context.get('workcenter_id'):
            workcenter = self.env["mrp.workcenter"].browse(self._context.get('workcenter_id'))
            for parameter in workcenter.work_center_type.parameters:
                parameter_ids_list.append(parameter.id)
                
        return parameter_ids_list
    
    routing_workcenter_id = fields.Many2one('mrp.routing.workcenter', ondelete="cascade")
    parameter = fields.Many2one('flex_print.workcenter_parameters', string='Parameter', required=True, ondelete="cascade")
    value = fields.Char(default="", required=True)

class RoutingWorkcenterImage(models.Model):
    _name = 'flex_print.routing_workcenter_image'
    _description = "Routing Workcenter images"
    
    routing_workcenter_id = fields.Many2one('mrp.routing.workcenter', ondelete='cascade')
    name = fields.Char('Name')
    image = fields.Binary('Image', attachment=True)
    image_small = fields.Binary(
        "Small-sized image", compute='_compute_images', inverse='_set_image_small',
        help="Image of the product variant (Small-sized image of workcenter template if false).")
    image_medium = fields.Binary(
        "Medium-sized image", compute='_compute_images', inverse='_set_image_medium',
        help="Image of the product variant (Medium-sized image of workcenter template if false).")
    
    @api.one
    @api.depends('image')
    def _compute_images(self):
        if self._context.get('bin_size'):
            self.image_medium = self.image_variant
            self.image_small = self.image_variant
        else:
            resized_images = tools.image_get_resized_images(self.image, return_big=True, avoid_resize_medium=True)
            self.image_medium = resized_images['image_medium']
            self.image_small = resized_images['image_small']
            
        if not self.image_medium:
            self.image_medium = self.image_medium
        if not self.image_small:
            self.image_small = self.image_small
    
    @api.one
    def _set_image_medium(self):
        self._set_image_value(self.image_medium)

    @api.one
    def _set_image_small(self):
        self._set_image_value(self.image_small)
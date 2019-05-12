# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_manage_handles_types = fields.Boolean("Handles Types",
                                                implied_group='flexible_printing.group_manage_handles_types')
    
    
    group_manage_seals_types = fields.Boolean("Seals Types", 
                                              implied_group='flexible_printing.group_manage_seals_types')
    
    group_manage_quantity_units = fields.Boolean("Quantity Units", 
                                              implied_group='flexible_printing.group_manage_quantity_units')
    
    
    group_manage_work_center_by_type = fields.Boolean(
        "Manage work centers by type",
        implied_group='flexible_printing.group_manage_work_center_by_type')
    
    group_manage_layers_types = fields.Boolean(
        "Layer Type",
        implied_group='flexible_printing.group_manage_layers_types')
    
    @api.onchange('group_manage_handles_types')
    def _onchange_manage_handles_types(self):
        """  """
        pass
   
    @api.onchange('group_manage_seals_types')
    def _onchange_manage_seals_types(self):
        """  """
        pass
   
    @api.onchange('group_manage_quantity_units')
    def _onchange_manage_quantity_units(self):
        """  """
        pass
    
    @api.onchange('group_manage_work_center_by_type')
    def _onchange_manage_work_center_by_type(self):
        """  """
        pass
    
    @api.onchange('group_manage_layers_types')
    def _onchange_manage_layer_type(self):
        """  """
        pass
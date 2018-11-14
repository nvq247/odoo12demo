# -*- coding: utf-8 -*-
from odoo import fields, models, tools, api
import logging

log = logging.getLogger(__name__)

class ProductPrintingReport(models.Model):
    """ Product with Printing """

    _name = "flex_print.product.printing.report"
    _auto = False
    _description = "Product with Printing Analysis"
    
    product_printed_id = fields.Many2one('flex_print.product_printing_params', readonly=True)
    printed_name = fields.Char(string='Name', readonly=True)
    product_name = fields.Char(string='Product', readonly=True)
    printing_form = fields.Char(string='Type', readonly=True) 
    customer = fields.Many2one('res.partner', string='Customer', readonly=True)
    last_mo_date = fields.Datetime(string='Last MO Date', readonly=True)
     
    def _query(self):
        query_str = """
            SELECT
                pt.id,
                pt.customer_id as customer,
                pt.printing_form,
                pt.name as product_name,
                pp.id as product_printed_id,
                pp.name as printed_name,
                prod.date_planned_start as last_mo_date
                
            FROM "product_template" pt
            
            INNER JOIN "flex_print_product_printing_params" pp ON pp.product_id = pt.id
            
            LEFT JOIN "mrp_production" prod on prod.product_id = pt.id
        """
        
        return query_str

    @api.multi
    def open_product_printing_form(self):
        
        return {
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'flex_print.product_printing_params',
                'res_id': self.product_printed_id.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'flags': {'form': {'action_buttons': True}}
        }

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE VIEW %s AS (
            %s
        )""" % (self._table, self._query()))

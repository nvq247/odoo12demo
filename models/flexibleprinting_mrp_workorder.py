from odoo import models, fields, api
import logging

log = logging.getLogger(__name__)

class MrpWorkOrderInherited(models.Model):
    _inherit = 'mrp.workorder'
    
    preview = fields.Html('Report Preview', compute="_compute_manufacture_order_html")
      
    @api.multi
    def render_template(self, template, values=None):
        """Allow to render a QWeb template python-side. This function returns the 'ir.ui.view'
        render but embellish it with some variables/methods used in reports.
        :param values: additional methods/variables used in the rendering
        :returns: html representation of the template
        """
        if values is None:
            values = {}

        context = dict(self.env.context, inherit_branding=True)  # Tell QWeb to brand the generated html

        # Browse the user instead of using the sudo self.env.user
        user = self.env['res.users'].browse(self.env.uid)

        view_obj = self.env['ir.ui.view'].with_context(context)
        values.update(
            editable=False,
            user=user,
            company=None,
        )
        return view_obj.render_template(template, values)
      
    @api.model
    def render_qweb_html(self, docids, data=None):
        """
        This method generates and returns html version of a report.
        """
        # If the report is using a custom model to render its html, we must use it.
        # Otherwise, fallback on the generic html rendering.
        report_model_name = 'report.flexible_printing.mrp_mo_structure'
        report_name = "flexible_printing.mrp_mo_structure"
        report_model = self.env.get(report_model_name)

        if report_model is not None:
            data = report_model._get_report_values(docids, data=data)
        
        return self.render_template(report_name, data)
    
    @api.one
    def _compute_manufacture_order_html(self):
        """
        Render manufacture data and save rendered report into preview to display it on the workoder page 
        """
        production = self.production_id
        self.preview = self.render_qweb_html(production.id)
        
class MrpProductionInherited(models.Model):
    _inherit = 'mrp.production'
    
    print_mode = fields.Selection(related='product_id.printing_form', string="Print Mode", store=True)
    customer = fields.Many2one(related='product_id.customer_id', string="Customer", store=True)
    barcode = fields.Char(related='product_id.barcode', string="Barcode", store=True)
    seal_type = fields.Many2one(related='product_id.seal_type', string="Seal", store=True)
    handle_type = fields.Many2one(related='product_id.handle_type', string="Handle", store=True)
    layer_1 = fields.Many2one(related='product_id.layer_1', string="Mono Layer", store=True)
    layer_2 = fields.Many2one(related='product_id.layer_2', string="Duplex Layer", store=True)
    layer_3 = fields.Many2one(related='product_id.layer_3', string="Triplex Layer", store=True)
    layer_4 = fields.Many2one(related='product_id.layer_4', string="Fourlex Layer", store=True)
    cylinder_size = fields.Float(related='product_id.product_printing_id.cylinder_size', string="Cylinder Size", store=True)
    cylinder_width = fields.Float(related='product_id.product_printing_id.cylinder_width', string="Cylinder Width", store=True)
    remark = fields.Text('Remarks')
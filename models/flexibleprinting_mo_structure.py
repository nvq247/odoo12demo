from odoo import api, models
import logging
from datetime import datetime, timedelta
from math import ceil

log = logging.getLogger(__name__)

class MrpMoStructure(models.AbstractModel):
    _name = 'report.flexible_printing.mrp_mo_structure'
    _description = "Mrp MO report"
    
    @api.multi
    def get_routing(self, production):
        """
        @param production: production object
        
        @return routing if production found else None
        """
        routing = production.routing_id if production else None
        return routing
    
    @api.multi
    def get_operations(self, production, routing):
        """
        @param production: Production object (MO)
        @param routing: Routing object retrieve to get list of operations assigned to it
        
        Search operations by routing and append operations values into operations_list
        
        For each operation, get operation materials consumed in from MO consumed products(stock.move)
        Check if any of product consumed layers has a d2w parameter
        Get all operation params, get opreration imgs and kit compositions
        
        @return operations list of object containing operation info e.g. [{ 'operation_name': <operation.name>,
                                                                            'workcenter_name':  <operation.workcenter_id.name>,
                                                                            'operation_description': <operation.note>,
                                                                            'operation_materials': <operation_materials>, 
                                                                            'operation_params': <operation_params>,
                                                                            'operation_has_d2w': <operation_has_d2w>,
                                                                            'compositions': <compositions>,
                                                                            'operation_imgs': <operation_imgs>}, ..]
        """
        operations_list = []
        operations = self.env['mrp.routing.workcenter'].search([('routing_id', '=', routing.id)])
        
        for operation in operations:
            operation_material_obj = production.bom_id.bom_line_ids.search([('operation_id', '=', operation.id)])
            
            move_raw_ids = production.move_raw_ids.search([('bom_line_id', 'in', operation_material_obj.ids)])
            operation_materials_list = []
            raw_products_list = []
            for raw_id in move_raw_ids:
                raw_products_list.append(raw_id.product_id.id)
                operation_materials_list.append("%s/%s %s" % (raw_id.product_id.default_code if raw_id.product_id.default_code else raw_id.product_id.name, raw_id.product_uom_qty, raw_id.product_uom.name))
            
            for opperation in operation_material_obj:
                if opperation.product_id.id not in raw_products_list:
                    operation_materials_list.append("%s" % (opperation.product_id.name))
                
            operation_materials = ", ".join(operation_materials_list)
            
            operation_params = self.get_operation_params(production, operation)
            
            operation_imgs = self.env['flex_print.routing_workcenter_image'].search([('routing_workcenter_id', '=', operation.id)])
            
            operation_has_d2w = True if production.product_id.has_d2w and operation.workcenter_id.work_center_type.code == "EXTRUDER" else False
            
            compositions = self.get_kit_product(production, operation)
            operations_list.append({'operation_name': operation.name,
                                    'workcenter_name':  operation.workcenter_id.name,
                                    'operation_description': operation.note,
                                    'operation_materials': operation_materials, 
                                    'operation_params': operation_params,
                                    'operation_has_d2w': operation_has_d2w,
                                    'compositions': compositions,
                                    'operation_imgs': operation_imgs})
            
        return operations_list
       
    @api.multi
    def get_operation_params(self, production, operation): 
        """
        @param production: MO production object
        @param operation: operation object
        
        Get list of workcenter paramters assign to the workcenter of the operation and insert it into dict as code is the key and value is the arabic name and the name e.g {packaging_type: {'name':<name>, 'arabic_name':<arabic_name>}}
        used later on to update auto filled operations arabic name
        
        Get all operations parameters added in the operation configuration and for operations of type: PRINTING AND PACKAGING get product manufacturing parameters
        and Auto fill its parameters
        
        @return opreation_params list of objects e.g. [{'name':<name>, 'value':<value>, 'arabic_name':<arabic_name>},..]
        """
        product = production.product_id
        operation_workcenter_type = operation.workcenter_id.work_center_type
        operation_workcenter_type_code = operation.workcenter_id.work_center_type.code
        
        all_parameters = self.env['flex_print.workcenter_parameters'].search([('workcenter_type_id', '=', operation_workcenter_type.id)])
        parameters_dict = {parameter.code: {"name": parameter.name, "arabic_name": parameter.arabic_name, 'is_proportional': parameter.is_proportional} for parameter in all_parameters}
        
        operation_params = []
        operation_params_list = []
        excluded_parameter_code = []
        
        if operation_workcenter_type_code == "PRINTING":
            cliche_cylinder_manager = product.product_printing_id
            
            cylinder_size_code = "CYLINDER_SIZE" 
            colors_code = "COLORS" 
            ink_type_code = "INK_TYPE"
            direction_code = "PRINTING_DIRECTION"
            barcode_code = "CLICHE_BARCODE"
            printing_length_code = "LENGTH"
            excluded_parameter_code.extend([cylinder_size_code, colors_code, ink_type_code, direction_code, barcode_code, printing_length_code])
            
            printing_workcenter_parameters = self.env['flex_print.routing_workcenter_parameters'].search([('routing_workcenter_id.routing_id', '=', production.routing_id.id), ('routing_workcenter_id', '=', operation.id), ('routing_workcenter_id.workcenter_id.work_center_type.code', '=', 'PRINTING'), ('parameter.code', '=', 'LENGTH')])
            printing_length = float(printing_workcenter_parameters.value) if printing_workcenter_parameters else None
            
            if printing_length:
                bom_product_to_consume_qty = float(sum([bom_line.product_qty for bom_line in self.env['stock.move'].search([('bom_line_id.operation_id', '=', operation.id), ('raw_material_production_id', '=', production.id)]).bom_line_id]))
                
                if parameters_dict.get(printing_length_code, {}).get('is_proportional', False) and bom_product_to_consume_qty > 0:
                    printing_length = float(ceil(printing_length * production.product_qty / bom_product_to_consume_qty))
                    
                operation_params.append({'name': parameters_dict.get(printing_length_code, {}).get('name', 'Length'), 'value': "%s METERS" % (printing_length, ), 'arabic_name': parameters_dict.get(printing_length_code, {}).get('arabic_name', '')})
            
            if cliche_cylinder_manager.cylinder_size and cliche_cylinder_manager.thickness:
                operation_params.append({'name': parameters_dict.get(cylinder_size_code, {}).get('name', 'Cylinder Size'), 'value': "%s (Cliche %s)" % (cliche_cylinder_manager.cylinder_size, cliche_cylinder_manager.thickness), 'arabic_name': parameters_dict.get(cylinder_size_code, {}).get('arabic_name', '')})
            
            if cliche_cylinder_manager.color:
                operation_params.append({'name': parameters_dict.get(colors_code, {}).get('name', 'Colors'), 'value': cliche_cylinder_manager.color, 'arabic_name': parameters_dict.get(colors_code, {}).get('arabic_name', '')})

            if product.ink_type:
                operation_params.append({'name': parameters_dict.get(ink_type_code, {}).get('name', 'Ink Type'), 'value': product.ink_type, 'arabic_name': parameters_dict.get(ink_type_code, {}).get('arabic_name', '')})
            
            if dict(self.env['flex_print.product_printing_params'].print_direction_values).get(cliche_cylinder_manager.direction, ''):
                operation_params.append({'name': parameters_dict.get(direction_code, {}).get('name', 'Direction'), 'value': dict(self.env['flex_print.product_printing_params'].print_direction_values).get(cliche_cylinder_manager.direction, ''), 'arabic_name': parameters_dict.get(direction_code, {}).get('arabic_name', '')})

            if cliche_cylinder_manager.barcode:
                operation_params.append({'name': parameters_dict.get(barcode_code, {}).get('name', 'Barcode'), 'value': cliche_cylinder_manager.barcode, 'arabic_name': parameters_dict.get(barcode_code, {}).get('arabic_name', '')})

        elif operation_workcenter_type_code == "PACKAGING":
            package_type = product.package_type
            
            package_type_code = "PACKAGING_TYPE"
            size_code = "BOX_SIZE" if package_type == 'box' else "BAG_SIZE"
            size_str = "Box Size" if package_type == 'box' else "Bag Size"  
            weight_code = "BOX_WEIGHT" if package_type == 'box' else "BAG_WEIGHT" 
            weight_str = "Box Weight" if package_type == 'box' else "Bag Weight" 
            pallet_needed_code = "PALLET_NEEDED"
            sticker_needed_code = "STICKER_NEEDED"
            delivery_place_code = "DELIVERY_PLACE_DATE"
            total_bag_boxes_code = "TOTAL_BOXES" if package_type == 'box' else "TOTAL_BAGS"  
            total_bag_box = 'Total Boxes' if package_type == 'box' else "Total Bags"  
            
            excluded_parameter_code.extend([package_type_code, size_code, weight_code, pallet_needed_code, sticker_needed_code, delivery_place_code, total_bag_boxes_code])
            
            product_delivery_date = product.delivery_date
            delivery_date = None
            
            if product_delivery_date:
                
                if production.origin:
                    sale_confirmation_date = self.env['sale.order'].search([('name', '=', production.origin)]).confirmation_date
                    delivery_date = datetime.strptime(sale_confirmation_date, "%Y-%m-%d %H:%M:%S") + timedelta(days=product_delivery_date) if sale_confirmation_date else None
                else:
                    delivery_date = production.date_planned_start + timedelta(days=product_delivery_date)
                    
            delivery_date_str = datetime.strftime(delivery_date, "%d/%m/%Y") if delivery_date else None
            
            #Add total of boxes used param here
            if package_type:
                operation_params.append({'name': parameters_dict.get(package_type_code, {}).get('name', 'Package Type'), 'value': package_type, 'arabic_name': parameters_dict.get(package_type_code, {}).get('arabic_name', '')})
                
            if product.package_size:
                operation_params.append({'name': parameters_dict.get(size_code, {}).get('name', size_str), 'value': product.package_size, 'arabic_name': parameters_dict.get(size_code, {}).get('arabic_name', '')})
 
            if product.package_quantity:
                operation_params.append({'name': parameters_dict.get(weight_code, {}).get('name', weight_str), 'value': "%s %s" % (product.package_quantity, product.package_quantity_uom.name if product.package_quantity_uom else ""), 'arabic_name': parameters_dict.get(weight_code, {}).get('arabic_name', '')})
            
            total_boxes = ceil(production.product_qty / product.package_quantity) if product.package_quantity > 0 else 0
            
            operation_params.extend([{'name': parameters_dict.get(pallet_needed_code, {}).get('name', 'Pallet'), 'value': "Yes" if product.pallet else "No", 'arabic_name': parameters_dict.get(pallet_needed_code, {}).get('arabic_name', '')},
                {'name': parameters_dict.get(sticker_needed_code, {}).get('name', 'Sticker'), 'value': "Yes" if product.sticker else "No", 'arabic_name': parameters_dict.get(sticker_needed_code, {}).get('arabic_name', '')}
            ])
            
            if total_boxes > 0:
                operation_params.append({'name': parameters_dict.get(total_bag_boxes_code, {}).get('name', total_bag_box), 'value': total_boxes, 'arabic_name': parameters_dict.get(total_bag_boxes_code, {}).get('arabic_name', '')})

            if delivery_date_str:
                operation_params.append({'name': parameters_dict.get(delivery_place_code, {}).get('name', 'Delivery Place and Date'), 'value': "%s %s" % (delivery_date_str, product.destination_remarks if product.destination_remarks else "") if product_delivery_date else "" , 'arabic_name': parameters_dict.get(delivery_place_code, {}).get('arabic_name', '')})
         
        elif operation_workcenter_type_code == "CUTTING":
            sealing_type_code = "SEALING_TYPE"
            gusset_code = "GUSSET"
            options_code = "OPTIONS"
            
            excluded_parameter_code.extend([sealing_type_code, gusset_code, options_code])
            
            product_side_gusset, product_bottom_gusset = "", ""
            if product.side_gusset:
                product_side_gusset = "Side Gusset (%s cm)" % (product.side_gusset_width)
            if product.bottom_gusset:
                product_bottom_gusset = "Bottom Gusset (%s cm)" % (product.bottom_gusset_width)
                
            product_gusset = "%s %s" % (product_side_gusset, product_bottom_gusset)
                                                           
            operation_params.extend([{'name': parameters_dict.get(sealing_type_code, {}).get('name', 'Sealing Type'), 'value': product.seal_type.name if product.seal_type else 'NO', 'arabic_name': parameters_dict.get(sealing_type_code, {}).get('arabic_name', '')},
                                    {'name': parameters_dict.get(options_code, {}).get('name', 'Options'), 'value': ", ".join(product.options) if product.options else 'NO', 'arabic_name': parameters_dict.get(options_code, {}).get('arabic_name', '')},
                                    {'name': parameters_dict.get(gusset_code, {}).get('name', 'Gusset'), 'value': product_gusset if product_gusset.strip() else 'NO', 'arabic_name': parameters_dict.get(gusset_code, {}).get('arabic_name', '')}
                                ])
            
        operation_params_list.extend([{'name': op_param.parameter.name, 'value': op_param.value, 'arabic_name': op_param.parameter.arabic_name} for op_param in self.env['flex_print.routing_workcenter_parameters'].search([('routing_workcenter_id', '=', operation.id), ('parameter.code', 'not in', excluded_parameter_code)])])
        operation_params_list.extend(operation_params)
        
        return operation_params_list  
    
    @api.multi
    def get_kit_product(self, production, operation):
        """
        @param production: MO object
        @param operation: mrp.routing.workcenter 
        
        Get stock products for MO
        Get BOM of type kit where stock products are found in BOM bom_line
        
        Check for assigned BOM for MO, that the kit_product is in BOM line and get Product that are added to a BOM with kit type where BOM line is consumed in an operation
        
        Search stock.move for the MO and kit products and get the product name, consume qty and ratio
        
        total quantity is the sum of kit product qty (product_uom_qty), ratio is the percentage for the kit product with respect to the total qty
        
        Loop over stock.move retrieved and append product to composition list 
        
        Add to composition dict the total ratio, total qty, and compositions list
        
        @return dict of kit product info {
            "total_ration": <total_ratio>,
            "total_qty": <total_qty>,
            "composition_list": <composition_list>
        }
        """
        move_raw_ids = production.move_raw_ids
        
        product_in_move_raw_ids_list = move_raw_ids.mapped('product_id').ids
        
        kit_bom = production.bom_id.search([('type', '=', 'phantom'), ('bom_line_ids.product_id', 'in', product_in_move_raw_ids_list)])
        
        kit_bom_product_ids_list = kit_bom.mapped('bom_line_ids.product_id').ids
        
        kit_bom_product_assigned_product = kit_bom.mapped('product_tmpl_id').ids
        
        production_bom_line_ids = production.bom_id.bom_line_ids.search([('product_id.product_tmpl_id', 'in', kit_bom_product_assigned_product), 
                                                                   ('operation_id', '=', operation.id)])
        
        composition_dict = {}
        if production_bom_line_ids:   
            kit_mo_products = move_raw_ids.search([('raw_material_production_id', '=', production.id), ('product_id', 'in', kit_bom_product_ids_list)])
            
            if kit_mo_products:
                total_qty = self._is_integer(sum(kit_mo_products.mapped('product_uom_qty')))
                total_ratio = 100
                 
                composition_list = []
                for kit_product in kit_mo_products:
                    product_uom_qty = kit_product.product_uom_qty
                    composition_list.append({
                            'name': kit_product.product_id.name,
                            'quantity': self._is_integer(product_uom_qty),
                            "ratio": float("%.2f" % (product_uom_qty * 100 / total_qty)),
                        })
         
                composition_dict = {
                    "total_ratio": total_ratio,
                    "total_qty": total_qty,
                    "composition_list": composition_list,
                }
                 
        log.info("Kit product composition dict: %s for MO: '%s' and BOM operation: '%s'", composition_dict, production.name, operation.name) 
         
        return composition_dict
      
    def _is_integer(self, value):
        """
        @param value: number to check if is integer or no
        @return integer if integer else float with precision 2
        """  
        return int(value) if value.is_integer() else float("%.2f" % value) 
    
    @api.model
    def _get_report_values(self, docid, data=None):
        """
        From docid get production list
        """
        production = self.env['mrp.production'].browse(docid)
        routing = self.get_routing(production)
        operations = self.get_operations(production, routing)
        
        sales_order = self.env['sale.order'].search([('name', '=', production.origin)])
        
        if production.product_id and production.product_id.customer_id:
            customer_name = production.product_id.customer_id.name
        elif sales_order and sales_order.partner_id:
            customer_name = sales_order.partner_id.name
        else:
            customer_name = ""
            
        product_barcode = production.product_id.barcode if production.product_id else "" 
        
        return {
                'operations': operations, 
                'order_number': production.name,
                'order_receipt_date': production.date_planned_start,
                'customer_name': customer_name,
                'product_barcode': product_barcode,
                'order_quantity': production.product_qty,
                'order_uom': production.product_uom_id.name,
                'routing_name':  routing.name if routing else None,
                'print_type': data.get('print_type') if data else None
            }

class MrpMoSinglePageStructure(models.AbstractModel):
    _name = 'report.flexible_printing.mrp_mo_single_page_structure'
    _inherit = 'report.flexible_printing.mrp_mo_structure'
    _template = 'flexible_printing.mrp_mo_structure'
    
    @api.model
    def _get_report_values(self, docid, data=None):
        data = {"print_type": "SINGLE_PAGE"}
        return self.env['report.flexible_printing.mrp_mo_structure']._get_report_values(docid, data=data)
    
class MrpMoMultiPageStructure(models.AbstractModel):
    _name = 'report.flexible_printing.mrp_mo_multi_page_structure'
    _inherit = 'report.flexible_printing.mrp_mo_structure'
    _template = 'flexible_printing.mrp_mo_structure'
    
    @api.model
    def _get_report_values(self, docid, data=None):
        data = {"print_type": "MULTI_PAGE"}
        return self.env['report.flexible_printing.mrp_mo_structure']._get_report_values(docid, data=data)
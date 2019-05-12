# -*- coding: utf-8 -*-
from odoo import http

# class FlexiblePrinting(http.Controller):
#     @http.route('/flexible_printing/flexible_printing/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/flexible_printing/flexible_printing/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('flexible_printing.listing', {
#             'root': '/flexible_printing/flexible_printing',
#             'objects': http.request.env['flexible_printing.flexible_printing'].search([]),
#         })

#     @http.route('/flexible_printing/flexible_printing/objects/<model("flexible_printing.flexible_printing"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('flexible_printing.object', {
#             'object': obj
#         })
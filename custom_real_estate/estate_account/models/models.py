# -*- coding: utf-8 -*-

from odoo import models, Command

class EstateProperty(models.Model):
    
    _inherit = "estate_property"

    def Action_Sold(self):
        res = super().Action_Sold()
        journal = self.env["account.journal"].search([("type", "=", "sale")], limit=1)
        for prop in self :
            self.env["account.move"].create(
             {
                 "partner_id"  : prop.buyer_id.id,
                 "move_type"  : "out_invoice",
                 "journal_id"  : journal.id,
                 "invoice_line_ids": [
                    Command.create({
                        "name": prop.name,
                        "quantity": "1.0",
                        "price_unit": prop.selling_price * 6.0 / 100.0,
                    }),
                    Command.create({
                        "name": "Administrative Fees",
                        "quantity": "1.0",
                        "price_unit": "100.00",
                    })
                ],
             }
         )
        return res
        
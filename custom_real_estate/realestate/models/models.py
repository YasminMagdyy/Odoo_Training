# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

class RealEstate(models.Model):
    
    _name = 'estate_property'
    _description = "estate_property"
    _order = "id desc"
    name = fields.Char('Name', required=True)
    description = fields.Text('Description')
    postcode = fields.Char('PostCode')
    date_availability = fields.Datetime('Date Availability', default=lambda self:(fields.Datetime.today()+relativedelta(days=90)).strftime('%Y-%m-%d %H:%M'))
    expected_price = fields.Float('Expected Price', required=True)
    selling_price = fields.Float('Selling Price', readonly=True, copy=False)
    bedrooms = fields.Integer('Bed Rooms', default=2)
    living_area = fields.Integer('Living Area')
    facades = fields.Integer('Facades')
    garage = fields.Boolean('Garage')
    garden = fields.Boolean('Garden')
    garden_area = fields.Integer('Garden Area')
    garden_orientation = fields.Selection([('north', 'North'),('south', 'South'),('east', 'East'),('west', 'West')],'Garden Orientation')
    active = fields.Boolean('Active', default=False)
    state = fields.Selection([('new', 'New'), ('offer received', 'Offer Received'), ('offer accepted', 'Offer Accepted'), ('sold', 'Sold'), ('canceled', 'Canceled')], 'State', default='new', required=True, copy=False)
    property_type_id = fields.Many2one('estate_property_type', 'Property_Type_ID')
    tag_ids = fields.Many2many('estate_property_tag', string='Tag_IDs')
    property_offer_id = fields.One2many('estate_property_offer', 'offer_property_id', string='Offer_Property_IDs')
    user_id = fields.Many2one('res.users', string='Salesperson')
    buyer_id = fields.Many2one('res.partner', string='Buyer', readonly=True, copy=False) 
    total_area = fields.Integer(compute="_Total_Area")
    best_price = fields.Float(compute="_Best_Offer_Price")
    _sql_constraints=[('check_expected_price', 'CHECK(expected_price > 0)', 'The expected price must be strictly positive'),
                    ('check_selling_price', 'CHECK (selling_price >= 0)', 'The selling price  must be  positive')]
                       
    
    @api.depends('living_area', 'garden_area')
    def _Total_Area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends('property_offer_id.price')
    def _Best_Offer_Price(self):
        for record in self:
            record.best_price = sum(record.property_offer_id.mapped("price")) if record.property_offer_id else 0.0 

    @api.onchange("garden")
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = "north"
        else:
            self.garden_area = 0
            self.garden_orientation = False
           
    def Action_Sold(self):
        if "canceled" in self.mapped("state"):
            raise UserError("Canceled properties cannot be sold.")
        return self.write({"state": "sold"})
    
    def Action_Cancelled(self):
        if "sold" in self.mapped("state"):
            raise UserError("Sold properties cannot be canceled")
        return self.write({"state": "canceled"})

    @api.constrains("expected_price", "selling_price")
    def _Check_Difference_Price(self):
        for record in self:
            if (not float_is_zero(record.selling_price, precision_rounding=0.01) 
                and float_compare(record.selling_price, record.expected_price * 90.0/100.0, precision_rounding=0.01) < 0):
                raise ValidationError("The selling price must be at least 90% of the expected price! "
                    + "You must reduce the expected price if you want to accept this offer.")

    def unlink(self):
        if self.state not in ['new', 'canceled']:
            raise UserError("Only new and canceled properties can be deleted.")
        return super().unlink()

class ResUser(models.Model):
    _inherit = "res.users"

    property_ids = fields.One2many('estate_property', 'user_id', string='Properties', domain="[('state','in',('new', 'offer received'))]")

class RealEstateType(models.Model):
    _sql_constraints=[("check_name", "UNIQUE(name)", "The name must be unique")]
    _name = 'estate_property_type'
    _description = "property_type"
    _order = "sequence, name"

    name = fields.Char('Name', required=True)
    property_ids = fields.One2many('estate_property', 'property_type_id', string="Properties")
    sequence = fields.Integer('Sequence', default=10)
    offer_ids = fields.One2many('estate_property_offer', 'property_type_id', string="Offers")
    offer_count = fields.Integer(compute="_Number_of_Offers_property")
    
    def _Number_of_Offers_property(self):
        for record in self:
            self.offer_count = len(self.offer_ids)


class RealEstateTag(models.Model):
    _sql_constraints=[("check_name", "UNIQUE(name)", "The name must be unique")]
    _name = 'estate_property_tag'
    _description = "property_tag"
    _order = "name"

    name = fields.Char('Name', required=True)
    color = fields.Integer('Color')

class RealEstateOffer(models.Model):

    _name = 'estate_property_offer'
    _description = "property_offer"
    _order = "price desc"
    _sql_constraints = [
        ("check_price", "CHECK(price > 0)", "The price must be strictly positive"),
    ]

    price = fields.Float('Price')
    state = fields.Selection([('accepted', 'Accepted'), ('refused', 'Refused')], 'State', copy=False)
    offer_property_id = fields.Many2one('estate_property', 'Offer_ID')
    partner_id = fields.Many2one('res.partner', string='Partnerperson', required=True)
    property_type_id = fields.Many2one('estate_property_type',related="offer_property_id.property_type_id", string="Property Type", store=True)

    def Action_Accepte(self):
        if "accepted" in self.mapped("offer_property_id.property_offer_id.state"):
            raise UserError("An offer as already been accepted.")
        self.write({"state": "accepted"})
       
        return self.mapped("offer_property_id").write(
            {
                "state" : "offer accepted",
                "selling_price" : self.price,
                "buyer_id" : self.partner_id.id,
        }
    )
    
    def Action_Refuse(self):
        return self.write({"state": "refused"})

    @api.model
    def create(self, vals):
        if vals.get("offer_property_id") and vals.get("price"):
            record = self.env['estate_property'].browse(vals['offer_property_id'])

            if record.property_offer_id: 
                max_offer = max(record.mapped("property_offer_id.price"))
                if float_compare(vals["price"], max_offer, precision_rounding=0.01) <= 0:
                    raise UserError("The offer must be higher than %.2f" % max_offer)
        
            record.state = "offer received"
        
        return super().create(vals) 

        
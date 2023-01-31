from odoo import fields, models
from datetime import datetime


class GymEquipments(models.Model):
    _inherit = 'product.template'

    gym_product = fields.Boolean(string='Equipo del Gym')

    def actualizar_membrecia(self):
        if self.membership_date_from != datetime.today():
            self.membership_date_from = datetime.today()

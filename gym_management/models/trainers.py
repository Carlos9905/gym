from odoo import fields, models


class TrainerEmployee(models.Model):
    _inherit = "hr.employee"

    trainer = fields.Boolean(string="Entrenador GYM")
    exercise_for_ids = fields.Many2many("trainer.skill", string="Especializacion")

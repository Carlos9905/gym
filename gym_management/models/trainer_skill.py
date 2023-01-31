from odoo import fields, models

class TrainerSkill(models.Model):
    _name = "trainer.skill"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Trainer Skill"

    name = fields.Char(string="Nombre")
    code = fields.Char(string="Codigo")

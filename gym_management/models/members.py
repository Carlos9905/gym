# -*- coding: utf-8 -*-
from odoo import fields, models, api


class GymMember(models.Model):
    _name = "gym.member"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Miembros del gym"


class MemberPartner(models.Model):
    _inherit = "res.partner"

    gym_member = fields.Boolean(string="Miembro Gym", default=True)
    membership_count = fields.Integer(
        "membership_count", compute="_compute_membership_count"
    )
    def _compute_membership_count(self):
        """número de membresía para miembros del gimnasio"""
        for rec in self:
            rec.membership_count = rec.env["gym.membership"].search_count(
                [("member.id", "=", rec.id)]
            )

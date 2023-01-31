from datetime import datetime
from odoo import api, fields, models, _
import pytz


class GymMembership(models.Model):
    _name = "gym.membership"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Membresías del gym"
    _rec_name = "reference"

    reference = fields.Char(
        string="GYM reference",
        required=True,
        readonly=True,
        default=lambda self: _("New"),
    )
    member = fields.Many2one(
        "res.partner",
        string="Cliente",
        required=True,
        tracking=True,
        domain="[('gym_member', '!=',False)]",
    )    
    membership_scheme = fields.Many2one(
        "product.product",
        string="Tipo de membresía",
        required=True,
        tracking=True,
        domain="[('membership_date_from', '!=',False)]",
    )
    paid_amount = fields.Integer(string="Monto pagado", tracking=True)
    membership_fees = fields.Float(
        string="Costo de la Membresía",
        tracking=True,
        related="membership_scheme.list_price",
    )
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Orden de venta",
        ondelete="cascade",
        copy=False,
        readonly=True,
    )
    factura = fields.Many2one("account.move", string="Numero de factura")
    membership_date_from = fields.Date(
        string="Comienzo de la Membresía",
        compute="get_date_from",
        store=True,
        help="Fecha a partir de la cual se activa la membresía.",
    )
    membership_date_to = fields.Date(
        string="Fin de la Membresía",
        compute="get_date_to",
        store=True,
        help="Fecha hasta la cual la membresía permanece activa.",
    )

    currency_id = fields.Many2one("res.currency", string="Moneda", default=lambda self: self.env.company.currency_id)

    _sql_constraints = [
        (
            "membership_date_greater",
            "check(membership_date_to >= membership_date_from)",
            "Error ! La fecha de finalización no se puede establecer antes de la fecha de inicio.",
        )
    ]
    state = fields.Selection(
        [
            ("borrador", "Borrador"),
            ("pendiente", "Pendiente"),
            ("facturado", "Facturado"),
            ("pagado", "Pagado"),
        ],        
        default="borrador",
        string="Estado",
        compute="_cal_state",
        store=True
    )

    date = fields.Datetime("Fecha", default=datetime.now())

    journals_id = fields.Many2one(
        "account.journal",
        string="Diario",
        default=lambda self: self.env["account.journal"].search(
            [("name", "=", "Caja")]
        ),
    )

    #Calculos
    @api.depends("membership_scheme")
    def get_date_from(self):
        for record in self:
            record.membership_date_from = record.membership_scheme.membership_date_from
    
    #Calculos
    @api.depends("membership_scheme")
    def get_date_to(self):
        for record in self:
            record.membership_date_to = record.membership_scheme.membership_date_to

    #Creando una factura
    def membership_invoice(self):
        factura = self.env["account.move"].create(
            {
                "line_id":self.id,
                "move_type": "out_invoice",
                "partner_id": self.member.id,
                "currency_id":self.currency_id,
                "invoice_line_ids": [
                    (
                        0,
                        None,
                        {
                            "product_id": self.membership_scheme.id,
                            "quantity": 1,
                            "price_unit": self.membership_fees,
                            "tax_ids": [(6, 0, self.membership_scheme.taxes_id.ids)],
                        },
                    )
                ],
            }
        )
        self.state = 'facturado'
        self.factura = factura.id
        factura.action_post()

    def registrar_pago(self):
        for record in self:
            vals = {
                "reconciled_invoice_ids": [(4, record.factura.id)],
                "partner_id": record.member.id,
                "amount": record.paid_amount,
                "date": record.membership_date_from,
                "journal_id": record.journals_id.id,
                "payment_type": "inbound",
                "ref": record.membership_scheme.name,
            }
            self.payment_register(vals,record.factura)

    #Ver facturas pendientes
    def ver_membership_invoice(self):
        search_view_ref = self.env.ref("account.view_account_invoice_filter", False)
        form_view_ref = self.env.ref("account.view_move_form", False)
        tree_view_ref = self.env.ref("account.view_move_tree", False)
        return {
            "domain": [("line_id", "=", self.id), ("payment_state", "in", ("not_paid", "partial"))],
            "name": "Factura de membresía",
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "views": [(tree_view_ref.id, "tree"), (form_view_ref.id, "form")],
            "search_view_id": search_view_ref and [search_view_ref.id],
        }

    @api.model
    def create(self, vals):
        """número de secuencia para membresía"""
        if vals.get("reference", ("New")) == ("New"):
            vals["reference"] = self.env["ir.sequence"].next_by_code(
                "gym.membership"
            ) or ("New")
        vals["state"] = "pendiente"
        res = super(GymMembership, self).create(vals)
        return res

    @api.depends("factura.payment_state")
    def _cal_state(self):
        for record in self:
            if record.factura:
                if record.factura.payment_state == 'paid':
                    record.state = 'pagado'
            else:
                record.state = 'pendiente'

    # Funcion para registrar pagos
    @api.model
    def payment_register(self, vals: dict, invoice):
        """
        Registra un pago y la concilia a una factura
        :param vals: es un diccionario que contiene los datos del pago
        :param invoice: factura la cual se hará la conciliación
        :returns: la conciliacion
        """
        payment = self.env["account.payment"].create(vals)
        payment.action_post()
        inv_receivable = invoice.line_ids.filtered(
            lambda l: l.account_id.internal_type == "receivable"
        )
        pay_receivable = payment.move_id.line_ids.filtered(
            lambda l: l.account_id.internal_type == "receivable"
        )
        # Conciliar el pago con la factura
        return (inv_receivable + pay_receivable).reconcile()

class SaleConfirm(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        """membresía creada directamente desde la orden de venta"""
        product = self.env["product.product"].search(
            [
                ("membership_date_from", "!=", False),
                ("id", "=", self.order_line.product_id.id),
            ]
        )
        for record in product:
            self.env["gym.membership"].create(
                [
                    {
                        "member": self.partner_id.id,
                        "membership_date_from": record.membership_date_from,
                        "membership_scheme": self.order_line.product_id.id,
                        "paid_amount": self.order_line.product_id.lst_price,
                        "sale_order_id": self.id,
                    }
                ]
            )

        res = super(SaleConfirm, self).action_confirm()
        return res
class AccountMove(models.Model):
    _inherit = "account.move"

    line_id = fields.Many2one("gym.membership", string="Membresia a la que pertenece")

from odoo import fields, models


class CrmContactJob(models.Model):
    _name = "crm.contact.job"
    _description = "Cargo de contacto CRM"
    _order = "sequence, name"

    name = fields.Char(string="Cargo", required=True, translate=True, index="trigram")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _name_unique = models.Constraint(
        "UNIQUE(name)",
        "El cargo ya existe.",
    )

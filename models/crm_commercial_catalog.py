from odoo import fields, models


class CrmCommercialCatalog(models.Model):
    _name = "crm.commercial.catalog"
    _description = "Catálogo comercial CRM"
    _order = "category, sequence, name"

    name = fields.Char(string="Nombre", required=True, translate=True)
    code = fields.Char(string="Código", required=True)
    category = fields.Selection(
        [
            ("business_line", "Línea de negocio"),
            ("service_type", "Tipo de servicio"),
            ("solution", "Producto / solución"),
            ("brand", "Marca"),
            ("commercial_situation", "Situación comercial"),
            ("customer_type", "Tipo de cliente"),
        ],
        string="Familia",
        required=True,
        index=True,
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _code_category_unique = models.Constraint(
        "UNIQUE(category, code)",
        "El código debe ser único dentro de cada familia comercial.",
    )

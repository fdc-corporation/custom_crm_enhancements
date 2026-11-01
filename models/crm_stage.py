from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmStage(models.Model):
    _inherit = "crm.stage"

    is_lost = fields.Boolean(string="Etapa de pérdida")

    @api.constrains("is_lost", "is_won")
    def _check_lost_stage(self):
        if any(stage.is_lost and stage.is_won for stage in self):
            raise ValidationError(_("Una etapa no puede ser ganada y perdida a la vez."))

    @api.model
    def _configure_existing_lost_stages(self):
        stages = self.with_context(lang="es_PE").search([("is_won", "=", False)])
        stages.filtered(lambda stage: stage.name.strip().casefold() in ("perdido", "perdida", "perdidos", "lost")).write({"is_lost": True})

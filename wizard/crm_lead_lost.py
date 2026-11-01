from odoo import api, models, _
from odoo.exceptions import ValidationError


class CrmLeadLost(models.TransientModel):
    _inherit = "crm.lead.lost"

    @api.constrains("lost_reason_id")
    def _check_lost_reason(self):
        for wizard in self:
            reason = (wizard.lost_reason_id.name or "").strip()
            if len(reason) < 5:
                raise ValidationError(_("El motivo de pérdida es obligatorio y debe tener al menos 5 caracteres."))

    def action_lost_reason_apply(self):
        self._check_lost_reason()
        stage_id = self.env.context.get("crm_target_lost_stage_id")
        if stage_id:
            stage = self.env["crm.stage"].browse(stage_id).exists()
            if not stage or not stage.is_lost:
                raise ValidationError(_("La etapa seleccionada ya no es una etapa de pérdida."))
            self.lead_ids.with_context(crm_apply_lost=True).write({"stage_id": stage.id})
        return super().action_lost_reason_apply()


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
        return super().action_lost_reason_apply()


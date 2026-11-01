from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = "crm.lead"

    industry_id = fields.Many2one(
        "res.partner.industry", string="Industria", compute="_compute_industry_id",
        inverse="_inverse_industry_id", readonly=False,
    )

    @api.depends(
        "commercial_partner_id", "partner_id.industry_id",
        "partner_id.commercial_partner_id.industry_id",
    )
    def _compute_industry_id(self):
        for lead in self:
            company = lead.commercial_partner_id or lead.partner_id.commercial_partner_id
            lead.industry_id = company.industry_id or lead.partner_id.industry_id

    def _inverse_industry_id(self):
        for lead in self:
            company = lead.commercial_partner_id or lead.partner_id.commercial_partner_id
            if company and company.industry_id != lead.industry_id:
                company.industry_id = lead.industry_id

    def _prepare_opportunity_quotation_context(self):
        context = super()._prepare_opportunity_quotation_context()
        company = self.commercial_partner_id or self.partner_id.commercial_partner_id
        context["default_partner_id"] = (company or self.partner_id).id
        return context

    job_position_id = fields.Many2one(
        "crm.contact.job",
        string="Puesto de trabajo",
        compute="_compute_job_position_id",
        inverse="_inverse_job_position_id",
        store=True,
        readonly=False,
    )

    expected_revenue = fields.Monetary(
        string="Expected Revenue",
        compute="_compute_expected_revenue_from_quotations",
        store=True,
        readonly=True,
        currency_field="company_currency",
        help="Total con impuestos de las cotizaciones vinculadas, convertido a la moneda de la compañía.",
    )

    @api.depends("function", "partner_id", "partner_id.job_position_id")
    def _compute_job_position_id(self):
        jobs = self.env["crm.contact.job"].search([])
        by_name = {job.name.strip().casefold(): job for job in jobs}
        for lead in self:
            lead.job_position_id = (
                lead.partner_id.job_position_id
                if lead.partner_id and not lead.partner_id.is_company
                else by_name.get((lead.function or "").strip().casefold())
            )

    def _inverse_job_position_id(self):
        for lead in self:
            job = lead.job_position_id
            contact = lead.partner_id
            if contact and not contact.is_company and contact.job_position_id != job:
                contact.job_position_id = job
            lead.function = job.name or False

    @api.depends(
        "order_ids.state",
        "order_ids.amount_total",
        "order_ids.currency_id",
        "order_ids.date_order",
        "order_ids.company_id",
    )
    def _compute_expected_revenue_from_quotations(self):
        """Only draft/sent quotations are expected revenue; cancelled/orders are excluded."""
        for lead in self:
            company_currency = lead.company_currency or lead.company_id.currency_id or self.env.company.currency_id
            quotations = lead.order_ids.filtered(lambda order: order.state in ("draft", "sent"))
            lead.expected_revenue = sum(
                order.currency_id._convert(
                    order.amount_total,
                    company_currency,
                    order.company_id,
                    order.date_order or fields.Date.context_today(order),
                )
                for order in quotations
            )

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        unassigned = leads.filtered(lambda lead: lead.type == "opportunity" and not lead.user_id)
        if unassigned:
            managers = self.env.ref("sales_team.group_sale_manager", raise_if_not_found=False)
            manager_users = managers.all_user_ids if managers else self.env["res.users"]
            for lead in unassigned:
                lead._crm_send_alert(
                    manager_users,
                    _("Nueva oportunidad sin asignar"),
                    _("La oportunidad “%s” fue creada y aún no tiene vendedor.", lead.display_name),
                    "warning",
                )
        return leads

    def write(self, vals):
        if vals.get("stage_id") and not self.env.context.get("crm_apply_lost"):
            stage = self.env["crm.stage"].browse(vals["stage_id"])
            if stage.is_lost and any(lead.stage_id != stage for lead in self):
                raise ValidationError(_("Seleccione el motivo de pérdida para mover la oportunidad a esta etapa."))
        previous_users = {lead.id: lead.user_id for lead in self} if "user_id" in vals else {}
        result = super().write(vals)
        if "user_id" in vals:
            for lead in self:
                if lead.type == "opportunity" and lead.user_id and lead.user_id != previous_users.get(lead.id):
                    lead._crm_send_alert(
                        lead.user_id,
                        _("Oportunidad asignada"),
                        _("Se te asignó la oportunidad “%s”.", lead.display_name),
                        "success",
                    )
        return result

    def action_prepare_lost_stage(self, stage_id):
        self.ensure_one()
        stage = self.env["crm.stage"].browse(stage_id).exists()
        if not stage or not stage.is_lost or self.stage_id == stage:
            return False
        return {
            "type": "ir.actions.act_window", "name": _("Motivo de pérdida"),
            "res_model": "crm.lead.lost", "views": [(False, "form")], "target": "new",
            "context": {
                "default_lead_ids": [(6, 0, self.ids)],
                "crm_target_lost_stage_id": stage.id,
            },
        }

    def action_set_lost(self, **additional_values):
        for lead in self:
            stage = lead.stage_id if lead.stage_id.is_lost else lead._stage_find(domain=[("is_lost", "=", True)])
            if not stage:
                raise ValidationError(_("Configure una etapa de pérdida para este equipo de ventas."))
            lead.with_context(crm_apply_lost=True).write({"stage_id": stage.id})
        result = super().action_set_lost(**additional_values)
        managers = self.env.ref("sales_team.group_sale_manager", raise_if_not_found=False)
        for lead in self.filtered(lambda item: item.type == "opportunity"):
            recipients = (managers.all_user_ids if managers else self.env["res.users"]) | lead.user_id
            reason = lead.lost_reason_id.name if lead.lost_reason_id else _("Sin motivo")
            lead._crm_send_alert(
                recipients,
                _("Oportunidad perdida"),
                _("La oportunidad “%(lead)s” se marcó como perdida. Motivo: %(reason)s.", lead=lead.display_name, reason=reason),
                "danger",
            )
        return result

    def _crm_send_alert(self, users, title, message, notification_type="info"):
        self.ensure_one()
        users = users.filtered(lambda user: user.active and not user.share)
        if not users:
            return
        partner_ids = users.partner_id.ids
        self.message_notify(
            partner_ids=partner_ids,
            subject=title,
            body=Markup("<p>%s</p>") % message,
        )
        payload = {
            "title": title,
            "message": message,
            "type": notification_type,
            "res_model": self._name,
            "res_id": self.id,
        }
        for user in users:
            user._bus_send("crm_akane/alert", payload)


class CrmLostReason(models.Model):
    _inherit = "crm.lost.reason"

    @api.constrains("name")
    def _check_name_minimum_length(self):
        for reason in self:
            if len((reason.name or "").strip()) < 5:
                raise ValidationError(_("El motivo de pérdida debe tener al menos 5 caracteres."))


from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = "crm.lead"

    job_position_id = fields.Many2one(
        "crm.contact.job",
        string="Puesto de trabajo",
        compute="_compute_job_position_id",
        inverse="_inverse_job_position_id",
        store=True,
        readonly=False,
    )

    industry_id = fields.Many2one(
        "res.partner.industry",
        string="Industria",
        compute="_compute_industry_id",
        inverse="_inverse_industry_id",
        readonly=False,
    )

    expected_revenue = fields.Monetary(
        string="Expected Revenue",
        compute="_compute_expected_revenue_from_quotations",
        store=False,
        readonly=True,
        currency_field="company_currency",
        help="Total con impuestos de las cotizaciones y órdenes de venta vinculadas, excepto canceladas.",
    )

    @api.depends("function")
    def _compute_job_position_id(self):
        jobs = self.env["crm.contact.job"].search([])
        by_name = {job.name.strip().casefold(): job for job in jobs}
        for lead in self:
            lead.job_position_id = by_name.get((lead.function or "").strip().casefold())

    def _inverse_job_position_id(self):
        for lead in self:
            lead.function = lead.job_position_id.name or False

    @api.depends("commercial_partner_id", "partner_id")
    def _compute_industry_id(self):
        for lead in self:
            company = lead.commercial_partner_id
            if not company and lead.partner_id:
                company = lead.partner_id.commercial_partner_id
            lead.industry_id = company.industry_id if company and company.is_company else False

    def _inverse_industry_id(self):
        for lead in self:
            company = lead.commercial_partner_id
            if not company and lead.partner_id:
                company = lead.partner_id.commercial_partner_id
            if company and company.is_company:
                company.industry_id = lead.industry_id

    def _prepare_opportunity_quotation_context(self):
        """Dirige las cotizaciones a la empresa, nunca al contacto individual."""
        self.ensure_one()
        context = super()._prepare_opportunity_quotation_context()
        company = self.commercial_partner_id
        if not company and self.partner_id:
            company = self.partner_id.commercial_partner_id
        if not company or not company.is_company:
            raise ValidationError(
                _("Seleccione una empresa para la oportunidad antes de crear la cotización.")
            )
        context["default_partner_id"] = company.id
        return context

    @api.depends(
        "email_domain_criterion",
        "email_normalized",
        "partner_id",
        "phone_sanitized",
    )
    def _compute_potential_lead_duplicates(self):
        """Calcula duplicados sin exponer ni abrir CRM de otros vendedores.

        El cálculo estándar necesita leer los candidatos coincidentes. Se hace
        con sudo para que un candidato ajeno no provoque AccessError, pero el
        resultado se vuelve a filtrar con los permisos reales del vendedor.
        """
        elevated_leads = self.sudo()
        super(CrmLead, elevated_leads)._compute_potential_lead_duplicates()

        Lead = self.env["crm.lead"].with_context(active_test=False)
        for lead, elevated_lead in zip(self, elevated_leads):
            duplicate_ids = elevated_lead.duplicate_lead_ids.ids
            visible_duplicates = Lead.search([("id", "in", duplicate_ids)]) if duplicate_ids else Lead
            lead.duplicate_lead_ids = visible_duplicates
            lead.duplicate_lead_count = len(visible_duplicates - lead)

    @api.depends(
        "order_ids.state",
        "order_ids.amount_total",
        "order_ids.currency_id",
        "order_ids.date_order",
        "order_ids.company_id",
    )
    def _compute_expected_revenue_from_quotations(self):
        """Calcula en cada lectura cotizaciones y órdenes vinculadas, con impuestos."""
        SaleOrder = self.env["sale.order"]
        for lead in self:
            company_currency = lead.company_currency or lead.company_id.currency_id or self.env.company.currency_id
            orders = (
                SaleOrder.search([
                    ("opportunity_id", "=", lead.id),
                    ("state", "!=", "cancel"),
                ])
                if lead.id
                else SaleOrder
            )
            lead.expected_revenue = sum(
                order.currency_id._convert(
                    order.amount_total,
                    company_currency,
                    order.company_id,
                    order.date_order or fields.Date.context_today(order),
                )
                for order in orders
            )

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        unassigned = leads.filtered(lambda lead: lead.type == "opportunity" and not lead.user_id)
        if unassigned:
            managers = self.env.ref("sales_team.group_sale_manager", raise_if_not_found=False)
            manager_users = managers.users if managers else self.env["res.users"]
            for lead in unassigned:
                lead._crm_send_alert(
                    manager_users,
                    _("Nueva oportunidad sin asignar"),
                    _("La oportunidad “%s” fue creada y aún no tiene vendedor.", lead.display_name),
                    "warning",
                )
        return leads

    def write(self, vals):
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

    def action_set_lost(self, **additional_values):
        result = super().action_set_lost(**additional_values)
        managers = self.env.ref("sales_team.group_sale_manager", raise_if_not_found=False)
        for lead in self.filtered(lambda item: item.type == "opportunity"):
            recipients = (managers.users if managers else self.env["res.users"]) | lead.user_id
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


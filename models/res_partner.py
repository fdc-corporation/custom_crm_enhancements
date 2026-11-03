from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    job_position_id = fields.Many2one(
        "crm.contact.job",
        string="Puesto de trabajo",
        compute="_compute_job_position_id",
        inverse="_inverse_job_position_id",
        store=True,
        readonly=False,
    )

    @api.depends("function")
    def _compute_job_position_id(self):
        jobs = self.env["crm.contact.job"].search([])
        by_name = {job.name.strip().casefold(): job for job in jobs}
        for partner in self:
            partner.job_position_id = by_name.get((partner.function or "").strip().casefold())

    def _inverse_job_position_id(self):
        for partner in self:
            partner.function = partner.job_position_id.name or False

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if self.env.context.get("crm_create_company_contact"):
            parent_id = self.env.context.get("default_parent_id")
            if parent_id:
                values.update({
                    "parent_id": parent_id,
                    "is_company": False,
                    "company_type": "person",
                })
            vat_type = self.env.ref("l10n_latam_base.it_vat", raise_if_not_found=False)
            if vat_type and "l10n_latam_identification_type_id" in self._fields:
                values["l10n_latam_identification_type_id"] = vat_type.id
        return values

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get("crm_create_company_contact"):
            parent_id = self.env.context.get("default_parent_id")
            vat_type = self.env.ref("l10n_latam_base.it_vat", raise_if_not_found=False)
            for values in vals_list:
                if parent_id:
                    values.update({
                        "parent_id": parent_id,
                        "is_company": False,
                        "company_type": "person",
                    })
                if vat_type and "l10n_latam_identification_type_id" in self._fields:
                    values["l10n_latam_identification_type_id"] = vat_type.id
        return super().create(vals_list)

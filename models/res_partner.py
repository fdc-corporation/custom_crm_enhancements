from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        dni = self.env.ref("l10n_pe.it_DNI", raise_if_not_found=False)
        is_company = values.get("is_company", self.env.context.get("default_is_company", False))
        if dni and not is_company and "l10n_latam_identification_type_id" in fields_list:
            values["l10n_latam_identification_type_id"] = dni.id
        return values

    @api.model
    def _commercial_fields(self):
        names = super()._commercial_fields()
        if self.env.ref("l10n_pe.it_DNI", raise_if_not_found=False):
            names = [name for name in names if name not in ("vat", "l10n_latam_identification_type_id")]
        return names

    @api.model
    def _synced_commercial_fields(self):
        names = super()._synced_commercial_fields()
        if self.env.ref("l10n_pe.it_DNI", raise_if_not_found=False):
            names = [name for name in names if name not in ("vat", "l10n_latam_identification_type_id")]
        return names

    @api.onchange("parent_id", "is_company")
    def _onchange_parent_document(self):
        dni = self.env.ref("l10n_pe.it_DNI", raise_if_not_found=False)
        for partner in self:
            if dni and not partner.is_company and not partner._origin.id:
                partner.l10n_latam_identification_type_id = dni

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

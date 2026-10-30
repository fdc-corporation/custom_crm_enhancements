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

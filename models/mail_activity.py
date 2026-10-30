from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MailActivity(models.Model):
    _inherit = "mail.activity"

    crm_deadline_datetime = fields.Datetime(
        string="Fecha y hora",
        index=True,
        help="Fecha y hora exactas de la actividad CRM.",
    )
    crm_reminder_minutes = fields.Integer(
        string="Recordar antes (minutos)",
        default=15,
    )
    crm_notification_sent = fields.Boolean(default=False, copy=False)

    @api.constrains("crm_reminder_minutes")
    def _check_crm_reminder_minutes(self):
        for activity in self:
            if activity.crm_reminder_minutes < 0:
                raise ValidationError(_("Los minutos del recordatorio no pueden ser negativos."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("crm_deadline_datetime"):
                vals["date_deadline"] = fields.Datetime.to_datetime(vals["crm_deadline_datetime"]).date()
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        if vals.get("crm_deadline_datetime"):
            vals["date_deadline"] = fields.Datetime.to_datetime(vals["crm_deadline_datetime"]).date()
            vals["crm_notification_sent"] = False
        if "crm_reminder_minutes" in vals:
            vals["crm_notification_sent"] = False
        return super().write(vals)

    @api.model
    def _cron_notify_crm_deadlines(self):
        now = fields.Datetime.now()
        activities = self.search([
            ("active", "=", True),
            ("res_model", "=", "crm.lead"),
            ("crm_deadline_datetime", "!=", False),
            ("crm_notification_sent", "=", False),
        ])
        due = activities.filtered(
            lambda activity: activity.crm_deadline_datetime - timedelta(minutes=activity.crm_reminder_minutes) <= now
        )
        for activity in due:
            title = _("Actividad CRM próxima")
            message = _("%(summary)s — %(record)s", summary=activity.summary or activity.activity_type_id.display_name, record=activity.res_name)
            activity.user_id._bus_send("crm_akane/alert", {
                "title": title,
                "message": message,
                "type": "warning",
                "res_model": activity.res_model,
                "res_id": activity.res_id,
            })
            activity.action_notify()
            activity.crm_notification_sent = True


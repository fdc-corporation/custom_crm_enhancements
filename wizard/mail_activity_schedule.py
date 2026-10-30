from odoo import fields, models


class MailActivitySchedule(models.TransientModel):
    _inherit = "mail.activity.schedule"

    crm_deadline_datetime = fields.Datetime(string="Fecha y hora")
    crm_reminder_minutes = fields.Integer(string="Recordar antes (minutos)", default=15)

    def _action_schedule_activities(self):
        activities = super()._action_schedule_activities()
        if self.res_model == "crm.lead" and self.crm_deadline_datetime:
            activities.write({
                "crm_deadline_datetime": self.crm_deadline_datetime,
                "crm_reminder_minutes": self.crm_reminder_minutes,
            })
        return activities


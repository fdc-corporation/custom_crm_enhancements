{
    "name": "CRM Akane Enhancements",
    "version": "19.0.2.0.0",
    "category": "Sales/CRM",
    "summary": "Mejoras de actividades, cotizaciones, Kanban y alertas del CRM",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["crm", "sale_crm", "mail", "l10n_latam_base"],
    "data": [
        "security/crm_access_rules.xml",
        "security/ir.model.access.csv",
        "data/crm_contact_job_data.xml",
        "data/crm_commercial_catalog_data.xml",
        "data/ir_cron_data.xml",
        "views/crm_commercial_catalog_views.xml",
        "views/res_partner_views.xml",
        "views/crm_lead_views.xml",
        "views/mail_activity_views.xml",
        "wizard/crm_lead_lost_views.xml",
        "wizard/mail_activity_schedule_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "custom_crm_enhancements/static/src/js/crm_notification_service.js",
        ],
    },
    "post_init_hook": "_post_init_hook",
    "installable": True,
    "application": False,
}


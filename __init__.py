from . import models
from . import wizard


def _post_init_hook(env):
    env["res.partner"].search([("function", "!=", False)]).modified(["function"])
    env["crm.lead"].search([("function", "!=", False)]).modified(["function"])
    env.flush_all()


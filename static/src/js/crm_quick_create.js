/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { KanbanQuickCreateController } from "@web/views/kanban/kanban_record_quick_create";

patch(KanbanQuickCreateController.prototype, {
    setup() {
        super.setup(...arguments);
        this.crmAction = useService("action");
    },

    async validate(mode) {
        if (this.props.resModel !== "crm.lead") {
            return super.validate(mode);
        }
        if (this.state.disabled) {
            return;
        }
        this.state.disabled = true;
        try {
            const saved = await this.model.root.save({
                reload: false,
                // Keep the entered values and surface the error if saving fails.
                onError: (error) => { throw error; },
            });
            if (!saved || !this.model.root.resId) {
                return;
            }
            const resId = this.model.root.resId;
            await this.props.onValidate(resId, "add");
            await this.crmAction.doAction({
                type: "ir.actions.act_window",
                res_model: "crm.lead",
                res_id: resId,
                views: [[false, "form"]],
                target: "current",
            });
        } finally {
            this.state.disabled = false;
        }
    },
});

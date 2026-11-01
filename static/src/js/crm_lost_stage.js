/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Record } from "@web/model/relational_model/record";
import { CrmKanbanDynamicGroupList } from "@crm/views/crm_kanban/crm_kanban_model";

patch(CrmKanbanDynamicGroupList.prototype, {
    async moveRecord(dataRecordId, dataGroupId, refId, targetGroupId) {
        const source = this.groups.find((group) => group.id === dataGroupId);
        const target = this.groups.find((group) => group.id === targetGroupId);
        const record = source?.list.records.find((item) => item.id === dataRecordId);
        if (record && target?.groupByField.name === "stage_id" && dataGroupId !== targetGroupId && target.value) {
            const action = await this.model.orm.call(
                "crm.lead", "action_prepare_lost_stage", [[record.resId], target.value],
                { context: record.context }
            );
            if (action) {
                // Stop before CRM moves the card and checks the destination for
                // its won-stage effect. The wizard applies the move on confirmation.
                await this.model.action.doAction(action, {
                    onClose: () => this.model.load(),
                });
                return;
            }
        }
        return super.moveRecord(...arguments);
    },
});

patch(Record.prototype, {
    async update(changes, options) {
        const stageId = changes.stage_id?.id;
        if (this.resModel === "crm.lead" && this.resId && stageId && stageId !== this.data.stage_id?.id) {
            const action = await this.model.orm.call(
                "crm.lead", "action_prepare_lost_stage", [[this.resId], stageId],
                { context: this.context }
            );
            if (action) {
                // Do not move the card until the user confirms the reason.
                // Kanban moves are handled above; this handles the form status bar.
                await this.model.action.doAction(action, {
                    onClose: () => this.model.load(),
                });
                return false;
            }
        }
        return super.update(changes, options);
    },
});

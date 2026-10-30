/** @odoo-module **/

import { registry } from "@web/core/registry";

let audioContext;

const crmAkaneNotificationService = {
    dependencies: ["bus_service", "notification", "action"],

    start(env, { bus_service, notification, action }) {
        globalThis.addEventListener("pointerdown", unlockAudio, { once: true });
        bus_service.subscribe("crm_akane/alert", (payload) => {
            notification.add(payload.message, {
                title: payload.title,
                type: payload.type || "info",
                sticky: payload.type === "danger",
                buttons: payload.res_model && payload.res_id
                    ? [{
                        name: "Abrir",
                        primary: true,
                        onClick: () => action.doAction({
                            type: "ir.actions.act_window",
                            res_model: payload.res_model,
                            res_id: payload.res_id,
                            views: [[false, "form"]],
                            target: "current",
                        }),
                    }]
                    : [],
            });
            playNotificationTone();
        });
        bus_service.start();
    },
};

function playNotificationTone() {
    const AudioContext = globalThis.AudioContext || globalThis.webkitAudioContext;
    if (!AudioContext) {
        return;
    }
    audioContext ||= new AudioContext();
    if (audioContext.state !== "running") {
        audioContext.resume();
    }
    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(880, audioContext.currentTime);
    oscillator.frequency.setValueAtTime(1175, audioContext.currentTime + 0.12);
    gain.gain.setValueAtTime(0.0001, audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.18, audioContext.currentTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.32);
    oscillator.connect(gain);
    gain.connect(audioContext.destination);
    oscillator.start();
    oscillator.stop(audioContext.currentTime + 0.34);
}

function unlockAudio() {
    const AudioContext = globalThis.AudioContext || globalThis.webkitAudioContext;
    if (!AudioContext) {
        return;
    }
    audioContext ||= new AudioContext();
    audioContext.resume();
}

registry.category("services").add("crm_akane_notification", crmAkaneNotificationService);


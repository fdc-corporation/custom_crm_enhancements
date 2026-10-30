# CRM Akane Enhancements — Odoo 19

Módulo único para las mejoras solicitadas del CRM.

## Alcance implementado

1. Fecha y hora en actividades CRM, con recordatorio configurable en minutos.
2. Monto esperado calculado desde la suma de cotizaciones en borrador/enviadas, incluido IGV (`amount_total`).
3. Cargo del contacto visible en la tarjeta Kanban.
4. Selector y borde de color eliminados del Kanban CRM.
5. Filtro visible **Actividades de hoy**.
6. Alertas persistentes y emergentes con sonido para:
   - oportunidad nueva sin vendedor (gerentes CRM);
   - oportunidad perdida (gerentes CRM y vendedor asignado);
   - nueva asignación (vendedor asignado);
   - recordatorio de actividad (responsable de la actividad).
7. Motivo de pérdida obligatorio, con mínimo 5 caracteres.

## Instalación

Copiar `custom_crm_enhancements` a una ruta incluida en `addons_path`, actualizar la lista de aplicaciones e instalar **CRM Akane Enhancements**. Reiniciar Odoo y regenerar los assets si el entorno no lo hace automáticamente.

## Criterios funcionales asumidos

- “Cotización” significa `sale.order` en estado `draft` o `sent`; pedidos confirmados y cancelados no forman parte del monto esperado.
- Los importes en otras monedas se convierten a la moneda de la compañía usando la fecha de la cotización.
- Los gerentes CRM son los destinatarios de alertas globales (sin asignar/perdidas).
- El sonido requiere que el navegador haya permitido audio después de una interacción del usuario; es una restricción normal de los navegadores.

## Plan de implementación

### Fase 1 — Validación y línea base

- Confirmar edición Community/Enterprise, repositorio exacto de Odoo 19 y módulos instalados (`crm`, `sale_crm`, `mail`).
- Respaldar base de datos y filestore; preparar ambiente de staging.
- Validar destinatarios y reglas de cómputo con usuarios clave.

### Fase 2 — Instalación técnica

- Incorporar el add-on y actualizar aplicaciones.
- Instalar en staging y verificar carga de XML, Python y assets web.
- Revisar permisos de los grupos de Ventas/CRM y configuración de notificaciones de cada usuario.

### Fase 3 — Pruebas funcionales

- Crear oportunidades con/sin vendedor y comprobar alertas.
- Reasignar una oportunidad y comprobar que solo el nuevo vendedor recibe la alerta.
- Crear cotizaciones con IGV, varias monedas y estados diferentes; cotejar el monto esperado.
- Programar actividades con fecha/hora y recordatorios vencidos/futuros.
- Marcar oportunidades como perdidas con motivo vacío, corto y válido.
- Revisar Kanban en escritorio y móvil.

### Fase 4 — Calidad y despliegue

- Ejecutar pruebas automatizadas y una UAT con ventas.
- Desplegar fuera del horario operativo, actualizar el módulo y limpiar assets si corresponde.
- Monitorear cron, cola de correo y logs durante 48 horas.
- Documentar rollback: desactivar el cron, revertir el add-on y restaurar respaldo si hubiera una incidencia crítica.


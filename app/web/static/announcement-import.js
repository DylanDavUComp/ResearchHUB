// Importacion de comunicados desde un archivo JSON (uno o varios). Primero se
// valida en el servidor sin crear nada y se muestra el informe; al confirmar se
// crean todos como borradores por aprobar, o ninguno si alguno tiene errores.

const announcementImportElements = {
  button: document.querySelector("#import-announcements-button"),
  file: document.querySelector("#import-announcements-file"),
  dialog: document.querySelector("#announcement-import-dialog"),
  fileName: document.querySelector("#announcement-import-file"),
  summary: document.querySelector("#announcement-import-summary"),
  list: document.querySelector("#announcement-import-list"),
  confirm: document.querySelector("#confirm-announcement-import"),
  cancel: document.querySelector("#cancel-announcement-import"),
  close: document.querySelector("#close-announcement-import"),
};

const announcementImportMaxBytes = 5 * 1024 * 1024;
let pendingAnnouncementImport = null;

function announcementImportNode(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function describeJsonError(error, text) {
  const position = Number((error.message.match(/position (\d+)/) || [])[1]);
  if (!Number.isFinite(position)) return "El archivo no es un JSON válido.";
  const before = text.slice(0, position).split("\n");
  return `El archivo no es un JSON válido: revisa la línea ${before.length}, columna ${before.at(-1).length + 1}.`;
}

async function requestAnnouncementImport(payload, dryRun) {
  const response = await apiFetch(`/api/v1/admin/announcements/import?dry_run=${dryRun}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  let body = null;
  try {
    body = await response.json();
  } catch (error) {
    // Sin JSON: se informa el mensaje general.
  }
  if (response.ok) return body;
  const report = body?.error?.details?.report;
  if (report) return report;
  throw new Error(body?.error?.message || "No fue posible revisar el archivo.");
}

function renderAnnouncementImportReport(report) {
  const elements = announcementImportElements;
  const invalid = report.total - report.valid;
  elements.summary.textContent = invalid
    ? `${report.valid} de ${report.total} listos. Corrige ${invalid} ${invalid === 1 ? "comunicado" : "comunicados"} y vuelve a cargar el archivo: no se importará ninguno mientras haya errores.`
    : `${report.total} ${report.total === 1 ? "comunicado listo" : "comunicados listos"} para importar como borradores por aprobar.`;
  elements.summary.classList.toggle("has-errors", Boolean(invalid));
  elements.list.replaceChildren(
    ...report.items.map((item) => {
      const row = announcementImportNode("li", item.errors.length ? "has-errors" : "");
      const heading = announcementImportNode("div", "import-item-heading");
      heading.append(
        announcementImportNode("strong", "", item.title),
        announcementImportNode(
          "span",
          `status-pill ${item.errors.length ? "import-status-error" : "announcement-status-draft"}`,
          item.errors.length ? `${item.errors.length} ${item.errors.length === 1 ? "error" : "errores"}` : "Listo",
        ),
      );
      const meta = [announcementAdminCategoryCopy[item.category] || item.category, `${item.blocks} ${item.blocks === 1 ? "bloque" : "bloques"}`]
        .filter(Boolean)
        .join(" · ");
      row.append(heading, announcementImportNode("small", "table-secondary", meta));
      if (item.errors.length) {
        const errors = announcementImportNode("ul", "import-errors");
        item.errors.forEach((issue) => {
          const entry = announcementImportNode("li");
          entry.append(announcementImportNode("code", "", issue.field), document.createTextNode(`: ${issue.message}`));
          errors.append(entry);
        });
        row.append(errors);
      }
      return row;
    }),
  );
  elements.confirm.disabled = Boolean(invalid);
  elements.confirm.textContent = invalid
    ? "Corrige los errores para importar"
    : `Importar ${report.total} ${report.total === 1 ? "borrador" : "borradores"}`;
}

async function reviewAnnouncementFile(file) {
  const elements = announcementImportElements;
  pendingAnnouncementImport = null;
  elements.fileName.textContent = file.name;
  elements.list.replaceChildren();
  elements.confirm.disabled = true;
  elements.confirm.textContent = "Importar borradores";
  elements.summary.classList.remove("has-errors");
  elements.summary.textContent = "Revisando el archivo…";
  if (!elements.dialog.open) elements.dialog.showModal();
  if (file.size > announcementImportMaxBytes) {
    elements.summary.textContent = "El archivo supera 5 MB. Divídelo en varios archivos.";
    elements.summary.classList.add("has-errors");
    return;
  }
  const text = await file.text();
  let payload;
  try {
    payload = JSON.parse(text.replace(/^﻿/, ""));
  } catch (error) {
    elements.summary.textContent = describeJsonError(error, text);
    elements.summary.classList.add("has-errors");
    return;
  }
  try {
    const report = await requestAnnouncementImport(payload, true);
    pendingAnnouncementImport = payload;
    renderAnnouncementImportReport(report);
    elements.confirm.focus();
  } catch (error) {
    elements.summary.textContent = error.message;
    elements.summary.classList.add("has-errors");
  }
}

async function confirmAnnouncementImport() {
  const elements = announcementImportElements;
  if (!pendingAnnouncementImport) return;
  elements.confirm.disabled = true;
  elements.summary.textContent = "Importando…";
  try {
    const report = await requestAnnouncementImport(pendingAnnouncementImport, false);
    if (!report.created) {
      renderAnnouncementImportReport(report);
      return;
    }
    pendingAnnouncementImport = null;
    elements.dialog.close();
    await loadAnnouncementSettings();
    elements.button.focus();
    announcementAdminElements.pending.textContent = `Se importaron ${report.created} ${
      report.created === 1 ? "borrador" : "borradores"
    }. Revísalos y apruébalos para publicarlos.`;
  } catch (error) {
    elements.summary.textContent = error.message;
    elements.summary.classList.add("has-errors");
    elements.confirm.disabled = false;
  }
}

announcementImportElements.button.addEventListener("click", () => {
  announcementImportElements.file.value = "";
  announcementImportElements.file.click();
});
announcementImportElements.file.addEventListener("change", () => {
  const [file] = announcementImportElements.file.files;
  if (file) reviewAnnouncementFile(file);
});
announcementImportElements.confirm.addEventListener("click", confirmAnnouncementImport);
[announcementImportElements.cancel, announcementImportElements.close].forEach((button) => {
  button.addEventListener("click", () => announcementImportElements.dialog.close());
});
// Tambien se puede soltar el archivo sobre la tabla de comunicados.
const announcementImportDropZone = document.querySelector("#announcement-settings-card");
announcementImportDropZone.addEventListener("dragover", (event) => {
  if ([...event.dataTransfer.types].includes("Files")) {
    event.preventDefault();
    announcementImportDropZone.classList.add("is-dropping");
  }
});
announcementImportDropZone.addEventListener("dragleave", () => announcementImportDropZone.classList.remove("is-dropping"));
announcementImportDropZone.addEventListener("drop", (event) => {
  announcementImportDropZone.classList.remove("is-dropping");
  const file = [...event.dataTransfer.files].find((item) => /\.json$/i.test(item.name));
  if (!file) return;
  event.preventDefault();
  reviewAnnouncementFile(file);
});

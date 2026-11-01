// Aprobacion de comunicados de la portada en la consola de configuracion general.
// Un borrador espera revision: se ajusta, se aprueba (publica) o no se aprueba
// (se descarta). El backend solo acepta estas operaciones de un superadministrador.

const announcementAdminCategoryCopy = {
  NOTICIA: "Noticia",
  COMUNICADO: "Comunicado",
  EVENTO: "Evento",
  CONVOCATORIA: "Convocatoria",
};

const announcementAdminStatusCopy = {
  DRAFT: "Por aprobar",
  PUBLISHED: "Publicado",
  WITHDRAWN: "Retirado",
};

const announcementAdminDateFormat = new Intl.DateTimeFormat("es-CO", {
  day: "numeric",
  month: "long",
  year: "numeric",
});

const announcementAdminElements = {
  body: document.querySelector("#announcement-settings-body"),
  pending: document.querySelector("#announcement-pending"),
  newButton: document.querySelector("#new-announcement-button"),
  dialog: document.querySelector("#announcement-dialog"),
  form: document.querySelector("#announcement-form"),
  formTitle: document.querySelector("#announcement-form-title"),
  id: document.querySelector("#announcement-id"),
  version: document.querySelector("#announcement-version"),
  category: document.querySelector("#announcement-category"),
  link: document.querySelector("#announcement-link"),
  imageUrl: document.querySelector("#announcement-image-url"),
  imageAlt: document.querySelector("#announcement-image-alt"),
  title: document.querySelector("#announcement-title"),
  summary: document.querySelector("#announcement-summary"),
  bodyText: document.querySelector("#announcement-body"),
  message: document.querySelector("#announcement-form-message"),
  hint: document.querySelector("#announcement-form-hint"),
  close: document.querySelector("#close-announcement-form"),
  cancel: document.querySelector("#cancel-announcement-form"),
};

let managedAnnouncements = [];

function announcementAdminNode(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function announcementAdminJson(url, options = {}) {
  const response = await apiFetch(url, options);
  if (!response.ok) {
    let message = "No fue posible completar la operación.";
    try {
      const payload = await response.json();
      message = payload.error?.message || payload.detail?.[0]?.msg || message;
    } catch (error) {
      message = "El servidor devolvió una respuesta no válida.";
    }
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

function announcementRowMessage(message) {
  const row = document.createElement("tr");
  const cell = announcementAdminNode("td", "", message);
  cell.colSpan = 5;
  row.append(cell);
  announcementAdminElements.body.replaceChildren(row);
}

function renderPendingCount() {
  const pending = managedAnnouncements.filter((item) => item.status === "DRAFT").length;
  announcementAdminElements.pending.textContent = pending
    ? `${pending} ${pending === 1 ? "comunicado espera" : "comunicados esperan"} tu aprobación.`
    : "No hay comunicados pendientes de aprobación.";
}

async function loadAnnouncementSettings() {
  announcementRowMessage("Cargando comunicados...");
  try {
    const payload = await announcementAdminJson("/api/v1/admin/announcements?page_size=100");
    // Los pendientes de aprobacion van primero; el resto conserva el orden del servidor.
    managedAnnouncements = [...payload.data].sort(
      (a, b) => Number(b.status === "DRAFT") - Number(a.status === "DRAFT"),
    );
    renderPendingCount();
    renderAnnouncementSettings();
  } catch (error) {
    announcementAdminElements.pending.textContent = "";
    announcementRowMessage(error.message);
  }
}

function announcementActionButton(label, action, variant = "", itemTitle = "") {
  const button = announcementAdminNode("button", `table-button ${variant}`, label);
  button.type = "button";
  if (itemTitle) button.setAttribute("aria-label", `${label}: ${itemTitle}`);
  button.addEventListener("click", action);
  return button;
}

function renderAnnouncementSettings() {
  if (!managedAnnouncements.length) {
    announcementRowMessage("Todavía no hay comunicados. Crea el primero con «Nuevo comunicado».");
    return;
  }
  announcementAdminElements.body.replaceChildren(
    ...managedAnnouncements.map((item) => {
      const row = document.createElement("tr");
      const title = announcementAdminNode("td");
      title.append(
        announcementAdminNode("strong", "", item.title),
        announcementAdminNode("small", "table-secondary", item.summary),
      );
      const status = announcementAdminNode("td");
      status.append(
        announcementAdminNode(
          "span",
          `status-pill announcement-status-${item.status.toLowerCase()}`,
          announcementAdminStatusCopy[item.status],
        ),
      );
      const actions = announcementAdminNode("td");
      const wrap = announcementAdminNode("div", "action-buttons");
      if (item.status === "DRAFT") {
        wrap.append(
          announcementActionButton("Revisar y ajustar", () => openAnnouncementDialog(item), "", item.title),
          announcementActionButton("Aprobar y publicar", () => approveAnnouncement(item), "approve", item.title),
          announcementActionButton("No aprobar", () => rejectAnnouncement(item), "danger", item.title),
        );
      } else if (item.status === "WITHDRAWN") {
        wrap.append(
          announcementActionButton("Editar", () => openAnnouncementDialog(item), "", item.title),
          announcementActionButton("Volver a publicar", () => approveAnnouncement(item), "approve", item.title),
          announcementActionButton("Eliminar", () => deleteAnnouncement(item), "danger", item.title),
        );
      } else {
        wrap.append(
          announcementActionButton("Editar", () => openAnnouncementDialog(item), "", item.title),
          announcementActionButton("Retirar", () => withdrawAnnouncement(item), "", item.title),
          announcementActionButton("Eliminar", () => deleteAnnouncement(item), "danger", item.title),
        );
      }
      actions.append(wrap);
      row.append(
        title,
        announcementAdminNode("td", "", announcementAdminCategoryCopy[item.category]),
        status,
        announcementAdminNode(
          "td",
          "",
          item.published_at ? announcementAdminDateFormat.format(new Date(item.published_at)) : "—",
        ),
        actions,
      );
      return row;
    }),
  );
}

function openAnnouncementDialog(item = null) {
  const form = announcementAdminElements;
  form.form.reset();
  form.message.textContent = "";
  form.id.value = item?.id || "";
  form.version.value = item?.version || "";
  form.category.value = item?.category || "NOTICIA";
  form.link.value = item?.link_url || "";
  form.imageUrl.value = item?.image_url || "";
  form.imageAlt.value = item?.image_alt || "";
  form.title.value = item?.title || "";
  form.summary.value = item?.summary || "";
  form.bodyText.value = item?.body || "";
  const isPublished = item?.status === "PUBLISHED";
  form.formTitle.textContent = !item
    ? "Nuevo comunicado"
    : item.status === "DRAFT"
      ? "Revisar comunicado"
      : "Editar comunicado";
  form.hint.textContent = isPublished
    ? "Está publicado: los cambios se verán de inmediato en la portada."
    : "";
  form.hint.classList.toggle("is-hidden", !isPublished);
  form.dialog.showModal();
}

async function saveAnnouncement(event) {
  event.preventDefault();
  const form = announcementAdminElements;
  const id = form.id.value;
  const payload = {
    category: form.category.value,
    title: form.title.value.trim(),
    summary: form.summary.value.trim(),
    body: form.bodyText.value.trim(),
    link_url: form.link.value.trim() || null,
    image_url: form.imageUrl.value.trim() || null,
    image_alt: form.imageAlt.value.trim() || null,
  };
  if (id) payload.version = Number(form.version.value);
  form.message.textContent = "Guardando...";
  try {
    await announcementAdminJson(id ? `/api/v1/admin/announcements/${id}` : "/api/v1/admin/announcements", {
      method: id ? "PATCH" : "POST",
      body: JSON.stringify(payload),
    });
    form.dialog.close();
    await loadAnnouncementSettings();
  } catch (error) {
    form.message.textContent = error.message;
  }
}

async function runAnnouncementAction(request) {
  try {
    await request();
    await loadAnnouncementSettings();
  } catch (error) {
    window.alert(error.message);
  }
}

function approveAnnouncement(item) {
  if (!window.confirm(`¿Aprobar y publicar en la portada "${item.title}"?`)) return;
  runAnnouncementAction(() =>
    announcementAdminJson(`/api/v1/admin/announcements/${item.id}/publication`, {
      method: "POST",
      body: JSON.stringify({ version: item.version }),
    }),
  );
}

function withdrawAnnouncement(item) {
  if (!window.confirm(`¿Retirar de la portada "${item.title}"?`)) return;
  runAnnouncementAction(() =>
    announcementAdminJson(`/api/v1/admin/announcements/${item.id}/withdrawal`, {
      method: "POST",
      body: JSON.stringify({ version: item.version }),
    }),
  );
}

function deleteAnnouncement(item) {
  const warning = item.status === "PUBLISHED"
    ? "Se quitará de la portada y se eliminará definitivamente."
    : "Se eliminará definitivamente.";
  if (!window.confirm(`¿Eliminar "${item.title}"? ${warning}`)) return;
  runAnnouncementAction(() =>
    announcementAdminJson(`/api/v1/admin/announcements/${item.id}`, { method: "DELETE" }),
  );
}

function rejectAnnouncement(item) {
  if (!window.confirm(`¿No aprobar "${item.title}"? El borrador se elimina y no se publica.`)) return;
  runAnnouncementAction(() =>
    announcementAdminJson(`/api/v1/admin/announcements/${item.id}`, { method: "DELETE" }),
  );
}

announcementAdminElements.newButton.addEventListener("click", () => openAnnouncementDialog());
announcementAdminElements.form.addEventListener("submit", saveAnnouncement);
[announcementAdminElements.close, announcementAdminElements.cancel].forEach((button) => {
  button.addEventListener("click", () => announcementAdminElements.dialog.close());
});

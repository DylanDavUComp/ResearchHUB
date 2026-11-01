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
  editor: document.querySelector("#announcement-editor"),
  message: document.querySelector("#announcement-form-message"),
  hint: document.querySelector("#announcement-form-hint"),
  close: document.querySelector("#close-announcement-form"),
  cancel: document.querySelector("#cancel-announcement-form"),
  dirty: document.querySelector("#announcement-dirty"),
  tabEdit: document.querySelector("#studio-tab-edit"),
  tabPreview: document.querySelector("#studio-tab-preview"),
  editPanel: document.querySelector("#studio-edit-panel"),
  previewPanel: document.querySelector("#studio-preview-panel"),
  preview: document.querySelector("#announcement-preview"),
  coverPreview: document.querySelector("#announcement-cover-preview"),
  coverUpload: document.querySelector("#announcement-cover-upload"),
  coverRemove: document.querySelector("#announcement-cover-remove"),
  coverStatus: document.querySelector("#announcement-cover-status"),
};

let managedAnnouncements = [];
let announcementIsDirty = false;

const announcementEditor = new AnnouncementEditor(announcementAdminElements.editor, {
  onChange: () => setAnnouncementDirty(true),
});

function setAnnouncementDirty(isDirty) {
  announcementIsDirty = isDirty;
  announcementAdminElements.dirty.textContent = isDirty ? "Cambios sin guardar" : "";
}

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
      message = payload.error?.message || describeValidationError(payload.detail?.[0]) || message;
    } catch (error) {
      message = "El servidor devolvió una respuesta no válida.";
    }
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

// Traduce un error de validacion del servidor y senala el bloque afectado.
function describeValidationError(detail) {
  if (!detail) return "";
  const message = String(detail.msg || "").replace(/^Value error, /, "");
  const location = detail.loc || [];
  const blockIndex = location[0] === "body" && location[1] === "content" ? location[2] : null;
  if (Number.isInteger(blockIndex)) {
    announcementEditor.flagIndex(blockIndex, message);
    return `Bloque ${blockIndex + 1}: ${message}`;
  }
  return message;
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

function paintAnnouncementCover() {
  const form = announcementAdminElements;
  const src = form.imageUrl.value.trim();
  form.coverPreview.replaceChildren();
  form.coverPreview.classList.toggle("is-empty", !src);
  if (src) {
    const image = document.createElement("img");
    image.src = src;
    image.alt = "";
    form.coverPreview.append(image);
  } else {
    form.coverPreview.append(announcementAdminNode("span", "", "Sin imagen: se muestra el tipo de comunicado."));
  }
  form.coverRemove.disabled = !src;
}

function updateAnnouncementCounters() {
  document.querySelectorAll("[data-counter-for]").forEach((counter) => {
    const field = document.getElementById(counter.dataset.counterFor);
    counter.textContent = `${field.value.length}/${field.maxLength}`;
    counter.classList.toggle("is-near", field.value.length > field.maxLength * 0.9);
  });
}

function showAnnouncementTab(tab) {
  const form = announcementAdminElements;
  const preview = tab === "preview";
  if (preview && !renderAnnouncementPreview()) return;
  form.tabEdit.setAttribute("aria-selected", String(!preview));
  form.tabPreview.setAttribute("aria-selected", String(preview));
  form.tabEdit.tabIndex = preview ? -1 : 0;
  form.tabPreview.tabIndex = preview ? 0 : -1;
  form.editPanel.classList.toggle("is-hidden", preview);
  form.previewPanel.classList.toggle("is-hidden", !preview);
}

// La vista previa usa el mismo renderizador que la portada.
function renderAnnouncementPreview() {
  const form = announcementAdminElements;
  let content;
  try {
    content = announcementEditor.read();
    form.message.textContent = "";
  } catch (error) {
    form.message.textContent = error.message;
    return false;
  }
  const item = {
    category: form.category.value,
    title: form.title.value.trim() || "Título del comunicado",
    summary: form.summary.value.trim(),
    image_url: form.imageUrl.value.trim(),
    image_alt: form.imageAlt.value.trim(),
    link_url: form.link.value.trim(),
  };
  const media = announcementAdminNode("div", "news-article-media");
  if (item.image_url) {
    const image = document.createElement("img");
    image.src = item.image_url;
    image.alt = item.image_alt;
    media.append(image);
  } else {
    media.classList.add("is-fallback");
    media.append(announcementAdminNode("span", "", announcementAdminCategoryCopy[item.category]));
  }
  const body = announcementAdminNode("div", "news-article-body rich-content");
  body.append(renderAnnouncementBlocks(content));
  item.body = body.textContent;
  const meta = `${announcementAdminCategoryCopy[item.category]} · Vista previa · ${announcementReadingMinutes(item)} min de lectura`;
  form.preview.replaceChildren(
    media,
    announcementAdminNode("span", "news-article-meta", meta),
    announcementAdminNode("h3", "", item.title),
    announcementAdminNode("p", "news-article-summary", item.summary),
    body,
  );
  if (item.link_url) {
    const link = announcementAdminNode("a", "button primary news-article-link", "Conocer más");
    link.href = item.link_url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    form.preview.append(link);
  }
  return true;
}

function openAnnouncementDialog(item = null) {
  const form = announcementAdminElements;
  form.form.reset();
  form.message.textContent = "";
  form.coverStatus.textContent = "";
  form.id.value = item?.id || "";
  form.version.value = item?.version || "";
  form.category.value = item?.category || "NOTICIA";
  form.link.value = item?.link_url || "";
  form.imageUrl.value = item?.image_url || "";
  form.imageAlt.value = item?.image_alt || "";
  form.title.value = item?.title || "";
  form.summary.value = item?.summary || "";
  announcementEditor.load(item?.content?.length ? item.content : announcementBlocksFromText(item?.body));
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
  paintAnnouncementCover();
  updateAnnouncementCounters();
  showAnnouncementTab("edit");
  setAnnouncementDirty(false);
  form.dialog.showModal();
  form.title.focus();
}

function closeAnnouncementDialog() {
  if (announcementIsDirty && !window.confirm("Hay cambios sin guardar. ¿Cerrar de todas formas?")) return;
  setAnnouncementDirty(false);
  announcementAdminElements.dialog.close();
}

async function saveAnnouncement(event) {
  event?.preventDefault();
  const form = announcementAdminElements;
  if (form.title.value.trim().length < 5 || form.summary.value.trim().length < 10) {
    form.message.textContent = "Escribe un título (5+ caracteres) y un resumen (10+ caracteres).";
    showAnnouncementTab("edit");
    (form.title.value.trim().length < 5 ? form.title : form.summary).focus();
    return;
  }
  let content;
  try {
    content = announcementEditor.read();
  } catch (error) {
    form.message.textContent = error.message;
    showAnnouncementTab("edit");
    return;
  }
  const id = form.id.value;
  const payload = {
    category: form.category.value,
    title: form.title.value.trim(),
    summary: form.summary.value.trim(),
    content,
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
    setAnnouncementDirty(false);
    form.dialog.close();
    await loadAnnouncementSettings();
  } catch (error) {
    form.message.textContent = error.message;
  }
}

async function uploadAnnouncementCover() {
  const form = announcementAdminElements;
  const [file] = await pickEditorFiles({ accept: editorImageTypes.join(",") });
  if (!file) return;
  form.coverStatus.textContent = `Subiendo ${file.name}…`;
  try {
    const asset = await uploadAnnouncementFile(file);
    if (asset.kind !== "image") throw new Error("La portada debe ser una imagen.");
    form.imageUrl.value = asset.url;
    if (!form.imageAlt.value.trim()) form.imageAlt.value = file.name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " ");
    form.coverStatus.textContent = "Imagen subida. Revisa su descripción.";
    paintAnnouncementCover();
    setAnnouncementDirty(true);
    form.imageAlt.focus();
    form.imageAlt.select();
  } catch (error) {
    form.coverStatus.textContent = error.message;
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
announcementAdminElements.form.addEventListener("input", (event) => {
  if (!announcementAdminElements.editor.contains(event.target)) setAnnouncementDirty(true);
  updateAnnouncementCounters();
});
announcementAdminElements.imageUrl.addEventListener("change", paintAnnouncementCover);
announcementAdminElements.coverUpload.addEventListener("click", uploadAnnouncementCover);
announcementAdminElements.coverRemove.addEventListener("click", () => {
  announcementAdminElements.imageUrl.value = "";
  announcementAdminElements.imageAlt.value = "";
  paintAnnouncementCover();
  setAnnouncementDirty(true);
});
announcementAdminElements.tabEdit.addEventListener("click", () => showAnnouncementTab("edit"));
announcementAdminElements.tabPreview.addEventListener("click", () => showAnnouncementTab("preview"));
[announcementAdminElements.tabEdit, announcementAdminElements.tabPreview].forEach((tab) => {
  tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
    const next = tab === announcementAdminElements.tabEdit ? "preview" : "edit";
    showAnnouncementTab(next);
    (next === "preview" ? announcementAdminElements.tabPreview : announcementAdminElements.tabEdit).focus();
  });
});
[announcementAdminElements.close, announcementAdminElements.cancel].forEach((button) => {
  button.addEventListener("click", closeAnnouncementDialog);
});
announcementAdminElements.dialog.addEventListener("cancel", (event) => {
  event.preventDefault();
  closeAnnouncementDialog();
});
announcementAdminElements.dialog.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
    event.preventDefault();
    saveAnnouncement();
  }
});
window.addEventListener("beforeunload", (event) => {
  if (announcementIsDirty && announcementAdminElements.dialog.open) event.preventDefault();
});

// Editor visual por bloques de los comunicados (consola de configuracion general).
// El texto se edita en linea; al guardar, cada bloque se lee como datos tipados que
// el servidor valida. Nunca se envia HTML: lo pegado entra como texto plano.

const editorBlockCatalog = [
  { type: "paragraph", label: "Párrafo", hint: "Texto normal", icon: "¶" },
  { type: "heading2", label: "Título", hint: "Sección principal", icon: "H2" },
  { type: "heading3", label: "Subtítulo", hint: "Sección secundaria", icon: "H3" },
  { type: "bullet", label: "Lista", hint: "Con viñetas", icon: "•" },
  { type: "ordered", label: "Lista numerada", hint: "Pasos en orden", icon: "1." },
  { type: "quote", label: "Cita", hint: "Testimonio o frase", icon: "“" },
  { type: "callout", label: "Destacado", hint: "Aviso en recuadro", icon: "!" },
  { type: "image", label: "Imagen", hint: "Con pie de foto", icon: "▣" },
  { type: "gallery", label: "Galería", hint: "De 2 a 12 imágenes", icon: "▦" },
  { type: "video", label: "Video", hint: "YouTube o Vimeo", icon: "▶" },
  { type: "button", label: "Botón", hint: "Llamado a la acción", icon: "➜" },
  { type: "file", label: "Documento", hint: "PDF descargable", icon: "⇩" },
  { type: "table", label: "Tabla", hint: "Fechas, cifras, cupos", icon: "▤" },
  { type: "event", label: "Evento", hint: "Fecha, lugar e inscripción", icon: "◷" },
  { type: "divider", label: "Separador", hint: "Línea divisoria", icon: "—" },
];

const editorBlockNames = {
  paragraph: "Párrafo",
  heading: "Título",
  list: "Lista",
  quote: "Cita",
  callout: "Destacado",
  image: "Imagen",
  gallery: "Galería",
  video: "Video",
  button: "Botón",
  file: "Documento",
  table: "Tabla",
  event: "Evento",
  divider: "Separador",
};

const editorImageTypes = ["image/jpeg", "image/png", "image/webp", "image/gif"];
const editorMaxImageBytes = 2 * 1024 * 1024;
const editorMaxDocumentBytes = 5 * 1024 * 1024;

class BlockValidationError extends Error {}

function editorNode(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
}

function editorButton(label, className, onClick, ariaLabel) {
  const button = editorNode("button", className, label);
  button.type = "button";
  if (ariaLabel) button.setAttribute("aria-label", ariaLabel);
  button.addEventListener("click", onClick);
  return button;
}

function editorField(labelText, input, className = "") {
  const label = editorNode("label", `rich-field ${className}`.trim());
  label.append(editorNode("span", "", labelText), input);
  return label;
}

function editorInput(value = "", { type = "text", maxLength, placeholder, required } = {}) {
  const input = document.createElement("input");
  input.type = type;
  input.value = value || "";
  if (maxLength) input.maxLength = maxLength;
  if (placeholder) input.placeholder = placeholder;
  if (required) input.required = true;
  return input;
}

function editorSelect(options, value) {
  const select = document.createElement("select");
  options.forEach(([optionValue, label]) => {
    const option = editorNode("option", "", label);
    option.value = optionValue;
    select.append(option);
  });
  if (value) select.value = value;
  return select;
}

function formatEditorBytes(bytes) {
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.ceil(bytes / 1024)} KB`;
}

// Reconoce enlaces de YouTube o Vimeo pegados por la persona editora.
function parseEditorVideoUrl(value) {
  const text = String(value || "").trim();
  const youtube = text.match(
    /^https?:\/\/(?:www\.|m\.)?(?:youtube\.com\/(?:watch\?(?:.*&)?v=|embed\/|shorts\/|live\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/,
  );
  if (youtube) return { provider: "youtube", video_id: youtube[1] };
  const vimeo = text.match(/^https?:\/\/(?:www\.|player\.)?vimeo\.com\/(?:video\/)?(\d{6,12})/);
  if (vimeo) return { provider: "vimeo", video_id: vimeo[1] };
  return null;
}

function normalizeEditorUrl(value) {
  const text = String(value || "").trim();
  if (!text) return "";
  if (/^(https:\/\/|mailto:|\/media\/announcements\/|\/static\/)/.test(text)) return text;
  if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(text)) return `mailto:${text}`;
  if (/^www\./.test(text)) return `https://${text}`;
  return text;
}

async function uploadAnnouncementFile(file) {
  const isImage = editorImageTypes.includes(file.type);
  const isPdf = file.type === "application/pdf";
  if (!isImage && !isPdf) {
    throw new Error("Sube una imagen JPG, PNG, WebP o GIF, o un documento PDF.");
  }
  const limit = isImage ? editorMaxImageBytes : editorMaxDocumentBytes;
  if (file.size > limit) {
    throw new Error(`«${file.name}» pesa ${formatEditorBytes(file.size)}; el límite es ${formatEditorBytes(limit)}.`);
  }
  const response = await apiFetch(
    `/api/v1/admin/announcement-assets?filename=${encodeURIComponent(file.name.slice(0, 200))}`,
    { method: "POST", headers: { "Content-Type": file.type }, body: file },
  );
  if (!response.ok) {
    let message = "No fue posible subir el archivo.";
    try {
      message = (await response.json()).error?.message || message;
    } catch (error) {
      // Respuesta sin JSON: se conserva el mensaje general.
    }
    throw new Error(message);
  }
  return response.json();
}

function pickEditorFiles({ accept, multiple = false }) {
  return new Promise((resolve) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = accept;
    input.multiple = multiple;
    input.addEventListener("change", () => resolve([...input.files]));
    input.click();
  });
}

// ---------------------------------------------------------------- texto con formato

const editorMarkByTag = {
  B: "bold",
  STRONG: "bold",
  I: "italic",
  EM: "italic",
  U: "underline",
  S: "strike",
  STRIKE: "strike",
  DEL: "strike",
  CODE: "code",
};

// Lee el contenido editable como fragmentos {text, marks, link}.
function readEditableRuns(root) {
  const runs = [];
  const push = (text, marks, link) => {
    if (!text) return;
    const last = runs[runs.length - 1];
    const key = `${[...marks].sort().join(",")}|${link || ""}`;
    if (last && last.key === key) {
      last.text += text;
    } else {
      runs.push({ text, marks: [...new Set(marks)], link, key });
    }
  };
  const walk = (node, marks, link) => {
    node.childNodes.forEach((child, index) => {
      if (child.nodeType === Node.TEXT_NODE) {
        push(child.textContent.replace(/ /g, " "), marks, link);
        return;
      }
      if (child.nodeType !== Node.ELEMENT_NODE) return;
      if (child.tagName === "BR") {
        push("\n", marks, link);
        return;
      }
      // Algunos navegadores envuelven lineas nuevas en DIV o P.
      if ((child.tagName === "DIV" || child.tagName === "P") && index > 0) push("\n", marks, link);
      const mark = editorMarkByTag[child.tagName];
      const weight = child.style?.fontWeight;
      const childMarks = [...marks];
      if (mark) childMarks.push(mark);
      if (weight === "bold" || Number(weight) >= 600) childMarks.push("bold");
      if (child.style?.fontStyle === "italic") childMarks.push("italic");
      const href = child.tagName === "A" ? child.getAttribute("href") : null;
      walk(child, childMarks, href ? normalizeEditorUrl(href) : link);
    });
  };
  walk(root, [], null);
  // Recorta espacios y saltos al inicio y al final del bloque.
  if (runs.length) runs[0].text = runs[0].text.replace(/^\s+/, "");
  if (runs.length) runs[runs.length - 1].text = runs[runs.length - 1].text.replace(/\s+$/, "");
  return runs
    .filter((run) => run.text)
    .map(({ text, marks, link }) => {
      const run = { text };
      if (marks.length) run.marks = marks;
      if (link) run.link = link;
      return run;
    });
}

function createEditable(runs, { label, placeholder, multiline = true }) {
  const editable = editorNode("div", "rich-editable");
  editable.contentEditable = "true";
  editable.setAttribute("role", "textbox");
  editable.setAttribute("aria-label", label);
  if (multiline) editable.setAttribute("aria-multiline", "true");
  editable.dataset.placeholder = placeholder || "";
  editable.spellcheck = true;
  if (runs?.length) renderAnnouncementRuns(runs, editable);
  return editable;
}

function requireText(runs, message) {
  if (!runs.length) throw new BlockValidationError(message);
  return runs;
}

// ---------------------------------------------------------------- bloques

function textBlock(editor, data, kind) {
  const config = {
    paragraph: { label: "Párrafo", placeholder: "Escribe aquí. Pega un enlace de YouTube para insertar un video." },
    heading2: { label: "Título de sección", placeholder: "Título de la sección" },
    heading3: { label: "Subtítulo", placeholder: "Subtítulo" },
    quote: { label: "Cita", placeholder: "Texto de la cita" },
  }[kind];
  const body = editorNode("div", `rich-text-block is-${kind}`);
  const editable = createEditable(data.runs, config);
  body.append(editable);
  let cite;
  if (kind === "quote") {
    cite = editorInput(data.cite, { maxLength: 160, placeholder: "Quién lo dice (opcional)" });
    body.append(editorField("Autor de la cita", cite, "is-inline"));
  }
  return {
    body,
    editable,
    focus: () => editable.focus(),
    isEmpty: () => !editable.textContent.trim(),
    read() {
      const runs = readEditableRuns(editable);
      if (kind === "paragraph") return runs.length ? { type: "paragraph", runs } : null;
      if (kind === "quote") {
        return { type: "quote", runs: requireText(runs, "La cita está vacía."), cite: cite.value.trim() };
      }
      return {
        type: "heading",
        level: kind === "heading3" ? 3 : 2,
        runs: requireText(runs, "El título está vacío."),
      };
    },
  };
}

function listBlock(editor, data, kind) {
  const body = editorNode("div", "rich-list-block");
  const list = editorNode(kind === "ordered" ? "ol" : "ul", "rich-editable rich-list");
  list.contentEditable = "true";
  list.setAttribute("role", "textbox");
  list.setAttribute("aria-multiline", "true");
  list.setAttribute("aria-label", kind === "ordered" ? "Lista numerada" : "Lista con viñetas");
  const items = data.items?.length ? data.items : [[]];
  items.forEach((runs) => list.append(renderAnnouncementRuns(runs, document.createElement("li"))));
  body.append(list);
  return {
    body,
    editable: list,
    focus: () => list.focus(),
    isEmpty: () => !list.textContent.trim(),
    read() {
      const values = [...list.querySelectorAll(":scope > li")]
        .map((item) => readEditableRuns(item))
        .filter((runs) => runs.length);
      if (!values.length) throw new BlockValidationError("La lista está vacía.");
      return { type: "list", style: kind, items: values };
    },
  };
}

function calloutBlock(editor, data) {
  const body = editorNode("div", "rich-callout-block");
  const tone = editorSelect(
    [
      ["info", "Información"],
      ["success", "Logro o buena noticia"],
      ["warning", "Importante o fecha límite"],
    ],
    data.tone || "info",
  );
  const title = editorInput(data.title, { maxLength: 120, placeholder: "Ej.: Cierre de inscripciones" });
  const editable = createEditable(data.runs, { label: "Texto del destacado", placeholder: "Texto del destacado" });
  const syncTone = () => {
    body.dataset.tone = tone.value;
  };
  tone.addEventListener("change", syncTone);
  syncTone();
  const fields = editorNode("div", "rich-field-row");
  fields.append(editorField("Tipo", tone), editorField("Título", title, "is-wide"));
  body.append(fields, editable);
  return {
    body,
    editable,
    focus: () => title.focus(),
    read() {
      const runs = readEditableRuns(editable);
      if (!title.value.trim() && !runs.length) throw new BlockValidationError("El destacado está vacío.");
      return { type: "callout", tone: tone.value, title: title.value.trim(), runs };
    },
  };
}

function dividerBlock() {
  const body = editorNode("div", "rich-divider-block");
  body.append(editorNode("hr", "rich-divider"));
  return { body, focus: () => body.closest(".rich-block")?.focus(), read: () => ({ type: "divider" }) };
}

// Una imagen editable: archivo subido o direccion, texto alternativo y pie de foto.
function pictureEditor(editor, data, { onRemove } = {}) {
  const wrap = editorNode("div", "rich-picture");
  const state = { src: data.src || "" };
  const preview = editorNode("div", "rich-picture-preview");
  const alt = editorInput(data.alt, { maxLength: 200, placeholder: "Qué muestra la imagen", required: true });
  const caption = editorInput(data.caption, { maxLength: 300, placeholder: "Pie de foto (opcional)" });
  const status = editorNode("p", "rich-upload-status");
  status.setAttribute("role", "status");

  const paint = () => {
    preview.replaceChildren();
    if (state.src) {
      const image = document.createElement("img");
      image.src = state.src;
      image.alt = "";
      preview.append(image);
      preview.classList.remove("is-empty");
    } else {
      preview.classList.add("is-empty");
      preview.append(editorNode("span", "", "Arrastra una imagen aquí o súbela"));
    }
  };
  const upload = async (file) => {
    status.textContent = `Subiendo ${file.name}…`;
    try {
      const asset = await uploadAnnouncementFile(file);
      if (asset.kind !== "image") throw new Error("Ese archivo no es una imagen.");
      state.src = asset.url;
      if (!alt.value.trim()) alt.value = file.name.replace(/\.[^.]+$/, "").replace(/[-_]+/g, " ");
      status.textContent = `Imagen subida (${formatEditorBytes(asset.size_bytes)}). Revisa la descripción.`;
      paint();
      editor.markDirty();
      alt.focus();
      alt.select();
    } catch (error) {
      status.textContent = error.message;
    }
  };
  const actions = editorNode("div", "rich-inline-actions");
  actions.append(
    editorButton("Subir imagen", "button secondary", async () => {
      const [file] = await pickEditorFiles({ accept: editorImageTypes.join(",") });
      if (file) upload(file);
    }),
    editorButton("Usar una dirección", "button secondary", () => {
      const value = window.prompt("Dirección de la imagen (/static/… o un dominio autorizado con HTTPS):", state.src);
      if (value === null) return;
      state.src = value.trim();
      paint();
      editor.markDirty();
    }),
  );
  if (onRemove) actions.append(editorButton("Quitar", "button secondary danger", onRemove));
  preview.addEventListener("dragover", (event) => {
    event.preventDefault();
    preview.classList.add("is-dragging");
  });
  preview.addEventListener("dragleave", () => preview.classList.remove("is-dragging"));
  preview.addEventListener("drop", (event) => {
    event.preventDefault();
    event.stopPropagation();
    preview.classList.remove("is-dragging");
    const [file] = event.dataTransfer.files;
    if (file) upload(file);
  });
  paint();
  const fields = editorNode("div", "rich-picture-fields");
  fields.append(
    editorField("Descripción para lectores de pantalla", alt),
    editorField("Pie de foto", caption),
    actions,
    status,
  );
  wrap.append(preview, fields);
  return {
    element: wrap,
    upload,
    focus: () => (state.src ? alt.focus() : actions.querySelector("button").focus()),
    read() {
      if (!state.src) throw new BlockValidationError("Falta subir la imagen.");
      if (!alt.value.trim()) {
        alt.focus();
        throw new BlockValidationError("Describe la imagen para quienes usan lector de pantalla.");
      }
      return { src: state.src, alt: alt.value.trim(), caption: caption.value.trim() };
    },
  };
}

function imageBlock(editor, data) {
  const body = editorNode("div", "rich-image-block");
  const picture = pictureEditor(editor, data);
  const size = editorSelect(
    [
      ["normal", "Ancho del texto"],
      ["wide", "Ancho completo"],
    ],
    data.size || "normal",
  );
  body.append(picture.element, editorField("Tamaño", size, "is-inline"));
  return {
    body,
    upload: picture.upload,
    focus: picture.focus,
    read: () => ({ type: "image", ...picture.read(), size: size.value }),
  };
}

function galleryBlock(editor, data) {
  const body = editorNode("div", "rich-gallery-block");
  const grid = editorNode("div", "rich-gallery-editor");
  const pictures = [];
  const status = editorNode("p", "rich-upload-status");
  status.setAttribute("role", "status");
  const addPicture = (pictureData) => {
    let entry;
    const picture = pictureEditor(editor, pictureData, {
      onRemove: () => {
        pictures.splice(pictures.indexOf(entry), 1);
        picture.element.remove();
        editor.markDirty();
      },
    });
    entry = picture;
    pictures.push(entry);
    grid.append(picture.element);
    return picture;
  };
  const addFiles = async (files) => {
    for (const file of files.slice(0, 12 - pictures.length)) {
      await addPicture({}).upload(file);
    }
  };
  (data.images || []).forEach(addPicture);
  body.append(
    grid,
    editorButton("Agregar imágenes", "button secondary", async () => {
      const files = await pickEditorFiles({ accept: editorImageTypes.join(","), multiple: true });
      if (files.length) addFiles(files);
    }),
    status,
  );
  return {
    body,
    addFiles,
    focus: () => body.querySelector("button")?.focus(),
    read() {
      const images = pictures.map((picture) => picture.read());
      if (images.length < 2) throw new BlockValidationError("Una galería necesita al menos 2 imágenes.");
      return { type: "gallery", images };
    },
  };
}

function videoBlock(editor, data) {
  const body = editorNode("div", "rich-video-block");
  const initialUrl = data.video_id
    ? data.provider === "vimeo"
      ? `https://vimeo.com/${data.video_id}`
      : `https://www.youtube.com/watch?v=${data.video_id}`
    : "";
  const url = editorInput(initialUrl, { type: "url", placeholder: "https://www.youtube.com/watch?v=…" });
  const title = editorInput(data.title || "", { maxLength: 160, placeholder: "De qué trata el video", required: true });
  const caption = editorInput(data.caption, { maxLength: 300, placeholder: "Pie del video (opcional)" });
  const preview = editorNode("div", "rich-video-preview");
  const paint = () => {
    const parsed = parseEditorVideoUrl(url.value);
    preview.replaceChildren();
    if (parsed) {
      preview.append(announcementBlockRenderers.video({ ...parsed, title: title.value || "Video" }));
    } else {
      preview.append(
        editorNode(
          "p",
          "rich-hint",
          url.value.trim() ? "Ese enlace no es de YouTube ni de Vimeo." : "Pega el enlace del video para verlo aquí.",
        ),
      );
    }
  };
  url.addEventListener("change", paint);
  url.addEventListener("paste", () => setTimeout(paint));
  paint();
  body.append(
    editorField("Enlace de YouTube o Vimeo", url),
    editorField("Título del video (accesibilidad)", title),
    editorField("Pie del video", caption),
    preview,
  );
  return {
    body,
    focus: () => url.focus(),
    read() {
      const parsed = parseEditorVideoUrl(url.value);
      if (!parsed) throw new BlockValidationError("Pega un enlace válido de YouTube o Vimeo.");
      if (title.value.trim().length < 3) {
        title.focus();
        throw new BlockValidationError("Escribe un título para el video.");
      }
      return { type: "video", ...parsed, title: title.value.trim(), caption: caption.value.trim() };
    },
  };
}

// Campo de destino: una direccion o un PDF subido al comunicado.
function targetField(editor, value, labelText) {
  const input = editorInput(value, { placeholder: "https://… o correo@ucompensar.edu.co" });
  const status = editorNode("p", "rich-upload-status");
  status.setAttribute("role", "status");
  const wrap = editorNode("div", "rich-target");
  wrap.append(
    editorField(labelText, input),
    editorButton("Subir PDF", "button secondary", async () => {
      const [file] = await pickEditorFiles({ accept: "application/pdf" });
      if (!file) return;
      status.textContent = `Subiendo ${file.name}…`;
      try {
        const asset = await uploadAnnouncementFile(file);
        input.value = asset.url;
        status.textContent = `PDF subido: ${asset.filename} (${formatEditorBytes(asset.size_bytes)}).`;
        input.dispatchEvent(new CustomEvent("asset", { detail: asset }));
        editor.markDirty();
      } catch (error) {
        status.textContent = error.message;
      }
    }),
    status,
  );
  return { element: wrap, input };
}

function buttonBlock(editor, data) {
  const body = editorNode("div", "rich-button-block");
  const label = editorInput(data.label, { maxLength: 60, placeholder: "Ej.: Inscríbete aquí", required: true });
  const target = targetField(editor, data.url, "Destino del botón");
  const variant = editorSelect(
    [
      ["primary", "Principal (naranja)"],
      ["secondary", "Secundario (contorno)"],
    ],
    data.variant || "primary",
  );
  const row = editorNode("div", "rich-field-row");
  row.append(editorField("Texto del botón", label, "is-wide"), editorField("Estilo", variant));
  body.append(row, target.element);
  return {
    body,
    focus: () => label.focus(),
    read() {
      if (label.value.trim().length < 2) throw new BlockValidationError("Escribe el texto del botón.");
      const url = normalizeEditorUrl(target.input.value);
      if (!url) throw new BlockValidationError("Indica a dónde lleva el botón.");
      return { type: "button", label: label.value.trim(), url, variant: variant.value };
    },
  };
}

function fileBlock(editor, data) {
  const body = editorNode("div", "rich-file-block");
  const label = editorInput(data.label, { maxLength: 160, placeholder: "Ej.: Términos de referencia", required: true });
  const description = editorInput(data.description, { maxLength: 200, placeholder: "PDF · 1,2 MB (opcional)" });
  const target = targetField(editor, data.url, "Documento");
  target.input.addEventListener("asset", (event) => {
    const asset = event.detail;
    if (!label.value.trim()) label.value = asset.filename.replace(/\.pdf$/i, "");
    description.value = `PDF · ${formatEditorBytes(asset.size_bytes)}`;
  });
  body.append(target.element, editorField("Nombre visible", label), editorField("Descripción", description));
  return {
    body,
    focus: () => target.element.querySelector("button").focus(),
    read() {
      const url = normalizeEditorUrl(target.input.value);
      if (!url) throw new BlockValidationError("Sube el PDF o indica su dirección.");
      if (label.value.trim().length < 2) throw new BlockValidationError("Escribe el nombre del documento.");
      return { type: "file", url, label: label.value.trim(), description: description.value.trim() };
    },
  };
}

function tableBlock(editor, data) {
  const body = editorNode("div", "rich-table-block");
  let rows = data.rows?.length
    ? data.rows.map((row) => [...row])
    : [
        ["Actividad", "Fecha"],
        ["", ""],
      ];
  const header = document.createElement("input");
  header.type = "checkbox";
  header.checked = data.header ?? true;
  const caption = editorInput(data.caption, { maxLength: 200, placeholder: "Título de la tabla (opcional)" });
  const grid = editorNode("div", "rich-table-wrap");
  const sync = () => {
    rows = [...grid.querySelectorAll("tr")].map((row) => [...row.querySelectorAll("input")].map((input) => input.value));
  };
  const paint = () => {
    const table = editorNode("table", "rich-table is-editing");
    rows.forEach((cells, rowIndex) => {
      const row = document.createElement("tr");
      cells.forEach((cell, columnIndex) => {
        const td = document.createElement(rowIndex === 0 && header.checked ? "th" : "td");
        const input = editorInput(cell, { maxLength: 300 });
        input.setAttribute("aria-label", `Fila ${rowIndex + 1}, columna ${columnIndex + 1}`);
        td.append(input);
        row.append(td);
      });
      table.append(row);
    });
    grid.replaceChildren(table);
  };
  const change = (mutate) => () => {
    sync();
    mutate();
    paint();
    editor.markDirty();
  };
  header.addEventListener("change", change(() => {}));
  const tools = editorNode("div", "rich-inline-actions");
  tools.append(
    editorButton("+ Fila", "button secondary", change(() => rows.length < 30 && rows.push(rows[0].map(() => "")))),
    editorButton("− Fila", "button secondary", change(() => rows.length > 1 && rows.pop())),
    editorButton("+ Columna", "button secondary", change(() => rows[0].length < 8 && rows.forEach((row) => row.push("")))),
    editorButton("− Columna", "button secondary", change(() => rows[0].length > 1 && rows.forEach((row) => row.pop()))),
  );
  const headerLabel = editorNode("label", "rich-check");
  headerLabel.append(header, document.createTextNode(" La primera fila es encabezado"));
  paint();
  body.append(editorField("Título", caption), grid, tools, headerLabel);
  return {
    body,
    focus: () => grid.querySelector("input")?.focus(),
    read() {
      sync();
      const values = rows.map((row) => row.map((cell) => cell.trim()));
      if (!values.some((row) => row.some(Boolean))) throw new BlockValidationError("La tabla está vacía.");
      return { type: "table", header: header.checked, caption: caption.value.trim(), rows: values };
    },
  };
}

function eventBlock(editor, data) {
  const body = editorNode("div", "rich-event-block");
  const startDate = editorInput(data.start_date, { type: "date", required: true });
  const startTime = editorInput(data.start_time?.slice(0, 5), { type: "time" });
  const endDate = editorInput(data.end_date, { type: "date" });
  const endTime = editorInput(data.end_time?.slice(0, 5), { type: "time" });
  const mode = editorSelect(
    [
      ["presencial", "Presencial"],
      ["virtual", "Virtual"],
      ["hibrido", "Híbrido"],
    ],
    data.mode || "presencial",
  );
  const location = editorInput(data.location, { maxLength: 200, placeholder: "Sede, salón o enlace de la reunión" });
  const registration = editorInput(data.registration_url, { type: "url", placeholder: "https://… (opcional)" });
  const dates = editorNode("div", "rich-field-row");
  dates.append(
    editorField("Fecha de inicio", startDate),
    editorField("Hora", startTime),
    editorField("Fecha de cierre", endDate),
    editorField("Hora de cierre", endTime),
  );
  const place = editorNode("div", "rich-field-row");
  place.append(editorField("Modalidad", mode), editorField("Lugar", location, "is-wide"));
  body.append(dates, place, editorField("Enlace de inscripción", registration));
  return {
    body,
    focus: () => startDate.focus(),
    read() {
      if (!startDate.value) throw new BlockValidationError("Indica la fecha del evento.");
      if (endDate.value && endDate.value < startDate.value) {
        throw new BlockValidationError("El evento no puede terminar antes de empezar.");
      }
      return {
        type: "event",
        start_date: startDate.value,
        start_time: startTime.value || null,
        end_date: endDate.value || null,
        end_time: endTime.value || null,
        mode: mode.value,
        location: location.value.trim(),
        registration_url: normalizeEditorUrl(registration.value) || null,
      };
    },
  };
}

function editorKindFor(block) {
  if (block.type === "heading") return block.level === 3 ? "heading3" : "heading2";
  if (block.type === "list") return block.style === "ordered" ? "ordered" : "bullet";
  return block.type;
}

const editorBlockFactories = {
  paragraph: (editor, data) => textBlock(editor, data, "paragraph"),
  heading2: (editor, data) => textBlock(editor, data, "heading2"),
  heading3: (editor, data) => textBlock(editor, data, "heading3"),
  quote: (editor, data) => textBlock(editor, data, "quote"),
  bullet: (editor, data) => listBlock(editor, data, "bullet"),
  ordered: (editor, data) => listBlock(editor, data, "ordered"),
  callout: calloutBlock,
  divider: dividerBlock,
  image: imageBlock,
  gallery: galleryBlock,
  video: videoBlock,
  button: buttonBlock,
  file: fileBlock,
  table: tableBlock,
  event: eventBlock,
};

// ---------------------------------------------------------------- editor

class AnnouncementEditor {
  constructor(root, { onChange } = {}) {
    this.root = root;
    this.onChange = onChange;
    this.entries = [];
    this.activeEditable = null;
    this.toolbar = this.buildToolbar();
    this.list = editorNode("div", "rich-blocks");
    this.inserter = this.buildInserter();
    this.root.replaceChildren(this.toolbar, this.list, this.inserter.element);
    this.root.addEventListener("input", () => this.markDirty());
    this.root.addEventListener("change", () => this.markDirty());
    this.root.addEventListener("focusin", (event) => this.trackFocus(event));
    this.root.addEventListener("keydown", (event) => this.handleKeydown(event));
    this.root.addEventListener("paste", (event) => this.handlePaste(event));
    this.root.addEventListener("dragover", (event) => {
      if ([...event.dataTransfer.types].includes("Files")) event.preventDefault();
    });
    this.root.addEventListener("drop", (event) => this.handleDrop(event));
    document.execCommand("defaultParagraphSeparator", false, "p");
  }

  markDirty() {
    this.onChange?.();
  }

  load(blocks) {
    this.entries = [];
    this.list.replaceChildren();
    (blocks?.length ? blocks : [{ type: "paragraph", runs: [] }]).forEach((block) => {
      this.insert(editorKindFor(block), block, null, false);
    });
  }

  // Inserta un bloque despues de `after` (o al final) y devuelve su entrada.
  insert(kind, data = {}, after = null, focus = true) {
    const factory = editorBlockFactories[kind];
    if (!factory) return null;
    const entry = { kind, ...factory(this, data) };
    entry.element = this.wrapBlock(entry);
    const index = after ? this.entries.indexOf(after) + 1 : this.entries.length;
    this.entries.splice(index, 0, entry);
    const reference = this.entries[index + 1]?.element || null;
    this.list.insertBefore(entry.element, reference);
    if (focus) {
      entry.focus?.();
      this.markDirty();
    }
    return entry;
  }

  wrapBlock(entry) {
    const element = editorNode("section", `rich-block is-${entry.kind}`);
    element.tabIndex = -1;
    const catalog = editorBlockCatalog.find((item) => item.type === entry.kind);
    const name = catalog?.label || editorBlockNames[entry.kind] || "Bloque";
    element.setAttribute("aria-label", name);
    const bar = editorNode("div", "rich-block-bar");
    bar.append(editorNode("span", "rich-block-name", name));
    const actions = editorNode("div", "rich-block-actions");
    actions.append(
      editorButton("↑", "rich-icon-button", () => this.move(entry, -1), `Subir ${name}`),
      editorButton("↓", "rich-icon-button", () => this.move(entry, 1), `Bajar ${name}`),
      editorButton("+", "rich-icon-button", (event) => this.inserter.open(event.currentTarget, entry), `Agregar bloque después de ${name}`),
      editorButton("⧉", "rich-icon-button", () => this.duplicate(entry), `Duplicar ${name}`),
      editorButton("✕", "rich-icon-button danger", () => this.remove(entry), `Eliminar ${name}`),
    );
    bar.append(actions);
    element.append(bar, entry.body);
    return element;
  }

  move(entry, offset) {
    const index = this.entries.indexOf(entry);
    const target = index + offset;
    if (target < 0 || target >= this.entries.length) return;
    this.entries.splice(index, 1);
    this.entries.splice(target, 0, entry);
    const reference = offset < 0 ? this.entries[target + 1].element : this.entries[target - 1].element.nextSibling;
    this.list.insertBefore(entry.element, reference);
    entry.element.querySelector(`[aria-label^="${offset < 0 ? "Subir" : "Bajar"}"]`)?.focus();
    this.markDirty();
  }

  duplicate(entry) {
    try {
      const data = entry.read() || {};
      this.insert(entry.kind, data, entry);
    } catch (error) {
      this.flag(entry, error.message);
    }
  }

  remove(entry, { focusPrevious = true } = {}) {
    const index = this.entries.indexOf(entry);
    if (index < 0) return;
    const hasContent = entry.isEmpty ? !entry.isEmpty() : entry.kind !== "divider";
    if (hasContent && focusPrevious !== "silent" && !window.confirm("¿Eliminar este bloque?")) return;
    this.entries.splice(index, 1);
    entry.element.remove();
    if (!this.entries.length) this.insert("paragraph", {}, null, false);
    const neighbour = this.entries[Math.max(0, index - 1)];
    if (focusPrevious) this.focusEnd(neighbour);
    this.markDirty();
  }

  focusEnd(entry) {
    if (!entry) return;
    if (!entry.editable) {
      entry.focus?.();
      return;
    }
    entry.editable.focus();
    const selection = window.getSelection();
    selection.selectAllChildren(entry.editable);
    selection.collapseToEnd();
  }

  entryFor(node) {
    const element = node?.closest?.(".rich-block");
    return this.entries.find((entry) => entry.element === element) || null;
  }

  flag(entry, message) {
    entry.element.classList.add("has-error");
    entry.element.dataset.error = message;
    entry.element.scrollIntoView({ block: "center", behavior: "smooth" });
    entry.focus?.();
  }

  clearFlags() {
    this.entries.forEach((entry) => {
      entry.element.classList.remove("has-error");
      delete entry.element.dataset.error;
    });
  }

  flagIndex(blockIndex, message) {
    // El servidor numera solo los bloques enviados; los parrafos vacios no viajan.
    const sent = this.entries.filter((entry) => !(entry.kind === "paragraph" && entry.isEmpty()));
    if (sent[blockIndex]) this.flag(sent[blockIndex], message);
  }

  // Devuelve los bloques o lanza el primer error, marcando el bloque.
  read() {
    this.clearFlags();
    const blocks = [];
    for (const entry of this.entries) {
      try {
        const block = entry.read();
        if (block) blocks.push(block);
      } catch (error) {
        this.flag(entry, error.message);
        const name = editorBlockCatalog.find((item) => item.type === entry.kind)?.label || "Bloque";
        throw new Error(`${name}: ${error.message}`);
      }
    }
    return blocks;
  }

  // ------------------------------------------------------------ barra de formato

  buildToolbar() {
    const toolbar = editorNode("div", "rich-toolbar");
    toolbar.setAttribute("role", "toolbar");
    toolbar.setAttribute("aria-label", "Formato del texto");
    const command = (label, title, run, className = "") => {
      const button = editorButton(label, `rich-tool ${className}`.trim(), () => {
        if (!this.restoreSelection()) return;
        run();
        this.markDirty();
      }, title);
      button.title = title;
      // Conserva la seleccion del texto al hacer clic en la barra.
      button.addEventListener("mousedown", (event) => event.preventDefault());
      return button;
    };
    this.styleSelect = editorSelect(
      [
        ["", "Estilo…"],
        ["paragraph", "Párrafo"],
        ["heading2", "Título"],
        ["heading3", "Subtítulo"],
        ["quote", "Cita"],
      ],
      "",
    );
    this.styleSelect.setAttribute("aria-label", "Convertir el bloque actual en");
    this.styleSelect.addEventListener("change", () => {
      const kind = this.styleSelect.value;
      this.styleSelect.value = "";
      if (kind) this.convertActive(kind);
    });
    toolbar.append(
      this.styleSelect,
      command("B", "Negrita (Ctrl+B)", () => document.execCommand("bold"), "is-bold"),
      command("I", "Cursiva (Ctrl+I)", () => document.execCommand("italic"), "is-italic"),
      command("U", "Subrayado (Ctrl+U)", () => document.execCommand("underline"), "is-underline"),
      command("S", "Tachado", () => document.execCommand("strikeThrough"), "is-strike"),
      command("</>", "Código", () => this.toggleCode()),
      command("Enlace", "Insertar enlace (Ctrl+K)", () => this.createLink()),
      command("Quitar enlace", "Quitar enlace", () => document.execCommand("unlink")),
      command("Limpiar", "Quitar formato", () => {
        document.execCommand("removeFormat");
        document.execCommand("unlink");
      }),
    );
    return toolbar;
  }

  trackFocus(event) {
    const editable = event.target.closest?.(".rich-editable");
    this.activeEditable = editable || null;
    this.toolbar.classList.toggle("is-idle", !editable);
  }

  restoreSelection() {
    if (!this.activeEditable) {
      window.alert("Ubica el cursor en un texto para darle formato.");
      return false;
    }
    if (!this.activeEditable.contains(window.getSelection().anchorNode)) this.activeEditable.focus();
    document.execCommand("styleWithCSS", false, false);
    return true;
  }

  createLink() {
    const selection = window.getSelection();
    if (!selection.toString().trim()) {
      window.alert("Selecciona primero el texto que quieres convertir en enlace.");
      return;
    }
    const range = selection.getRangeAt(0).cloneRange();
    const value = window.prompt("Dirección del enlace (https://… o un correo):", "https://");
    if (!value) return;
    const url = normalizeEditorUrl(value);
    if (!/^(https:\/\/[^\s]+|mailto:[^\s]+@[^\s]+|\/media\/announcements\/)/.test(url)) {
      window.alert("Usa una dirección que empiece por https:// o un correo electrónico.");
      return;
    }
    selection.removeAllRanges();
    selection.addRange(range);
    document.execCommand("createLink", false, url);
  }

  toggleCode() {
    const selection = window.getSelection();
    const code = selection.anchorNode?.parentElement?.closest("code");
    if (code && this.activeEditable.contains(code)) {
      code.replaceWith(...code.childNodes);
      return;
    }
    if (!selection.rangeCount || selection.isCollapsed) return;
    const range = selection.getRangeAt(0);
    const wrapper = document.createElement("code");
    wrapper.append(range.extractContents());
    range.insertNode(wrapper);
  }

  convertActive(kind) {
    const entry = this.entryFor(this.activeEditable);
    if (!entry || !entry.editable || entry.kind === kind) return;
    const runs = entry.editable.matches("ul, ol")
      ? [...entry.editable.querySelectorAll("li")].flatMap((item, index) => [
          ...(index ? [{ text: "\n" }] : []),
          ...readEditableRuns(item),
        ])
      : readEditableRuns(entry.editable);
    const replacement = this.insert(kind, { runs }, entry, false);
    this.remove(entry, { focusPrevious: "silent" });
    this.focusEnd(replacement);
    this.markDirty();
  }

  // ------------------------------------------------------------ teclado y pegado

  handleKeydown(event) {
    const editable = event.target.closest?.(".rich-editable");
    if (!editable) return;
    const entry = this.entryFor(editable);
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      this.createLink();
      return;
    }
    if (!entry) return;
    if (event.key === "Enter" && !event.shiftKey && editable.matches("ul, ol")) {
      const item = window.getSelection().anchorNode?.parentElement?.closest("li") || window.getSelection().anchorNode;
      if (item?.tagName === "LI" && !item.textContent.trim() && item === editable.lastElementChild) {
        event.preventDefault();
        item.remove();
        this.insert("paragraph", {}, entry);
      }
      return;
    }
    const splittable = ["paragraph", "heading2", "heading3"].includes(entry.kind);
    if (event.key === "Enter" && !event.shiftKey && splittable) {
      event.preventDefault();
      const selection = window.getSelection();
      const range = selection.getRangeAt(0);
      range.deleteContents();
      const tail = document.createRange();
      tail.setStart(range.startContainer, range.startOffset);
      tail.setEnd(editable, editable.childNodes.length);
      const rest = tail.extractContents();
      const next = this.insert("paragraph", {}, entry);
      next.editable.append(rest);
      next.editable.focus();
      const caret = window.getSelection();
      caret.selectAllChildren(next.editable);
      caret.collapseToStart();
      return;
    }
    if (event.key === "Backspace" && entry.isEmpty?.() && this.entries.length > 1) {
      event.preventDefault();
      this.remove(entry);
    }
  }

  handlePaste(event) {
    const editable = event.target.closest?.(".rich-editable");
    const files = [...(event.clipboardData?.files || [])];
    if (files.length) {
      event.preventDefault();
      this.insertFiles(files, this.entryFor(event.target));
      return;
    }
    if (!editable) return;
    event.preventDefault();
    const text = event.clipboardData.getData("text/plain");
    const entry = this.entryFor(editable);
    const video = parseEditorVideoUrl(text);
    if (video && entry?.kind === "paragraph" && entry.isEmpty()) {
      const block = this.insert("video", { ...video, title: "" }, entry);
      this.remove(entry, { focusPrevious: false });
      block.element.querySelector('input[maxlength="160"]')?.focus();
      return;
    }
    document.execCommand("insertText", false, text);
  }

  handleDrop(event) {
    const files = [...(event.dataTransfer?.files || [])];
    if (!files.length || event.defaultPrevented) return;
    event.preventDefault();
    this.insertFiles(files, this.entryFor(event.target));
  }

  // Imagenes sueltas -> imagen; varias -> galeria; PDF -> documento.
  async insertFiles(files, after) {
    const images = files.filter((file) => editorImageTypes.includes(file.type));
    const documents = files.filter((file) => file.type === "application/pdf");
    if (!images.length && !documents.length) {
      window.alert("Solo se pueden insertar imágenes JPG, PNG, WebP o GIF, o documentos PDF.");
      return;
    }
    let anchor = after || this.entries[this.entries.length - 1];
    if (images.length === 1) {
      anchor = this.insert("image", {}, anchor);
      await anchor.upload(images[0]);
    } else if (images.length > 1) {
      anchor = this.insert("gallery", {}, anchor);
      await anchor.addFiles(images);
    }
    for (const file of documents) {
      anchor = this.insert("file", {}, anchor);
      const status = anchor.element.querySelector(".rich-upload-status");
      status.textContent = `Subiendo ${file.name}…`;
      try {
        const asset = await uploadAnnouncementFile(file);
        const input = anchor.element.querySelector(".rich-target input");
        input.value = asset.url;
        input.dispatchEvent(new CustomEvent("asset", { detail: asset }));
        status.textContent = `PDF subido: ${asset.filename}.`;
      } catch (error) {
        status.textContent = error.message;
      }
    }
  }

  // ------------------------------------------------------------ menu de bloques

  buildInserter() {
    const element = editorNode("div", "rich-inserter");
    const trigger = editorButton("+ Agregar bloque", "button secondary rich-add", () => menu.toggle(trigger, null));
    trigger.setAttribute("aria-haspopup", "true");
    const panel = editorNode("div", "rich-insert-menu is-hidden");
    panel.setAttribute("role", "menu");
    panel.setAttribute("aria-label", "Tipos de bloque");
    let anchorEntry = null;
    let opener = null;
    const close = () => {
      panel.classList.add("is-hidden");
      trigger.setAttribute("aria-expanded", "false");
      opener?.focus();
    };
    editorBlockCatalog.forEach((item) => {
      const option = editorButton("", "rich-insert-option", () => {
        panel.classList.add("is-hidden");
        trigger.setAttribute("aria-expanded", "false");
        this.insert(item.type, {}, anchorEntry);
      });
      option.setAttribute("role", "menuitem");
      option.append(
        editorNode("span", "rich-insert-icon", item.icon),
        editorNode("strong", "", item.label),
        editorNode("small", "", item.hint),
      );
      panel.append(option);
    });
    panel.addEventListener("keydown", (event) => {
      const options = [...panel.querySelectorAll("button")];
      const index = options.indexOf(document.activeElement);
      if (event.key === "Escape") {
        event.preventDefault();
        close();
      } else if (["ArrowDown", "ArrowRight"].includes(event.key)) {
        event.preventDefault();
        options[(index + 1) % options.length].focus();
      } else if (["ArrowUp", "ArrowLeft"].includes(event.key)) {
        event.preventDefault();
        options[(index - 1 + options.length) % options.length].focus();
      }
    });
    const menu = {
      element,
      open: (source, entry) => {
        anchorEntry = entry;
        opener = source;
        (entry ? entry.element : element).after(panel);
        panel.classList.remove("is-hidden");
        trigger.setAttribute("aria-expanded", "true");
        panel.querySelector("button").focus();
      },
      toggle: (source, entry) => {
        if (!panel.classList.contains("is-hidden")) {
          close();
          return;
        }
        menu.open(source, entry);
      },
    };
    element.append(trigger, panel);
    return menu;
  }
}

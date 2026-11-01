// Pinta el contenido por bloques de un comunicado. Lo comparten la portada y la
// vista previa del editor, asi lo que se aprueba es exactamente lo que se publica.
// Solo crea nodos DOM con textContent: el contenido nunca se interpreta como HTML.

const announcementMarkTags = {
  bold: "strong",
  italic: "em",
  underline: "u",
  strike: "s",
  code: "code",
};

const announcementVideoSources = {
  youtube: (id) => `https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}?rel=0`,
  vimeo: (id) => `https://player.vimeo.com/video/${encodeURIComponent(id)}?dnt=1`,
};

const announcementEventModes = {
  presencial: "Presencial",
  virtual: "Virtual",
  hibrido: "Híbrido",
};

const announcementLongDate = new Intl.DateTimeFormat("es-CO", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: "UTC",
});

function renderNode(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
}

function isSafeAnnouncementUrl(url) {
  return /^(https:\/\/|mailto:|\/media\/announcements\/|\/static\/)/.test(url || "");
}

function renderAnnouncementLink(url, child) {
  const link = document.createElement("a");
  link.href = isSafeAnnouncementUrl(url) ? url : "#";
  if (/^https:\/\//.test(url)) {
    link.target = "_blank";
    link.rel = "noopener noreferrer";
  }
  if (/^\/media\/announcements\//.test(url)) link.setAttribute("download", "");
  link.append(child);
  return link;
}

// Texto con formato: cada fragmento puede combinar marcas y un enlace.
function renderAnnouncementRuns(runs, target) {
  (runs || []).forEach((run) => {
    let node = document.createDocumentFragment();
    String(run.text || "")
      .split("\n")
      .forEach((line, index) => {
        if (index) node.append(document.createElement("br"));
        node.append(document.createTextNode(line));
      });
    (run.marks || []).forEach((mark) => {
      const tag = announcementMarkTags[mark];
      if (!tag) return;
      const wrapper = document.createElement(tag);
      wrapper.append(node);
      node = wrapper;
    });
    if (run.link) node = renderAnnouncementLink(run.link, node);
    target.append(node);
  });
  return target;
}

function renderAnnouncementPicture(image, className) {
  const figure = renderNode("figure", className);
  const picture = document.createElement("img");
  picture.src = isSafeAnnouncementUrl(image.src) ? image.src : "";
  picture.alt = image.alt || "";
  picture.loading = "lazy";
  picture.decoding = "async";
  figure.append(picture);
  if (image.caption) figure.append(renderNode("figcaption", "", image.caption));
  return figure;
}

function formatAnnouncementTime(value) {
  return value ? value.slice(0, 5) : "";
}

function renderAnnouncementEvent(block) {
  const card = renderNode("aside", "rich-event");
  card.setAttribute("aria-label", "Datos del evento");
  card.append(renderNode("span", "rich-event-kicker", "Agenda"));
  const list = renderNode("dl", "rich-event-list");
  const add = (label, value) => {
    if (!value) return;
    list.append(renderNode("dt", "", label), renderNode("dd", "", value));
  };
  let when = announcementLongDate.format(new Date(`${block.start_date}T00:00:00Z`));
  if (block.start_time) when += `, ${formatAnnouncementTime(block.start_time)}`;
  if (block.end_date && block.end_date !== block.start_date) {
    when += ` al ${announcementLongDate.format(new Date(`${block.end_date}T00:00:00Z`))}`;
  }
  if (block.end_time) when += ` hasta las ${formatAnnouncementTime(block.end_time)}`;
  add("Cuándo", when);
  add("Modalidad", announcementEventModes[block.mode] || "");
  add("Dónde", block.location);
  card.append(list);
  if (block.registration_url) {
    const action = renderAnnouncementLink(block.registration_url, document.createTextNode("Inscríbete"));
    action.className = "rich-button primary";
    card.append(action);
  }
  return card;
}

function renderAnnouncementTable(block) {
  const wrap = renderNode("div", "rich-table-wrap");
  wrap.tabIndex = 0;
  const table = renderNode("table", "rich-table");
  if (block.caption) table.append(renderNode("caption", "", block.caption));
  const rows = [...(block.rows || [])];
  if (block.header && rows.length) {
    const head = document.createElement("thead");
    const row = document.createElement("tr");
    rows.shift().forEach((cell) => {
      const th = renderNode("th", "", cell);
      th.scope = "col";
      row.append(th);
    });
    head.append(row);
    table.append(head);
  }
  const body = document.createElement("tbody");
  rows.forEach((cells) => {
    const row = document.createElement("tr");
    cells.forEach((cell) => row.append(renderNode("td", "", cell)));
    body.append(row);
  });
  table.append(body);
  wrap.append(table);
  return wrap;
}

const announcementBlockRenderers = {
  paragraph: (block) => renderAnnouncementRuns(block.runs, renderNode("p")),
  heading: (block) =>
    renderAnnouncementRuns(block.runs, renderNode(block.level === 3 ? "h5" : "h4", "rich-heading")),
  list: (block) => {
    const list = renderNode(block.style === "ordered" ? "ol" : "ul", "rich-list");
    (block.items || []).forEach((item) => list.append(renderAnnouncementRuns(item, renderNode("li"))));
    return list;
  },
  quote: (block) => {
    const quote = renderNode("blockquote", "rich-quote");
    quote.append(renderAnnouncementRuns(block.runs, renderNode("p")));
    if (block.cite) quote.append(renderNode("cite", "", block.cite));
    return quote;
  },
  callout: (block) => {
    const callout = renderNode("aside", `rich-callout is-${block.tone}`);
    if (block.title) callout.append(renderNode("strong", "", block.title));
    if (block.runs?.length) callout.append(renderAnnouncementRuns(block.runs, renderNode("p")));
    return callout;
  },
  divider: () => renderNode("hr", "rich-divider"),
  image: (block) => renderAnnouncementPicture(block, `rich-image is-${block.size || "normal"}`),
  gallery: (block) => {
    const gallery = renderNode("div", "rich-gallery");
    (block.images || []).forEach((image) => gallery.append(renderAnnouncementPicture(image, "rich-gallery-item")));
    return gallery;
  },
  video: (block) => {
    const figure = renderNode("figure", "rich-video");
    const frame = renderNode("div", "rich-video-frame");
    const source = announcementVideoSources[block.provider];
    if (source) {
      const iframe = document.createElement("iframe");
      iframe.src = source(block.video_id);
      iframe.title = block.title || "Video";
      iframe.loading = "lazy";
      iframe.referrerPolicy = "strict-origin-when-cross-origin";
      iframe.allow = "accelerometer; encrypted-media; gyroscope; picture-in-picture; fullscreen";
      frame.append(iframe);
    }
    figure.append(frame);
    if (block.caption) figure.append(renderNode("figcaption", "", block.caption));
    return figure;
  },
  button: (block) => {
    const wrap = renderNode("p", "rich-button-row");
    const button = renderAnnouncementLink(block.url, document.createTextNode(block.label));
    button.className = `rich-button ${block.variant === "secondary" ? "secondary" : "primary"}`;
    wrap.append(button);
    return wrap;
  },
  file: (block) => {
    const file = renderAnnouncementLink(block.url, document.createDocumentFragment());
    file.className = "rich-file";
    file.append(renderNode("span", "rich-file-icon", "PDF"));
    const copy = renderNode("span", "rich-file-copy");
    copy.append(renderNode("strong", "", block.label));
    if (block.description) copy.append(renderNode("small", "", block.description));
    file.append(copy, renderNode("span", "rich-file-action", "Descargar"));
    return file;
  },
  table: renderAnnouncementTable,
  event: renderAnnouncementEvent,
};

function renderAnnouncementBlocks(blocks) {
  const fragment = document.createDocumentFragment();
  (blocks || []).forEach((block) => {
    const render = announcementBlockRenderers[block.type];
    if (render) fragment.append(render(block));
  });
  return fragment;
}

// Bloques de un comunicado antiguo guardado solo como texto plano.
function announcementBlocksFromText(text) {
  return String(text || "")
    .split(/\n\s*\n/)
    .filter((paragraph) => paragraph.trim())
    .map((paragraph) => ({ type: "paragraph", runs: [{ text: paragraph.trim() }] }));
}

function announcementReadingMinutes(item) {
  const words = `${item.summary || ""} ${item.body || ""}`.trim().split(/\s+/).length;
  return Math.max(1, Math.round(words / 200));
}

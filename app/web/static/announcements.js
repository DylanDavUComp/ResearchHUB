const announcementCategoryCopy = {
  NOTICIA: "Noticia",
  COMUNICADO: "Comunicado",
  EVENTO: "Evento",
  CONVOCATORIA: "Convocatoria",
};

const announcementStatusCopy = {
  DRAFT: "Borrador",
  PUBLISHED: "Publicado",
  WITHDRAWN: "Retirado",
};

const announcementDateFormat = new Intl.DateTimeFormat("es-CO", {
  day: "numeric",
  month: "long",
  year: "numeric",
});

const newsElements = {
  window: document.querySelector("#news-window"),
  eyebrow: document.querySelector("#news-eyebrow"),
  title: document.querySelector("#news-title"),
  researchBlog: document.querySelector("#open-research-news"),
  close: document.querySelector("#news-window-close"),
  back: document.querySelector("#news-back"),
  headlines: document.querySelector("#news-headlines"),
  layout: document.querySelector("#news-layout"),
  state: document.querySelector("#news-state"),
  more: document.querySelector("#news-more"),
  teaser: document.querySelector("#news-teaser"),
  teaserTitle: document.querySelector("#news-teaser-title"),
  article: document.querySelector("#news-article"),
  articleMedia: document.querySelector("#news-article-media"),
  articleMeta: document.querySelector("#news-article-meta"),
  articleTitle: document.querySelector("#news-article-title"),
  articleSummary: document.querySelector("#news-article-summary"),
  articleBody: document.querySelector("#news-article-body"),
  articleLink: document.querySelector("#news-article-link"),
};

const announcementAdminElements = {
  body: document.querySelector("#announcement-settings-body"),
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
  close: document.querySelector("#close-announcement-form"),
  cancel: document.querySelector("#cancel-announcement-form"),
};

const newsFeeds = {
  all: {
    category: null,
    eyebrow: "Bitácora del ecosistema",
    title: "Comunicados y noticias",
    closeLabel: "Cerrar comunicados",
    empty: "Aún no hay comunicados publicados. Cuando el equipo de investigación comparta novedades, las verás aquí.",
    error: "No pudimos cargar los comunicados.",
  },
  research: {
    category: "NOTICIA",
    eyebrow: "Blog de investigación",
    title: "Noticias de investigación",
    closeLabel: "Cerrar noticias de investigación",
    empty: "Aún no hay noticias de investigación publicadas. Cuando el equipo comparta hallazgos, los verás aquí.",
    error: "No pudimos cargar las noticias de investigación.",
  },
};

const newsState = { page: 0, totalPages: 0, items: [], feed: newsFeeds.all };
let managedAnnouncements = [];
let announcementUser = null;

function announcementNode(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function announcementMeta(item) {
  const category = announcementCategoryCopy[item.category] || item.category;
  if (!item.published_at) return category;
  return `${category} · ${announcementDateFormat.format(new Date(item.published_at))}`;
}

function renderNewsMedia(item, className) {
  const media = announcementNode("div", className);
  if (item.image_url) {
    const image = document.createElement("img");
    image.src = item.image_url;
    image.alt = item.image_alt || "";
    image.loading = "lazy";
    image.decoding = "async";
    media.append(image);
  } else {
    media.classList.add("is-fallback");
    media.append(announcementNode("span", "", announcementCategoryCopy[item.category] || ""));
    media.setAttribute("aria-hidden", "true");
  }
  return media;
}

function renderNewsEntry(item, isLead) {
  const entry = announcementNode("article", isLead ? "news-entry is-lead" : "news-entry");
  const copy = announcementNode("div", "news-entry-copy");
  const time = announcementNode("time", "news-entry-meta", announcementMeta(item));
  time.dateTime = item.published_at;
  const heading = announcementNode(isLead ? "h3" : "h4");
  const open = announcementNode("button", "news-entry-open", item.title);
  open.type = "button";
  open.addEventListener("click", () => showNewsArticle(item, open));
  heading.append(open);
  copy.append(time, heading);
  if (isLead) copy.append(announcementNode("p", "", item.summary));
  entry.append(renderNewsMedia(item, "news-entry-media"), copy);
  return entry;
}

function renderNews() {
  newsElements.layout.replaceChildren();
  const [lead, ...rest] = newsState.items;
  if (!lead) return;
  newsElements.layout.append(renderNewsEntry(lead, true));
  if (rest.length) {
    const list = announcementNode("div", "news-list");
    list.append(announcementNode("span", "news-list-title", "Más titulares"));
    rest.forEach((item) => list.append(renderNewsEntry(item, false)));
    newsElements.layout.append(list);
  }
  newsElements.layout.classList.toggle("is-single", !rest.length);
}

function showNewsState(message, withRetry = false) {
  newsElements.state.replaceChildren(document.createTextNode(message));
  if (withRetry) {
    const retry = announcementNode("button", "news-inline-action", "Reintentar");
    retry.type = "button";
    retry.addEventListener("click", () => loadPublicNews(true));
    newsElements.state.append(" ", retry);
  }
  newsElements.state.classList.remove("is-hidden");
}

function renderTeaser() {
  const latest = newsState.items[0];
  newsElements.teaserTitle.textContent = latest?.title || "Aún no hay comunicados publicados";
  newsElements.teaserTitle.disabled = !latest;
  if (latest) newsElements.teaserTitle.setAttribute("aria-label", `Leer el comunicado más reciente: ${latest.title}`);
}

async function loadPublicNews(reset = false) {
  if (reset) {
    newsState.page = 0;
    newsState.items = [];
  }
  newsElements.window.setAttribute("aria-busy", "true");
  newsElements.more.disabled = true;
  try {
    const feed = newsState.feed;
    const params = new URLSearchParams({ page: newsState.page + 1, page_size: 5 });
    if (feed.category) params.set("category", feed.category);
    const response = await fetch(`/api/v1/announcements?${params}`);
    if (!response.ok) throw new Error("unavailable");
    const payload = await response.json();
    if (feed !== newsState.feed) return;
    newsState.page = payload.page;
    newsState.totalPages = payload.total_pages;
    newsState.items = newsState.items.concat(payload.data);
    newsElements.state.classList.add("is-hidden");
    renderNews();
    if (!newsState.items.length) {
      showNewsState(feed.empty);
    }
    if (feed === newsFeeds.all) renderTeaser();
  } catch (error) {
    if (!newsState.items.length) {
      newsElements.layout.replaceChildren();
      if (newsState.feed === newsFeeds.all) {
        newsElements.teaserTitle.textContent = "Comunicados no disponibles por ahora";
        newsElements.teaserTitle.disabled = true;
      }
    }
    showNewsState(newsState.feed.error, true);
  } finally {
    newsElements.window.setAttribute("aria-busy", "false");
    newsElements.more.disabled = false;
    newsElements.more.classList.toggle("is-hidden", newsState.page >= newsState.totalPages);
  }
}

function showNewsHeadlines() {
  newsElements.article.classList.add("is-hidden");
  newsElements.back.classList.add("is-hidden");
  newsElements.headlines.classList.remove("is-hidden");
  newsElements.window.scrollTop = 0;
  newsElements.window.lastHeadline?.focus();
}

function showNewsArticle(item, trigger) {
  newsElements.window.lastHeadline = trigger;
  newsElements.articleMedia.replaceWith(renderNewsMedia(item, "news-article-media"));
  newsElements.articleMedia = newsElements.article.querySelector(".news-article-media");
  newsElements.articleMeta.textContent = announcementMeta(item);
  newsElements.articleTitle.textContent = item.title;
  newsElements.articleSummary.textContent = item.summary;
  newsElements.articleBody.replaceChildren(
    ...item.body
      .split(/\n\s*\n/)
      .filter((paragraph) => paragraph.trim())
      .map((paragraph) => announcementNode("p", "", paragraph.trim())),
  );
  newsElements.articleLink.classList.toggle("is-hidden", !item.link_url);
  newsElements.articleLink.href = item.link_url || "#";
  newsElements.headlines.classList.add("is-hidden");
  newsElements.article.classList.remove("is-hidden");
  newsElements.back.classList.remove("is-hidden");
  if (!newsElements.window.open) openNewsWindow(trigger);
  newsElements.window.scrollTop = 0;
  newsElements.articleTitle.focus();
}

function selectNewsFeed(feed) {
  newsElements.eyebrow.textContent = feed.eyebrow;
  newsElements.title.textContent = feed.title;
  newsElements.close.setAttribute("aria-label", feed.closeLabel);
  if (newsState.feed === feed) return Promise.resolve();
  newsState.feed = feed;
  newsElements.layout.replaceChildren(announcementNode("div", "news-placeholder"));
  newsElements.state.classList.add("is-hidden");
  newsElements.more.classList.add("is-hidden");
  return loadPublicNews(true);
}

function openNewsWindow(trigger) {
  newsElements.window.returnFocus = trigger;
  if (!newsElements.window.open) newsElements.window.showModal();
}

newsElements.teaser.addEventListener("click", () => {
  selectNewsFeed(newsFeeds.all);
  showNewsHeadlines();
  openNewsWindow(newsElements.teaser);
});
newsElements.researchBlog.addEventListener("click", () => {
  selectNewsFeed(newsFeeds.research);
  showNewsHeadlines();
  openNewsWindow(newsElements.researchBlog);
});
newsElements.teaserTitle.addEventListener("click", async () => {
  await selectNewsFeed(newsFeeds.all);
  if (newsState.items[0]) showNewsArticle(newsState.items[0], newsElements.teaserTitle);
});
newsElements.back.addEventListener("click", showNewsHeadlines);
newsElements.close.addEventListener("click", () => newsElements.window.close());
newsElements.window.addEventListener("click", (event) => {
  if (event.target === newsElements.window) newsElements.window.close();
});
newsElements.window.addEventListener("close", () => {
  newsElements.window.lastHeadline = null;
  newsElements.window.returnFocus?.focus();
});
newsElements.more.addEventListener("click", () => loadPublicNews());

async function announcementJson(url, options = {}) {
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
  const cell = announcementNode("td", "", message);
  cell.colSpan = 5;
  row.append(cell);
  announcementAdminElements.body.replaceChildren(row);
}

async function loadAnnouncementSettings(user) {
  if (!["Administrador", "Super administrador"].includes(user.role)) return;
  announcementUser = user;
  try {
    const payload = await announcementJson("/api/v1/admin/announcements?page_size=100");
    managedAnnouncements = payload.data;
    renderAnnouncementSettings();
  } catch (error) {
    announcementRowMessage(error.message);
  }
}

function announcementActionButton(label, action, variant = "") {
  const button = announcementNode("button", `table-button ${variant}`, label);
  button.type = "button";
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
      const title = announcementNode("td");
      title.append(announcementNode("strong", "", item.title), announcementNode("small", "table-secondary", item.summary));
      const status = announcementNode("td");
      status.append(announcementNode("span", `status-pill announcement-status-${item.status.toLowerCase()}`, announcementStatusCopy[item.status]));
      const actions = announcementNode("td");
      const wrap = announcementNode("div", "action-buttons");
      if (item.status !== "PUBLISHED") {
        wrap.append(announcementActionButton("Editar", () => openAnnouncementDialog(item)));
        wrap.append(announcementActionButton("Publicar", () => changeAnnouncementState(item, "publication")));
      } else {
        wrap.append(announcementActionButton("Retirar", () => changeAnnouncementState(item, "withdrawal"), "danger"));
      }
      if (item.status === "DRAFT") {
        wrap.append(announcementActionButton("Eliminar", () => deleteAnnouncement(item), "danger"));
      }
      actions.append(wrap);
      row.append(
        title,
        announcementNode("td", "", announcementCategoryCopy[item.category]),
        status,
        announcementNode("td", "", item.published_at ? announcementDateFormat.format(new Date(item.published_at)) : "—"),
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
  form.formTitle.textContent = item ? "Editar comunicado" : "Nuevo comunicado";
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
  form.message.textContent = "Guardando borrador...";
  try {
    await announcementJson(id ? `/api/v1/admin/announcements/${id}` : "/api/v1/admin/announcements", {
      method: id ? "PATCH" : "POST",
      body: JSON.stringify(payload),
    });
    form.dialog.close();
    await loadAnnouncementSettings(announcementUser);
  } catch (error) {
    form.message.textContent = error.message;
  }
}

async function changeAnnouncementState(item, action) {
  try {
    await announcementJson(`/api/v1/admin/announcements/${item.id}/${action}`, {
      method: "POST",
      body: JSON.stringify({ version: item.version }),
    });
    await loadAnnouncementSettings(announcementUser);
    loadPublicNews(true);
  } catch (error) {
    window.alert(error.message);
  }
}

async function deleteAnnouncement(item) {
  if (!window.confirm(`¿Eliminar el borrador "${item.title}"?`)) return;
  try {
    await announcementJson(`/api/v1/admin/announcements/${item.id}`, { method: "DELETE" });
    await loadAnnouncementSettings(announcementUser);
  } catch (error) {
    window.alert(error.message);
  }
}

announcementAdminElements.newButton.addEventListener("click", () => openAnnouncementDialog());
announcementAdminElements.form.addEventListener("submit", saveAnnouncement);
[announcementAdminElements.close, announcementAdminElements.cancel].forEach((button) => {
  button.addEventListener("click", () => announcementAdminElements.dialog.close());
});

loadPublicNews(true);

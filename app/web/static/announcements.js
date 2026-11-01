const announcementCategoryCopy = {
  NOTICIA: "Noticia",
  COMUNICADO: "Comunicado",
  EVENTO: "Evento",
  CONVOCATORIA: "Convocatoria",
};

const announcementDateFormat = new Intl.DateTimeFormat("es-CO", {
  day: "numeric",
  month: "long",
  year: "numeric",
});

const newsElements = {
  window: document.querySelector("#news-window"),
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
  articleShare: document.querySelector("#news-article-share"),
  articleShareStatus: document.querySelector("#news-article-share-status"),
};

const newsState = { page: 0, totalPages: 0, items: [], loaded: false };

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
    const response = await fetch(`/api/v1/announcements?page=${newsState.page + 1}&page_size=5`);
    if (!response.ok) throw new Error("unavailable");
    const payload = await response.json();
    newsState.page = payload.page;
    newsState.totalPages = payload.total_pages;
    newsState.items = newsState.items.concat(payload.data);
    newsElements.state.classList.add("is-hidden");
    renderNews();
    if (!newsState.items.length) {
      showNewsState("Aún no hay comunicados publicados. Cuando el equipo de investigación comparta novedades, las verás aquí.");
    }
    renderTeaser();
  } catch (error) {
    if (!newsState.items.length) {
      newsElements.layout.replaceChildren();
      newsElements.teaserTitle.textContent = "Comunicados no disponibles por ahora";
      newsElements.teaserTitle.disabled = true;
    }
    showNewsState("No pudimos cargar los comunicados.", true);
  } finally {
    newsElements.window.setAttribute("aria-busy", "false");
    newsElements.more.disabled = false;
    newsElements.more.classList.toggle("is-hidden", newsState.page >= newsState.totalPages);
  }
}

// Cada comunicado tiene un enlace directo: /?comunicado=<id>.
function setNewsDeepLink(id) {
  const url = new URL(window.location.href);
  if (id) url.searchParams.set("comunicado", id);
  else url.searchParams.delete("comunicado");
  window.history.replaceState(null, "", url);
}

async function copyNewsLink() {
  const url = new URL("/", window.location.origin);
  url.searchParams.set("comunicado", newsElements.articleShare.dataset.id);
  try {
    await navigator.clipboard.writeText(url.toString());
    newsElements.articleShareStatus.textContent = "Enlace copiado.";
  } catch (error) {
    newsElements.articleShareStatus.textContent = url.toString();
  }
}

async function openLinkedNews() {
  const id = new URLSearchParams(window.location.search).get("comunicado");
  if (!id || !/^[0-9a-f-]{36}$/.test(id)) return;
  try {
    const response = await fetch(`/api/v1/announcements/${id}`);
    if (!response.ok) throw new Error("unavailable");
    showNewsArticle(await response.json(), newsElements.teaserTitle);
  } catch (error) {
    setNewsDeepLink(null);
  }
}

function showNewsHeadlines() {
  setNewsDeepLink(null);
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
  newsElements.articleMeta.textContent = `${announcementMeta(item)} · ${announcementReadingMinutes(item)} min de lectura`;
  newsElements.articleTitle.textContent = item.title;
  newsElements.articleSummary.textContent = item.summary;
  newsElements.articleBody.replaceChildren(
    renderAnnouncementBlocks(item.content?.length ? item.content : announcementBlocksFromText(item.body)),
  );
  newsElements.articleShare.dataset.id = item.id;
  newsElements.articleShareStatus.textContent = "";
  setNewsDeepLink(item.id);
  newsElements.articleLink.classList.toggle("is-hidden", !item.link_url);
  newsElements.articleLink.href = item.link_url || "#";
  newsElements.headlines.classList.add("is-hidden");
  newsElements.article.classList.remove("is-hidden");
  newsElements.back.classList.remove("is-hidden");
  if (!newsElements.window.open) openNewsWindow(trigger);
  newsElements.window.scrollTop = 0;
  newsElements.articleTitle.focus();
}

function openNewsWindow(trigger) {
  newsElements.window.returnFocus = trigger;
  if (!newsElements.window.open) newsElements.window.showModal();
}

newsElements.teaser.addEventListener("click", () => {
  showNewsHeadlines();
  openNewsWindow(newsElements.teaser);
});
newsElements.teaserTitle.addEventListener("click", () => {
  if (newsState.items[0]) showNewsArticle(newsState.items[0], newsElements.teaserTitle);
});
newsElements.back.addEventListener("click", showNewsHeadlines);
newsElements.close.addEventListener("click", () => newsElements.window.close());
newsElements.window.addEventListener("click", (event) => {
  if (event.target === newsElements.window) newsElements.window.close();
});
newsElements.window.addEventListener("close", () => {
  setNewsDeepLink(null);
  newsElements.window.lastHeadline = null;
  newsElements.window.returnFocus?.focus();
});
newsElements.more.addEventListener("click", () => loadPublicNews());
newsElements.articleShare.addEventListener("click", copyNewsLink);

loadPublicNews(true);
openLinkedNews();

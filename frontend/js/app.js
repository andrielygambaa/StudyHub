const API = "/api";
const workspace = document.getElementById("workspace");
const userSelect = document.getElementById("user-select");
const connectionLabel = document.getElementById("connection-label");
const state = {
  users: [],
  subjects: [],
  userId: null,
  dashboard: null,
  view: "dashboard",
  topics: [],
  decks: [],
  managedDeck: null,
  achievements: [],
  achievementCatalog: [],
  xp: [],
  reviewDeckId: null,
  reviewCards: [],
  reviewIndex: 0,
  reviewRevealed: false,
  timer: null,
  timerSeconds: 0,
  timerInitialSeconds: 0,
  timerRunning: false,
  timerSubjectId: "",
  timerTopicId: "",
  timerDurationMinutes: 25,
};

const viewInfo = {
  dashboard: ["Visão geral", "Acompanhe sua rotina e continue de onde parou."],
  pomodoro: ["Pomodoro", "Um intervalo de foco por vez. Seu progresso fica registrado."],
  planner: ["Planner de estudos", "Organize seus tópicos e acompanhe cada avanço."],
  flashcards: ["Flashcards", "Revise no seu ritmo e fortaleça o que aprendeu."],
  gamification: ["Conquistas", "Cada sessão concluída conta na sua jornada."],
  subjects: ["Matérias", "Organize as áreas que fazem parte dos seus estudos."],
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

async function request(path, options = {}) {
  const config = { ...options, headers: { ...(options.headers || {}) } };
  if (config.body && typeof config.body !== "string") {
    config.headers["Content-Type"] = "application/json";
    config.body = JSON.stringify(config.body);
  }

  let response;
  try {
    response = await fetch(`${API}${path}`, config);
  } catch {
    throw new Error("Não foi possível falar com o servidor StudyHub.");
  }

  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.erro || data.mensagem || `A solicitação falhou (${response.status}).`);
  }
  return data;
}

function notify(message, type = "success") {
  const region = document.getElementById("toast-region");
  const toast = document.createElement("div");
  toast.className = `toast${type === "error" ? " error" : ""}`;
  toast.textContent = message;
  region.append(toast);
  window.setTimeout(() => toast.remove(), 4200);
}

function handleError(error) {
  notify(error.message || "Não foi possível concluir a operação.", "error");
}

function currentUser() {
  return state.users.find((user) => String(user.id) === String(state.userId)) || null;
}

function subjectById(id) {
  return state.subjects.find((subject) => String(subject.id) === String(id));
}

function subjectOptions(selected = "") {
  return state.subjects.map((subject) =>
    `<option value="${subject.id}" ${String(subject.id) === String(selected) ? "selected" : ""}>${escapeHtml(subject.nome)}</option>`
  ).join("");
}

function setConnection(connected, message) {
  connectionLabel.textContent = message;
  connectionLabel.previousElementSibling.classList.toggle("offline", !connected);
}

function heading(tag = "") {
  const [title, subtitle] = viewInfo[state.view] || viewInfo.dashboard;
  return `<div class="page-heading"><div><h1>${title}</h1><p>${subtitle}</p></div>${tag ? `<span class="heading-tag">${tag}</span>` : ""}</div>`;
}

function panelHeading(title, subtitle = "") {
  return `<div class="panel-heading"><div><h2>${title}</h2>${subtitle ? `<p>${subtitle}</p>` : ""}</div></div>`;
}

function emptyState(title, message) {
  return `<div class="empty-state"><strong>${title}</strong>${message}</div>`;
}

async function initialize() {
  try {
    const [, users, subjects] = await Promise.all([
      request("/health"),
      request("/usuarios"),
      request("/materias"),
    ]);
    state.users = users;
    state.subjects = subjects;
    setConnection(true, "Banco conectado");
    const savedId = localStorage.getItem("studyhub.usuario");
    state.userId = users.some((user) => String(user.id) === savedId)
      ? savedId
      : (users[0] ? String(users[0].id) : null);
    renderUserSelect();
    if (state.userId) {
      localStorage.setItem("studyhub.usuario", state.userId);
      await loadDashboard();
    } else {
      render();
    }
  } catch (error) {
    setConnection(false, "Servidor indisponível");
    workspace.innerHTML = `${heading()}<div class="welcome-card"><div class="welcome-mark">!</div><h1>Não foi possível conectar</h1><p>${escapeHtml(error.message)} Confira se o Flask e o banco de dados estão em execução e tente novamente.</p><button class="button primary" type="button" data-action="retry">Tentar novamente</button></div>`;
  }
}

function renderUserSelect() {
  userSelect.innerHTML = state.users.length
    ? state.users.map((user) => `<option value="${user.id}" ${String(user.id) === String(state.userId) ? "selected" : ""}>${escapeHtml(user.nome)}</option>`).join("")
    : '<option value="">Nenhum usuário</option>';
  userSelect.disabled = state.users.length === 0 || state.timerSeconds > 0;
}

async function loadDashboard() {
  if (!state.userId) {
    state.dashboard = null;
    render();
    return;
  }
  state.dashboard = await request(`/usuarios/${state.userId}/dashboard`);
  render();
}

function render() {
  document.querySelectorAll("[data-view]").forEach((item) => {
    if (item.classList.contains("nav-item")) item.classList.toggle("active", item.dataset.view === state.view);
  });
  renderUserSelect();
  if (!state.userId) {
    workspace.innerHTML = `${heading()}<div class="welcome-card"><div class="welcome-mark">S</div><h1>Seu próximo capítulo começa aqui.</h1><p>Crie seu perfil para organizar matérias, focar com Pomodoro e acompanhar sua evolução.</p>${userForm()}</div>`;
    return;
  }
  const user = currentUser();
  const name = escapeHtml((user?.nome || "estudante").split(" ")[0]);
  const greeting = `${heading(state.dashboard ? `NÍVEL ${state.dashboard.usuario.nivel}` : "")}`;
  const views = {
    dashboard: renderDashboard(name),
    pomodoro: renderPomodoro(),
    planner: renderPlanner(),
    flashcards: renderFlashcards(),
    gamification: renderGamification(),
    subjects: renderSubjects(),
  };
  workspace.innerHTML = `${greeting}${views[state.view] || views.dashboard}`;
}

function renderDashboard(firstName) {
  const data = state.dashboard;
  if (!data) return `<div class="loading-state"><span class="loader"></span><p>Carregando seu progresso...</p></div>`;
  const week = data.pomodoro.minutos_por_dia || [];
  const maxMinutes = Math.max(1, ...week.map((day) => Number(day.minutos) || 0));
  const dayLabels = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"];
  const chart = week.map((day) => {
    const minutes = Number(day.minutos) || 0;
    const label = new Date(`${day.data}T12:00:00`).getDay();
    const height = minutes ? Math.max(5, (minutes / maxMinutes) * 100) : 2;
    return `<div class="chart-day"><span class="chart-value">${minutes ? `${minutes}m` : "—"}</span><div class="chart-track"><div class="chart-bar" style="height:${height}%"></div></div><span class="chart-day-label">${dayLabels[label]}</span></div>`;
  }).join("");
  const progress = (data.planner.progresso_por_materia || []).map((item) => {
    const total = Number(item.total) || 0;
    const reviewed = Number(item.revisados) || 0;
    const percent = Number(item.percentual_revisado) || (total ? Math.round(reviewed / total * 100) : 0);
    return `<div class="progress-row"><span>${escapeHtml(item.materia || "Matéria")}</span><div class="progress-track"><div class="progress-fill" style="width:${percent}%"></div></div><span class="progress-count">${reviewed}/${total}</span></div>`;
  }).join("");
  const activities = (data.gamificacao.ultimos_xp || []).slice(0, 4).map((item) =>
    `<div class="activity-row"><span>${escapeHtml(item.descricao || item.origem || "Atividade")}</span><span class="xp-positive">+${Number(item.pontos) || 0} XP</span></div>`
  ).join("");

  return `
    <p class="welcome-line">Bom dia, ${firstName} ✦</p>
    <div class="stats-grid">
      <article class="stat-card" style="--stat-glow:rgba(72,152,247,.22)"><span class="stat-label">Foco nesta semana</span><strong class="stat-value">${Number(data.pomodoro.minutos_na_semana) || 0}<small> min</small></strong><span class="stat-hint">${Number(data.pomodoro.sessoes_concluidas) || 0} sessões concluídas</span></article>
      <article class="stat-card" style="--stat-glow:rgba(148,116,255,.2)"><span class="stat-label">Tópicos revisados</span><strong class="stat-value">${Number(data.planner.topicos_revisados) || 0}</strong><span class="stat-hint">um avanço de cada vez</span></article>
      <article class="stat-card" style="--stat-glow:rgba(54,221,160,.17)"><span class="stat-label">Para revisar hoje</span><strong class="stat-value">${Number(data.flashcards.cartoes_para_revisar_hoje) || 0}</strong><span class="stat-hint">flashcards no seu ritmo</span></article>
      <article class="stat-card" style="--stat-glow:rgba(255,196,93,.15)"><span class="stat-label">Pontos de experiência</span><strong class="stat-value">${Number(data.usuario.xp_total) || 0}<small> XP</small></strong><span class="stat-hint">nível ${Number(data.usuario.nivel) || 1}</span></article>
    </div>
    <div class="dashboard-grid">
      <section class="panel">${panelHeading("Seu foco", "Minutos estudados nos últimos 7 dias")}<div class="chart">${chart}</div></section>
      <section class="panel">${panelHeading("Planner", "Tópicos revisados por matéria")}${progress ? `<div class="progress-list">${progress}</div>` : emptyState("Tudo começa por aqui", "Adicione tópicos ao seu planner para acompanhar o progresso.")}</section>
      <section class="panel">${panelHeading("Atividade recente", "XP conquistado ao longo dos estudos")}${activities ? `<div class="activity-list">${activities}</div>` : emptyState("Sua jornada começa agora", "Conclua uma sessão ou revise um tópico para ganhar XP.")}</section>
      <section class="panel">${panelHeading("Próximo passo", "Escolha como quer estudar hoje")}<div class="quick-actions"><button class="quick-action" data-view="pomodoro"><strong>◷ Começar foco</strong><span>Uma sessão Pomodoro</span></button><button class="quick-action" data-view="planner"><strong>▤ Organizar estudos</strong><span>Avance em um tópico</span></button><button class="quick-action" data-view="flashcards"><strong>▱ Revisar cartões</strong><span>${Number(data.flashcards.cartoes_para_revisar_hoje) || 0} para hoje</span></button></div></section>
    </div>`;
}

function userForm() {
  return `<form class="form-grid" data-form="user"><div class="form-field"><label for="user-name">Seu nome</label><input class="field" id="user-name" name="nome" required maxlength="100" placeholder="Como podemos te chamar?"></div><div class="form-field"><label for="user-email">E-mail</label><input class="field" id="user-email" name="email" type="email" required maxlength="254" placeholder="voce@email.com"></div><div class="form-actions form-field full"><button class="button primary" type="submit">Criar meu perfil</button></div></form>`;
}

function renderPomodoro() {
  const topics = state.topics;
  const timer = formatTime(state.timerSeconds || state.timerInitialSeconds || state.timerDurationMinutes * 60);
  return `
    <div class="pomodoro-layout">
      <section class="panel timer-panel">
        <div class="timer-ring"><div><p class="timer-kicker">${state.timerRunning ? "FOCO EM ANDAMENTO" : "HORA DE FOCAR"}</p><div class="timer-display" id="timer-display">${timer}</div><p class="timer-subtitle">${state.timerRunning ? "Seu foco está sendo registrado." : "Prepare seu espaço e comece quando quiser."}</p><div class="timer-actions">${state.timerRunning ? '<button class="button secondary" data-action="pause-timer">Pausar</button><button class="button danger" data-action="stop-timer">Encerrar</button>' : `<button class="button primary" data-action="start-timer" ${state.subjects.length ? "" : "disabled"}>${state.timerSeconds ? "Retomar foco" : "Iniciar foco"}</button>`}</div></div></div>
      </section>
      <section class="panel">${panelHeading("Preparar sessão", "Escolha matéria, tópico e duração")}      <div class="form-field"><label for="timer-subject">Matéria</label><select class="select-field" id="timer-subject" ${state.timerRunning || state.timerSeconds > 0 ? "disabled" : ""}><option value="">Selecione uma matéria</option>${subjectOptions(state.timerSubjectId)}</select></div><div class="form-field" style="margin-top:13px"><label for="timer-topic">Tópico (opcional)</label><select class="select-field" id="timer-topic" ${state.timerRunning || state.timerSeconds > 0 ? "disabled" : ""}><option value="">Sem tópico específico</option>${topics.map((topic) => `<option value="${topic.id}" ${String(topic.id) === String(state.timerTopicId) ? "selected" : ""}>${escapeHtml(topic.titulo)}</option>`).join("")}</select></div>      <div class="form-field" style="margin-top:13px"><label for="timer-duration">Duração da sessão</label><select class="select-field" id="timer-duration" ${state.timerRunning || state.timerSeconds > 0 ? "disabled" : ""}><option value="25" ${state.timerDurationMinutes === 25 ? "selected" : ""}>25 minutos · Pomodoro</option><option value="50" ${state.timerDurationMinutes === 50 ? "selected" : ""}>50 minutos · foco profundo</option><option value="15" ${state.timerDurationMinutes === 15 ? "selected" : ""}>15 minutos · sessão curta</option><option value="custom" ${![15, 25, 50].includes(state.timerDurationMinutes) ? "selected" : ""}>Personalizar</option></select></div><div class="form-field" id="custom-duration-wrap" ${![15, 25, 50].includes(state.timerDurationMinutes) ? "" : "hidden"} style="margin-top:10px"><label for="custom-duration">Minutos (1–240)</label><input class="field" type="number" id="custom-duration" min="1" max="240" value="${state.timerDurationMinutes}"></div><p class="topic-meta" style="line-height:1.55;margin-top:16px">A sessão é registrada ao terminar. Se você encerrar antes do tempo, ela fica salva como interrompida e não concede XP.</p></section>
    </div>
    <section class="panel" style="margin-top:16px">${panelHeading("Sessões recentes", "Seu histórico de foco")}<div id="session-list">${emptyState("Sem sessões registradas", "Quando concluir uma sessão, ela aparecerá aqui.")}</div></section>`;
}

function formatTime(seconds) {
  const safe = Math.max(0, Number(seconds) || 0);
  return `${String(Math.floor(safe / 60)).padStart(2, "0")}:${String(safe % 60).padStart(2, "0")}`;
}

async function refreshTopics() {
  state.topics = state.userId ? await request(`/usuarios/${state.userId}/topicos`) : [];
}

async function refreshSessions() {
  const sessions = await request(`/usuarios/${state.userId}/sessoes`);
  const target = document.getElementById("session-list");
  if (!target) return;
  target.innerHTML = sessions.length ? `<div class="activity-list">${sessions.slice(0, 5).map((session) => {
    const subject = subjectById(session.materia_id);
    return `<div class="activity-row"><span>${escapeHtml(subject?.nome || "Sessão")} · ${Number(session.duracao_min)} min${session.concluida ? "" : " · interrompida"}</span><span class="${session.concluida ? "xp-positive" : "progress-count"}">${session.concluida ? "Concluída" : "Salva"}</span></div>`;
  }).join("")}</div>` : emptyState("Sem sessões registradas", "Quando concluir uma sessão, ela aparecerá aqui.");
}

function renderPlanner() {
  const grouped = ["nao_visto", "estudando", "revisado"];
  const names = { nao_visto: "A estudar", estudando: "Em andamento", revisado: "Revisados" };
  const groupedHtml = grouped.map((status) => {
    const items = state.topics.filter((topic) => topic.status === status);
    const content = items.length ? items.map((topic) => `<article class="topic-card"><div><div class="topic-title">${escapeHtml(topic.titulo)}</div><p class="topic-meta">${escapeHtml(subjectById(topic.materia_id)?.nome || "Matéria")}</p></div><div class="topic-actions"><span class="status-pill ${status === "estudando" ? "studying" : status === "revisado" ? "reviewed" : ""}">${names[status]}</span>${status !== "revisado" ? `<button class="button secondary small" data-action="advance-topic" data-id="${topic.id}">Avançar</button>` : ""}<button class="button danger small" data-action="delete-topic" data-id="${topic.id}" aria-label="Excluir tópico ${escapeHtml(topic.titulo)}">Excluir</button></div></article>`).join("") : "";
    return `<h2 class="section-title">${names[status]} <span class="progress-count">(${items.length})</span></h2>${content || emptyState(status === "revisado" ? "Nenhum tópico revisado ainda" : "Tudo em dia", status === "revisado" ? "Tópicos revisados aparecem aqui." : "Adicione um tópico ou avance os que já estão aqui.")}`;
  }).join("");
  const form = state.subjects.length ? `<form data-form="topic" class="form-grid"><div class="form-field"><label for="topic-title">Nome do tópico</label><input class="field" id="topic-title" name="titulo" maxlength="150" required placeholder="Ex.: Funções do 2º grau"></div><div class="form-field"><label for="topic-subject">Matéria</label><select class="select-field" id="topic-subject" name="materia_id" required><option value="">Selecione uma matéria</option>${subjectOptions()}</select></div><div class="form-actions form-field full"><button class="button primary" type="submit">Adicionar tópico</button></div></form>` : emptyState("Cadastre uma matéria primeiro", "Depois você poderá organizar seus tópicos por matéria.") ;
  return `<section class="panel form-panel">${panelHeading("Novo tópico", "Planeje o que quer aprender")}${form}</section><section class="panel">${panelHeading("Seus tópicos", "O status só avança: a estudar → em andamento → revisado")}${groupedHtml}</section>`;
}

async function loadDecks() {
  state.decks = await request(`/usuarios/${state.userId}/baralhos`);
}

function renderFlashcards() {
  const form = state.subjects.length ? `<form data-form="deck" class="form-grid"><div class="form-field"><label for="deck-name">Nome do baralho</label><input class="field" id="deck-name" name="nome" maxlength="100" required placeholder="Ex.: Biologia celular"></div><div class="form-field"><label for="deck-subject">Matéria</label><select class="select-field" id="deck-subject" name="materia_id" required><option value="">Selecione uma matéria</option>${subjectOptions()}</select></div><div class="form-actions form-field full"><button class="button primary" type="submit">Criar baralho</button></div></form>` : emptyState("Cadastre uma matéria primeiro", "Os baralhos são organizados por matéria.");
  const decks = state.decks.length ? `<div class="deck-grid">${state.decks.map((deck) => {
    const subject = subjectById(deck.materia_id);
    const subjectName = deck.materia || subject?.nome || "Matéria";
    const subjectColor = deck.cor || subject?.cor || "#7e88ff";
    const due = Number(deck.para_revisar) || 0;
    const count = Number(deck.total_cartoes) || 0;
    return `<article class="deck-card"><span class="deck-accent" style="background:${escapeHtml(subjectColor)}"></span><div class="deck-main"><h3 class="deck-title">${escapeHtml(deck.nome)}</h3><p class="deck-meta">${escapeHtml(subjectName)} · ${count} ${count === 1 ? "cartão" : "cartões"}${due ? ` · ${due} para revisar` : ""}</p><div class="deck-actions" style="margin-top:12px"><button class="button secondary small" data-action="manage-deck" data-id="${deck.id}">Cartões</button><button class="button secondary small" data-action="add-card" data-id="${deck.id}">+ Cartão</button><button class="button primary small" data-action="review-deck" data-id="${deck.id}">${due ? `Revisar (${due})` : "Estudar baralho"}</button><button class="button danger small" data-action="delete-deck" data-id="${deck.id}">Excluir</button></div></div></article>`;
  }).join("")}</div>` : emptyState("Seus baralhos começam aqui", "Crie um baralho e adicione cartões para praticar.");
  const managed = state.managedDeck ? `<section class="panel" style="margin-top:16px">${panelHeading(`Cartões · ${escapeHtml(state.managedDeck.nome)}`, `${state.managedDeck.cartoes.length} cartões neste baralho`)}${state.managedDeck.cartoes.length ? `<div class="item-list">${state.managedDeck.cartoes.map((card) => `<article class="topic-card"><div><div class="topic-title">${escapeHtml(card.frente)}</div><p class="topic-meta">Próxima revisão: ${escapeHtml(String(card.proxima_revisao || "").slice(0, 10))} · intervalo de ${Number(card.intervalo_dias) || 1} dia(s)</p></div><div class="topic-actions"><button class="button secondary small" data-action="edit-card" data-id="${card.id}">Editar</button><button class="button danger small" data-action="delete-card" data-id="${card.id}">Excluir</button></div></article>`).join("")}</div>` : emptyState("Este baralho ainda está vazio", "Adicione o primeiro cartão para começar.")}<button class="button secondary small" style="margin-top:13px" data-action="close-deck">Fechar cartões</button></section>` : "";
  return `<section class="panel form-panel">${panelHeading("Criar baralho", "Separe os cartões por matéria")}${form}</section><section class="panel">${panelHeading("Seus baralhos", "A repetição espaçada agenda suas próximas revisões")}${decks}</section>${managed}${state.reviewDeckId ? renderReview() : ""}`;
}

function renderReview() {
  const card = state.reviewCards[state.reviewIndex];
  if (!card) return `<section class="panel" style="margin-top:16px">${panelHeading("Revisão concluída")}<div class="empty-state"><strong>Mandou bem!</strong>Você terminou os cartões deste baralho.</div></section>`;
  return `<section class="panel" style="margin-top:16px">${panelHeading("Hora de revisar", `Cartão ${state.reviewIndex + 1} de ${state.reviewCards.length}`)}<div class="review-card"><p class="review-label">Frente do cartão</p><p class="review-text">${escapeHtml(card.frente)}</p>${state.reviewRevealed ? `<p class="review-label">Resposta</p><p class="review-text review-answer">${escapeHtml(card.verso)}</p>` : ""}</div><div class="review-controls">${state.reviewRevealed ? `<button class="button danger" data-action="review-answer" data-correct="false">Errei</button><button class="button primary" data-action="review-answer" data-correct="true">Acertei</button>` : '<button class="button primary" data-action="reveal-card">Mostrar resposta</button>'}<button class="button secondary" data-action="close-review">Fechar revisão</button></div></section>`;
}

async function renderGamificationViewData() {
  const [catalog, achievements, xpData] = await Promise.all([
    request("/conquistas"),
    request(`/usuarios/${state.userId}/conquistas`),
    request(`/usuarios/${state.userId}/xp?limite=20`),
  ]);
  state.achievementCatalog = catalog;
  state.achievements = achievements;
  state.xp = xpData.extrato || [];
}

function renderGamification() {
  const user = state.dashboard?.usuario || currentUser() || {};
  const total = Number(user.xp_total) || 0;
  const current = Number(user.xp_no_nivel) || 0;
  const level = Number(user.nivel) || 1;
  const progress = Math.min(100, current);
  const earned = new Set(state.achievements.map((item) => String(item.codigo || item.conquista?.codigo)));
  const cards = state.achievementCatalog.length ? state.achievementCatalog.map((item) => {
    const unlocked = earned.has(String(item.codigo));
    const unlockedAt = state.achievements.find((entry) => entry.conquista?.codigo === item.codigo)?.desbloqueada_em;
    return `<article class="achievement-card ${unlocked ? "" : "locked"}"><div class="achievement-icon">${unlocked ? "✧" : "◇"}</div><h3>${escapeHtml(item.nome)}</h3><p>${escapeHtml(item.descricao || (unlocked ? "Desbloqueada!" : "Continue estudando para desbloquear."))}${unlockedAt ? ` · ${escapeHtml(String(unlockedAt).slice(0, 10))}` : ""}</p></article>`;
  }).join("") : emptyState("Ainda sem conquistas", "Continue estudando para desbloquear suas primeiras conquistas.");
  const logs = state.xp.length ? `<div class="activity-list">${state.xp.map((entry) => `<div class="activity-row"><span>${escapeHtml(entry.descricao || entry.origem || "Atividade")}<small class="topic-meta"> ${escapeHtml((entry.criado_em || "").toString().slice(0, 10))}</small></span><span class="xp-positive">+${Number(entry.pontos) || 0} XP</span></div>`).join("")}</div>` : emptyState("Sem atividades de XP", "Seu extrato aparece aqui quando você ganhar pontos.");
  return `<div class="level-card"><div class="level-badge">${level}</div><div class="level-info"><h2>Nível ${level} · ${total} XP</h2><p>Faltam ${Number(user.xp_para_proximo_nivel) || 100 - current} XP para o próximo nível.</p><div class="level-track"><div class="level-fill" style="width:${progress}%"></div></div></div></div><section class="panel">${panelHeading("Conquistas", "Marcos alcançados na sua jornada")}<div class="achievement-grid">${cards}</div></section><section class="panel" style="margin-top:16px">${panelHeading("Extrato de XP", "Suas atividades mais recentes")}${logs}</section>`;
}

function renderSubjects() {
  const cards = state.subjects.length ? `<div class="item-list">${state.subjects.map((subject) => `<article class="subject-card"><span class="deck-accent" style="background:${escapeHtml(subject.cor || "#7e88ff")}"></span><div class="deck-main"><h3 class="subject-title">${escapeHtml(subject.nome)}</h3><p class="subject-meta">${escapeHtml(subject.cor || "#6c757d")}</p></div><button class="button danger small" data-action="delete-subject" data-id="${subject.id}">Excluir</button></article>`).join("")}</div>` : emptyState("Nenhuma matéria cadastrada", "Adicione uma matéria para começar a organizar seus estudos.");
  return `<section class="panel form-panel">${panelHeading("Nova matéria", "Escolha um nome e uma cor para identificar seus estudos")}<form data-form="subject" class="form-grid"><div class="form-field"><label for="subject-name">Nome</label><input class="field" id="subject-name" name="nome" required maxlength="60" placeholder="Ex.: Matemática"></div><div class="form-field"><label for="subject-color">Cor de identificação</label><input class="field" id="subject-color" name="cor" type="color" value="#4898f7" style="padding:5px"></div><div class="form-actions form-field full"><button class="button primary" type="submit">Adicionar matéria</button></div></form></section><section class="panel">${panelHeading("Suas matérias")}${cards}</section>`;
}

async function changeView(view) {
  if (!viewInfo[view]) return;
  state.view = view;
  try {
    if (view === "planner") await refreshTopics();
    if (view === "pomodoro") {
      await refreshTopics();
      render();
      await refreshSessions();
      return;
    }
    if (view === "flashcards") await loadDecks();
    if (view === "gamification") await renderGamificationViewData();
    render();
  } catch (error) {
    handleError(error);
    render();
  }
}

async function submitForm(form) {
  const data = Object.fromEntries(new FormData(form).entries());
  if (form.dataset.form === "user") {
    const user = await request("/usuarios", { method: "POST", body: data });
    state.users.push(user);
    state.userId = String(user.id);
    state.view = "dashboard";
    state.topics = [];
    state.decks = [];
    state.managedDeck = null;
    state.achievements = [];
    state.achievementCatalog = [];
    state.xp = [];
    localStorage.setItem("studyhub.usuario", state.userId);
    await loadDashboard();
    notify(`Bem-vinda ao StudyHub, ${user.nome.split(" ")[0]}!`);
    return;
  }
  if (form.dataset.form === "topic") {
    await request(`/usuarios/${state.userId}/topicos`, { method: "POST", body: { ...data, materia_id: Number(data.materia_id) } });
    await refreshTopics();
    render();
    notify("Tópico adicionado ao planner.");
    return;
  }
  if (form.dataset.form === "deck") {
    await request(`/usuarios/${state.userId}/baralhos`, { method: "POST", body: { ...data, materia_id: Number(data.materia_id) } });
    await loadDecks();
    render();
    notify("Baralho criado.");
    return;
  }
  if (form.dataset.form === "subject") {
    await request("/materias", { method: "POST", body: data });
    state.subjects = await request("/materias");
    render();
    notify("Matéria adicionada.");
  }
}

async function advanceTopic(id) {
  const result = await request(`/topicos/${id}/avancar`, { method: "POST" });
  await refreshTopics();
  await loadDashboard();
  const points = Number(result.gamificacao?.pontos) || 0;
  notify(points ? `Tópico avançado · +${points} XP` : "Tópico avançado.");
}

async function deleteTopic(id) {
  if (!window.confirm("Excluir este tópico do planner?")) return;
  await request(`/topicos/${id}`, { method: "DELETE" });
  await refreshTopics();
  render();
  notify("Tópico excluído.");
}

async function startTimer() {
  if (state.timerRunning) return;
  const resuming = state.timerSeconds > 0;
  const subjectId = resuming ? state.timerSubjectId : document.getElementById("timer-subject")?.value;
  if (!subjectId) {
    notify("Selecione uma matéria para iniciar.", "error");
    return;
  }
  const durationSelect = document.getElementById("timer-duration")?.value;
  const customDuration = document.getElementById("custom-duration")?.value;
  const minutes = resuming
    ? state.timerDurationMinutes
    : (durationSelect === "custom" ? Number(customDuration) : Number(durationSelect));
  if (!Number.isInteger(minutes) || minutes < 1 || minutes > 240) {
    notify("Escolha uma duração entre 1 e 240 minutos.", "error");
    return;
  }
  state.timerSubjectId = subjectId;
  state.timerTopicId = document.getElementById("timer-topic")?.value || "";
  if (!state.timerSeconds) {
    state.timerInitialSeconds = minutes * 60;
    state.timerSeconds = state.timerInitialSeconds;
    state.timerDurationMinutes = minutes;
  }
  state.timerRunning = true;
  render();
  state.timer = window.setInterval(async () => {
    state.timerSeconds = Math.max(0, state.timerSeconds - 1);
    const display = document.getElementById("timer-display");
    if (display) display.textContent = formatTime(state.timerSeconds);
    if (!state.timerSeconds) {
      window.clearInterval(state.timer);
      state.timer = null;
      state.timerRunning = false;
      try {
        await saveSession(true);
        notify("Sessão concluída! Seu foco foi registrado.");
      } catch (error) {
        handleError(error);
      }
      await loadDashboard();
      await changeView("pomodoro");
    }
  }, 1000);
}

function pauseTimer() {
  if (state.timer) window.clearInterval(state.timer);
  state.timer = null;
  state.timerRunning = false;
  render();
}

async function saveSession(concluded) {
  const duration = Math.max(1, Math.ceil((state.timerInitialSeconds - state.timerSeconds) / 60));
  const result = await request(`/usuarios/${state.userId}/sessoes`, {
    method: "POST",
    body: {
      materia_id: Number(state.timerSubjectId),
      duracao_min: concluded ? Math.ceil(state.timerInitialSeconds / 60) : duration,
      topico_id: state.timerTopicId ? Number(state.timerTopicId) : null,
      concluida: concluded,
    },
  });
  state.timerSeconds = 0;
  state.timerInitialSeconds = 0;
  state.timerSubjectId = "";
  state.timerTopicId = "";
  state.timerDurationMinutes = 25;
  if (result.gamificacao?.pontos) notify(`+${result.gamificacao.pontos} XP${result.gamificacao.conquistas_desbloqueadas?.length ? " · nova conquista!" : ""}`);
}

async function stopTimer() {
  if (state.timer) window.clearInterval(state.timer);
  state.timer = null;
  state.timerRunning = false;
  await saveSession(false);
  await loadDashboard();
  await changeView("pomodoro");
  notify("Sessão interrompida e salva sem XP.");
}

async function showCardForm(deckId) {
  const deck = await request(`/baralhos/${deckId}`);
  const target = document.getElementById("card-form-target");
  if (target) target.remove();
  const formPanel = document.createElement("section");
  formPanel.className = "panel form-panel";
  formPanel.id = "card-form-target";
  formPanel.innerHTML = `${panelHeading(`Novo cartão · ${escapeHtml(deck.nome)}`, "Frente e verso podem ter até 500 caracteres")}<form data-form="card" data-deck-id="${deckId}" class="form-grid"><div class="form-field"><label for="card-front">Frente</label><textarea class="text-field" id="card-front" name="frente" maxlength="500" required rows="3" placeholder="Pergunta ou conceito"></textarea></div><div class="form-field"><label for="card-back">Verso</label><textarea class="text-field" id="card-back" name="verso" maxlength="500" required rows="3" placeholder="Resposta ou explicação"></textarea></div><div class="form-actions form-field full"><button class="button primary" type="submit">Salvar cartão</button><button class="button secondary" type="button" data-action="cancel-card">Cancelar</button></div></form>`;
  document.querySelector(".page-heading")?.after(formPanel);
  formPanel.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function reviewDeck(id) {
  const cards = await request(`/baralhos/${id}/revisar`);
  if (!cards.length) {
    notify("Não há cartões vencidos. Vamos revisar o baralho todo?", "success");
    state.reviewCards = await request(`/baralhos/${id}/cartoes`);
  } else {
    state.reviewCards = cards;
  }
  state.reviewDeckId = id;
  state.reviewIndex = 0;
  state.reviewRevealed = false;
  render();
  document.querySelector(".review-card")?.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function submitReview(correct) {
  const card = state.reviewCards[state.reviewIndex];
  if (!card) return;
  const result = await request(`/cartoes/${card.id}/revisao`, { method: "POST", body: { acertou: correct } });
  state.reviewIndex += 1;
  state.reviewRevealed = false;
  if (result.gamificacao?.pontos) notify(`${correct ? "Boa!" : "Sem problema"} · +${result.gamificacao.pontos} XP`);
  await loadDashboard();
  await loadDecks();
  render();
  document.querySelector(".review-card")?.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function deleteDeck(id) {
  if (!window.confirm("Excluir este baralho e seus cartões?")) return;
  await request(`/baralhos/${id}`, { method: "DELETE" });
  if (String(state.managedDeck?.id) === String(id)) state.managedDeck = null;
  await loadDecks();
  render();
  notify("Baralho excluído.");
}

async function manageDeck(id) {
  state.managedDeck = await request(`/baralhos/${id}`);
  render();
}

async function editCard(id) {
  const card = state.managedDeck?.cartoes.find((item) => String(item.id) === String(id));
  if (!card) return;
  document.querySelectorAll(".card-edit-form").forEach((form) => form.remove());
  const form = document.createElement("form");
  form.className = "panel form-panel card-edit-form";
  form.dataset.form = "edit-card";
  form.dataset.id = id;
  form.innerHTML = `${panelHeading("Editar cartão")}<div class="form-grid"><div class="form-field"><label for="edit-card-front">Frente</label><textarea class="text-field" id="edit-card-front" name="frente" maxlength="500" required rows="3">${escapeHtml(card.frente)}</textarea></div><div class="form-field"><label for="edit-card-back">Verso</label><textarea class="text-field" id="edit-card-back" name="verso" maxlength="500" required rows="3">${escapeHtml(card.verso)}</textarea></div></div><div class="form-actions"><button class="button primary" type="submit">Salvar alterações</button><button class="button secondary" type="button" data-action="cancel-edit-card">Cancelar</button></div>`;
  document.querySelector(".page-heading")?.after(form);
  form.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function deleteCard(id) {
  if (!window.confirm("Excluir este cartão?")) return;
  await request(`/cartoes/${id}`, { method: "DELETE" });
  if (state.managedDeck) state.managedDeck = await request(`/baralhos/${state.managedDeck.id}`);
  await loadDecks();
  render();
  notify("Cartão excluído.");
}

async function deleteSubject(id) {
  if (!window.confirm("Excluir esta matéria? Só é possível se ela não estiver sendo usada.")) return;
  await request(`/materias/${id}`, { method: "DELETE" });
  state.subjects = await request("/materias");
  render();
  notify("Matéria excluída.");
}

document.addEventListener("click", async (event) => {
  const viewButton = event.target.closest("[data-view]");
  if (viewButton) {
    event.preventDefault();
    await changeView(viewButton.dataset.view);
    return;
  }
  const button = event.target.closest("[data-action]");
  if (!button) return;
  const id = button.dataset.id;
  try {
    switch (button.dataset.action) {
      case "new-user":
        if (!state.userId) {
          workspace.scrollIntoView({ behavior: "smooth" });
          document.getElementById("user-name")?.focus();
          return;
        }
        workspace.innerHTML = `${heading()}<div class="welcome-card"><div class="welcome-mark">+</div><h1>Novo perfil</h1><p>Cadastre outro perfil de estudos neste StudyHub.</p>${userForm()}</div>`;
        document.getElementById("user-name")?.focus();
        return;
      case "retry":
        await initialize();
        return;
      case "start-timer":
        await startTimer();
        return;
      case "pause-timer":
        pauseTimer();
        return;
      case "stop-timer":
        await stopTimer();
        return;
      case "advance-topic":
        await advanceTopic(id);
        return;
      case "delete-topic":
        await deleteTopic(id);
        return;
      case "add-card":
        await showCardForm(id);
        return;
      case "cancel-card":
        document.getElementById("card-form-target")?.remove();
        return;
      case "manage-deck":
        await manageDeck(id);
        return;
      case "close-deck":
        state.managedDeck = null;
        render();
        return;
      case "edit-card":
        await editCard(id);
        return;
      case "cancel-edit-card":
        document.querySelector(".card-edit-form")?.remove();
        return;
      case "delete-card":
        await deleteCard(id);
        return;
      case "review-deck":
        await reviewDeck(id);
        return;
      case "reveal-card":
        state.reviewRevealed = true;
        render();
        return;
      case "review-answer":
        await submitReview(button.dataset.correct === "true");
        return;
      case "close-review":
        state.reviewDeckId = null;
        state.reviewCards = [];
        render();
        return;
      case "delete-deck":
        await deleteDeck(id);
        return;
      case "delete-subject":
        await deleteSubject(id);
        return;
      default:
        return;
    }
  } catch (error) {
    handleError(error);
  }
});

document.addEventListener("submit", async (event) => {
  const form = event.target.closest("form[data-form]");
  if (!form) return;
  event.preventDefault();
  try {
    if (form.dataset.form === "card") {
      const data = Object.fromEntries(new FormData(form).entries());
      await request(`/baralhos/${form.dataset.deckId}/cartoes`, { method: "POST", body: data });
      await loadDecks();
      if (state.managedDeck) state.managedDeck = await request(`/baralhos/${state.managedDeck.id}`);
      render();
      notify("Cartão adicionado ao baralho.");
      return;
    }
    if (form.dataset.form === "edit-card") {
      const data = Object.fromEntries(new FormData(form).entries());
      await request(`/cartoes/${form.dataset.id}`, { method: "PUT", body: data });
      if (state.managedDeck) state.managedDeck = await request(`/baralhos/${state.managedDeck.id}`);
      await loadDecks();
      render();
      notify("Cartão atualizado.");
      return;
    }
    await submitForm(form);
  } catch (error) {
    handleError(error);
  }
});

userSelect.addEventListener("change", async () => {
  state.userId = userSelect.value || null;
  if (state.userId) localStorage.setItem("studyhub.usuario", state.userId);
  else localStorage.removeItem("studyhub.usuario");
  state.dashboard = null;
  state.topics = [];
  state.decks = [];
  state.managedDeck = null;
  state.reviewDeckId = null;
  state.reviewCards = [];
  state.achievements = [];
  state.achievementCatalog = [];
  state.xp = [];
  try {
    await loadDashboard();
    if (state.view !== "dashboard") await changeView(state.view);
  } catch (error) {
    handleError(error);
  }
});

document.addEventListener("change", (event) => {
  if (event.target.id === "timer-subject") {
    state.timerSubjectId = event.target.value;
  }
  if (event.target.id === "timer-topic") {
    state.timerTopicId = event.target.value;
  }
  if (event.target.id === "timer-duration") {
    const custom = document.getElementById("custom-duration-wrap");
    if (custom) custom.hidden = event.target.value !== "custom";
    if (event.target.value !== "custom") state.timerDurationMinutes = Number(event.target.value);
  }
  if (event.target.id === "custom-duration") {
    state.timerDurationMinutes = Number(event.target.value);
  }
});

initialize();

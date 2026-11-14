(() => {
  const T = JSON.parse(document.getElementById("i18n").textContent);
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
  const parse = (s) => { const [y, m, d] = s.split("-").map(Number); return new Date(y, m - 1, d); };

  const today = new Date(); today.setHours(0, 0, 0, 0);
  const todayIso = iso(today);
  const weekEnd = iso(addDays(today, 6));

  const cards = $$("#view-upcoming .ev");              // the server-rendered source of truth
  const months = $$("#view-upcoming .month");
  const views = { week: $("#view-week"), upcoming: $("#view-upcoming"), calendar: $("#view-calendar") };
  const tabs = $$(".tabs button");
  const chips = $$(".vchip");
  const empty = $("#empty");
  const state = { view: "week", venue: "", month: null, calMonth: null, calDay: null };

  const gigs = (n) => `${n} ${T.gigs[n === 1 ? 0 : 1]}`;
  const venueOk = (c) => !state.venue || c.dataset.venue === state.venue;
  const live = () => cards.filter((c) => c.dataset.date >= todayIso && venueOk(c));
  const clone = (c) => { const x = c.cloneNode(true); x.hidden = false; return x; };
  const el = (tag, cls, text) => { const x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; };

  function dayLabel(dateIso) {
    const d = parse(dateIso);
    const long = T.weekdays_long[(d.getDay() + 6) % 7];
    const full = `${long[0].toUpperCase()}${long.slice(1)}`;
    const when = `${d.getDate()}.${d.getMonth() + 1}.`;
    if (dateIso === todayIso) return [T.today, `${full} ${when}`];
    if (dateIso === iso(addDays(today, 1))) return [T.tomorrow, `${full} ${when}`];
    return [full, when];
  }

  /* ---- This week ---- */
  function renderWeek() {
    const box = $(".week-list", views.week);
    box.replaceChildren();
    const inWeek = live().filter((c) => c.dataset.date <= weekEnd);
    const byDay = new Map();
    for (const c of inWeek) (byDay.get(c.dataset.date) || byDay.set(c.dataset.date, []).get(c.dataset.date)).push(c);
    for (const [date, list] of byDay) {
      const [main, sub] = dayLabel(date);
      const g = el("section", "day-group" + (date === todayIso ? " is-today" : ""));
      const h = el("h2", null, main); h.append(el("span", null, sub));
      const grid = el("div", "grid");
      list.forEach((c) => grid.append(clone(c)));
      g.append(h, grid); box.append(g);
    }
    return inWeek.length ? null : T.empty_week;
  }

  /* ---- Coming up ---- */
  function renderUpcoming() {
    const later = live().filter((c) => c.dataset.date > weekEnd);
    const counts = new Map();
    later.forEach((c) => { const k = c.dataset.date.slice(0, 7); counts.set(k, (counts.get(k) || 0) + 1); });
    const keys = [...counts.keys()];
    if (!keys.includes(state.month)) state.month = keys[0] || null;
    const pills = $(".month-pills");
    pills.replaceChildren();
    for (const k of keys) {
      const [y, m] = k.split("-").map(Number);
      const b = el("button", "pill", T.months[m - 1][0].toUpperCase() + T.months[m - 1].slice(1));
      b.append(el("small", null, counts.get(k)));
      b.setAttribute("aria-pressed", String(k === state.month));
      b.title = `${T.months[m - 1]} ${y}`;
      b.addEventListener("click", () => { state.month = k; render(); });
      pills.append(b);
    }
    pills.hidden = keys.length < 2;
    const laterSet = new Set(later);
    cards.forEach((c) => { c.hidden = !laterSet.has(c); });
    months.forEach((m) => { m.hidden = m.dataset.month !== state.month; });
    return keys.length ? null : T.empty;
  }

  /* ---- Calendar ---- */
  function renderCalendar() {
    const all = live();
    const box = $(".cal", views.calendar), dayBox = $(".cal-day", views.calendar);
    box.replaceChildren(); dayBox.replaceChildren();
    if (!all.length) return T.empty;
    const first = parse(all[0].dataset.date), last = parse(all[all.length - 1].dataset.date);
    const minKey = first.getFullYear() * 12 + first.getMonth(), maxKey = last.getFullYear() * 12 + last.getMonth();
    const nowKey = today.getFullYear() * 12 + today.getMonth();
    if (state.calMonth == null) state.calMonth = Math.min(Math.max(nowKey, minKey), maxKey);
    state.calMonth = Math.min(Math.max(state.calMonth, minKey), maxKey);
    const y = Math.floor(state.calMonth / 12), m = state.calMonth % 12;

    const byDate = new Map();
    for (const c of all) (byDate.get(c.dataset.date) || byDate.set(c.dataset.date, []).get(c.dataset.date)).push(c);
    const selected = state.calDay && byDate.get(state.calDay) ? state.calDay
      : (byDate.has(todayIso) && state.calMonth === nowKey ? todayIso : null);

    const head = el("div", "cal-head");
    const title = el("h2", null, `${T.months[m][0].toUpperCase()}${T.months[m].slice(1)} ${y}`);
    const nav = el("div", "cal-nav");
    const prev = el("button", null, "‹"), next = el("button", null, "›");
    prev.setAttribute("aria-label", T.prev); next.setAttribute("aria-label", T.next);
    prev.disabled = state.calMonth <= minKey; next.disabled = state.calMonth >= maxKey;
    prev.addEventListener("click", () => { state.calMonth--; state.calDay = null; render(); });
    next.addEventListener("click", () => { state.calMonth++; state.calDay = null; render(); });
    nav.append(prev, next); head.append(title, nav);

    const grid = el("div", "cal-grid");
    T.weekdays.forEach((w) => grid.append(el("div", "cal-dow", w)));
    const offset = (new Date(y, m, 1).getDay() + 6) % 7;
    for (let i = 0; i < offset; i++) grid.append(el("div"));
    const days = new Date(y, m + 1, 0).getDate();
    for (let d = 1; d <= days; d++) {
      const key = `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      const list = byDate.get(key) || [];
      const cell = el("button", "cal-cell" + (list.length ? " has" : "") + (key === todayIso ? " today" : "") + (key < todayIso ? " past" : "") + (key === selected ? " selected" : ""));
      cell.append(el("span", "n", d));
      if (list.length) {
        const dots = el("span", "dots");
        [...new Set(list.map((c) => c.style.getPropertyValue("--vc")))].slice(0, 4).forEach((col) => { const i = el("i"); i.style.setProperty("--vc", col); dots.append(i); });
        cell.append(dots);
        cell.setAttribute("aria-label", `${d}.${m + 1}. ${gigs(list.length)}`);
        cell.addEventListener("click", () => { state.calDay = key === state.calDay ? null : key; render(); });
      } else cell.disabled = true;
      grid.append(cell);
    }
    box.append(head, grid);

    const shown = selected;
    if (shown) {
      const [main, sub] = dayLabel(shown);
      const h = el("h2", null, main); h.append(" ", el("span", null, sub));
      const g = el("div", "grid"); byDate.get(shown).forEach((c) => g.append(clone(c)));
      const wrap = el("section", "day-group"); wrap.append(h, g); dayBox.append(wrap);
    }
    return null;
  }

  /* ---- Add to calendar (.ics) ---- */
  const icsText = (v) => v.replace(/[\\;,]/g, "\\$&").replace(/\n/g, "\\n");
  // RFC 5545: a line is at most 75 octets (UTF-8 bytes), and a continuation line starts with one space.
  const utf8 = new TextEncoder();
  function icsFold(line) {
    const out = [];
    let cur = "", bytes = 0;
    for (const ch of line) {                       // iterates whole characters, never splitting one
      const n = utf8.encode(ch).length;
      if (bytes + n > (out.length ? 74 : 75)) { out.push(cur); cur = ""; bytes = 0; }
      cur += ch; bytes += n;
    }
    out.push(cur);
    return out.join("\r\n ");
  }
  // Floating times would shift on a phone in another time zone, so the event carries Helsinki's rules.
  const ICS_ZONE = ["BEGIN:VTIMEZONE", "TZID:Europe/Helsinki",
    "BEGIN:DAYLIGHT", "TZOFFSETFROM:+0200", "TZOFFSETTO:+0300", "TZNAME:EEST", "DTSTART:19700329T030000",
    "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU", "END:DAYLIGHT",
    "BEGIN:STANDARD", "TZOFFSETFROM:+0300", "TZOFFSETTO:+0200", "TZNAME:EET", "DTSTART:19701025T040000",
    "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU", "END:STANDARD", "END:VTIMEZONE"];
  const slug = (v) => v.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60) || "gig";
  function downloadIcs(c) {
    const d = c.dataset, day = d.date.replace(/-/g, "");
    const time = d.start || d.doors;
    const stamp = new Date().toISOString().replace(/[-:]|\.\d+/g, "");
    let when;
    if (time) {
      const [h, m] = time.split(":").map(Number);
      const end = new Date(2000, 0, 1, h + 2, m);   // gig lengths are not published: assume two hours
      const hhmm = (hh, mm) => `${String(hh).padStart(2, "0")}${String(mm).padStart(2, "0")}00`;
      const endDay = end.getDate() === 1 ? day : iso(addDays(parse(d.date), 1)).replace(/-/g, "");
      when = [`DTSTART;TZID=Europe/Helsinki:${day}T${hhmm(h, m)}`,
        `DTEND;TZID=Europe/Helsinki:${endDay}T${hhmm(end.getHours(), end.getMinutes())}`];
    } else {
      when = [`DTSTART;VALUE=DATE:${day}`, `DTEND;VALUE=DATE:${iso(addDays(parse(d.date), 1)).replace(/-/g, "")}`];
    }
    const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//livemusicTurku//EN", ...ICS_ZONE, "BEGIN:VEVENT",
      `UID:${day}-${encodeURIComponent(d.url)}@livemusicturku`, `DTSTAMP:${stamp}`, ...when,
      `SUMMARY:${icsText(d.title)}`, `LOCATION:${icsText(`${d.venue}, Turku`)}`, `URL:${d.url}`,
      `DESCRIPTION:${icsText(d.doors ? `${T.doors} ${d.doors}\n${d.url}` : d.url)}`, "END:VEVENT", "END:VCALENDAR"];
    const a = el("a");
    a.href = URL.createObjectURL(new Blob([lines.map(icsFold).join("\r\n") + "\r\n"], { type: "text/calendar" }));
    a.download = `${slug(d.title)}.ics`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);   // revoking at once can cancel the download in Safari
  }
  document.addEventListener("click", (e) => {
    const b = e.target.closest(".ics");
    if (b) downloadIcs(b.closest(".ev"));
  });

  /* ---- Orchestration ---- */
  function render() {
    for (const [name, node] of Object.entries(views)) node.hidden = name !== state.view;
    tabs.forEach((t) => t.setAttribute("aria-selected", String(t.dataset.view === state.view)));
    chips.forEach((c) => c.setAttribute("aria-pressed", String(c.dataset.venue === state.venue)));
    const msg = { week: renderWeek, upcoming: renderUpcoming, calendar: renderCalendar }[state.view]();
    empty.hidden = !msg; empty.textContent = msg || "";
    if (state.view === "upcoming" && msg) views.upcoming.hidden = true;
  }

  function setView(v, push) {
    state.view = v;
    if (push) history.replaceState(null, "", `#${v}`);
    render();
  }

  $(".tabs").hidden = false; $(".venues").hidden = false;
  tabs.forEach((t) => t.addEventListener("click", () => { setView(t.dataset.view, true); window.scrollTo({ top: Math.min(window.scrollY, $(".controls").offsetTop), behavior: "instant" }); }));
  chips.forEach((c) => c.addEventListener("click", () => { state.venue = c.dataset.venue; state.calDay = null; render(); }));
  window.addEventListener("hashchange", () => { const v = location.hash.slice(1); if (views[v]) setView(v); });

  const start = location.hash.slice(1);
  state.view = views[start] ? start : "week";
  render();
})();

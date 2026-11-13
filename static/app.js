(() => {
  const days = [...document.querySelectorAll(".day")];
  const chips = [...document.querySelectorAll(".chip")];
  const venueSelect = document.getElementById("venue");
  const empty = document.getElementById("empty");
  let range = "all";

  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

  // Friday-Sunday window: today..Sunday if already in it, otherwise the coming one.
  function weekendRange(now) {
    const dow = (now.getDay() + 6) % 7; // Mon=0 ... Sun=6
    const start = new Date(now);
    if (dow < 4) start.setDate(now.getDate() + (4 - dow));
    const end = new Date(now);
    end.setDate(now.getDate() + (6 - dow));
    if (dow < 4) end.setDate(start.getDate() + 2);
    return [iso(start), iso(end)];
  }

  function inRange(date) {
    const now = new Date();
    if (range === "today") return date === iso(now);
    if (range === "weekend") { const [a, b] = weekendRange(now); return date >= a && date <= b; }
    return true;
  }

  function apply() {
    const venue = venueSelect.value;
    let shown = 0;
    for (const day of days) {
      const ok = inRange(day.dataset.date);
      let any = false;
      for (const ev of day.querySelectorAll(".event")) {
        const visible = ok && (!venue || ev.dataset.venue === venue);
        ev.hidden = !visible;
        any = any || visible;
        shown += visible;
      }
      day.hidden = !any;
    }
    empty.hidden = shown > 0;
  }

  for (const chip of chips) {
    chip.addEventListener("click", () => {
      range = chip.dataset.range;
      chips.forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
      apply();
    });
  }
  venueSelect.addEventListener("change", apply);
})();

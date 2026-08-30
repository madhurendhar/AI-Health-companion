const TOKEN = "change-me-local-token";
let LOC = localStorage.getItem("flood_loc") || "Chennai";

document.getElementById("location").value = LOC;
document.getElementById("location").addEventListener("change", (e) => {
  LOC = e.target.value;
  localStorage.setItem("flood_loc", LOC);
  refresh();
});

function li(label, value, cls) {
  const c = cls ? ` class="${cls}"` : "";
  return `<li${c}><strong>${label}:</strong> ${value ?? "—"}</li>`;
}

async function get(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(path);
  return r.json();
}

async function refresh() {
  const [flood, rain, sys, data, mon, ev] = await Promise.all([
    get(`/flood/status?location=${LOC}`),
    get(`/rainfall?location=${LOC}`),
    get("/system/status"),
    get("/data-status"),
    get(`/monitor/status?location=${LOC}`),
    get(`/flood/events?location=${LOC}&limit=5`),
  ]);
  document.getElementById("demo-banner").classList.toggle(
    "hidden",
    !flood.demo_mode && !sys.demo_mode
  );

  const risk = flood.risk || flood.status;
  document.getElementById("flood").innerHTML = [
    li("location", flood.location),
    li("risk", risk, "st-" + risk),
    li("risk score", flood.risk_score),
    li("source", flood.source),
    li("data status", flood.data_status),
    li("stale", flood.stale),
    li("network", flood.network),
    li("inference", flood.inference),
    li("historical stats", flood.historical_stats_available),
    li("poll interval s", flood.poll_interval_s),
    li("reason", flood.reason),
    li("meaning", flood.meaning),
    li("event risk", flood.flood_event?.risk, "st-" + (flood.flood_event?.risk || "")),
    li("event probability", flood.flood_event?.probability),
    li("event reason", flood.flood_event?.reason),
  ].join("");

  const w = flood.rainfall || flood.windows || {};
  document.getElementById("rain").innerHTML = [
    li("1h mm", w["1h"] ?? w.rain_1h),
    li("3h mm", w["3h"] ?? w.rain_3h),
    li("6h mm", w["6h"] ?? w.rain_6h),
    li("12h mm", w["12h"] ?? w.rain_12h),
    li("24h mm", w["24h"] ?? w.rain_24h),
    li("72h mm", w["72h"] ?? w.rain_72h),
    li("provider", rain.source),
    li("updated", rain.updated_s),
    li("tail 6h", (rain.hourly_tail_mm || []).join(", ")),
  ].join("");

  const hc = flood.historical_comparison;
  document.getElementById("hist").innerHTML = hc
    ? (hc.anomalies || [])
        .filter((a) => a.level !== "normal")
        .map((a) => li(a.window, `${a.current_mm}mm vs p90=${a.historical_p90} (${a.level})`))
        .join("") || li("status", "within historical norms")
    : li("status", "demo mode — no historical compare");

  const tr = mon.trend || {};
  document.getElementById("trend").innerHTML = [
    li("escalating", tr.escalating),
    li("risk trend", tr.risk_trend),
    li("latest", tr.latest_status),
  ].join("");

  document.getElementById("sys").innerHTML = [
    li("subsystem", sys.subsystem),
    li("flood model", sys.flood_model?.name),
    li("method", sys.flood_model?.method),
    li("rainfall provider", sys.rainfall_provider),
    li("demo mode", sys.demo_mode),
    li("inference", data.inference_mode),
    li("historical stats", data.historical_stats?.Chennai),
  ].join("");

  const fe = flood.flood_event || {};
  const river = fe.river_level || ev.river_level;
  document.getElementById("events").innerHTML = [
    li("label source", ev.label_source),
    li("inventory events", ev.inventory?.event_records),
    li("flood days catalogued", ev.inventory?.flood_days),
    li("river level m", river?.level_m),
    li("river status", river?.status),
    li("recent IFI days", (ev.historical_event_days || []).map((e) => e.date).join(", ")),
  ].join("");
}

document.querySelectorAll("button[data-flood]").forEach((b) => {
  b.addEventListener("click", async () => {
    await fetch("/demo/scenario", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Api-Token": TOKEN },
      body: JSON.stringify({ flood_scenario: b.dataset.flood }),
    });
    refresh();
  });
});

refresh();
setInterval(refresh, 8000);

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
  const [flood, rain, sys, data] = await Promise.all([
    get(`/flood/status?location=${LOC}`),
    get(`/rainfall?location=${LOC}`),
    get("/system/status"),
    get("/data-status"),
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
    li("baseline used", flood.baseline_used),
    li("ML tree", flood.ml_tree_used),
    li("poll interval s", flood.poll_interval_s),
    li("reason", flood.reason),
    li("meaning", flood.meaning),
    li("supervised labels", flood.supervised_labels),
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

  document.getElementById("sys").innerHTML = [
    li("subsystem", sys.subsystem),
    li("health phase", sys.health_subsystem),
    li("flood model", `${sys.flood_model?.name} v${sys.flood_model?.version}`),
    li("model loaded", sys.flood_model?.loaded),
    li("validation", sys.flood_model?.validation),
    li("rainfall provider", sys.rainfall_provider),
    li("demo mode", sys.demo_mode),
  ].join("");

  document.getElementById("data").innerHTML = [
    li("NWDP locations", (data.nwdp_locations || []).join(", ")),
    li("Kanyakumari", data.kanyakumari_rainfall),
    li("flood labels", data.flood_event_labels),
    li("Chennai baseline", data.baseline_available?.Chennai),
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

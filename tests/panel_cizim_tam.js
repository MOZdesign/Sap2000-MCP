// Sahte AML sayfasıyla Çizim sekmesinin uçtan uca denemesi (GUI yok): köprüye sayfa gibi bağlanır, araç çağrılarını günlüğe yazar.
const fs = require("fs");
const { createRequire } = require("module");
const WebSocket = createRequire("C:/prefabrik-3d-viewer/tools/agent-bridge/package.json")("ws");
const { Oturum, SEKMELER } = require("C:/prefabrik-3d-viewer/panel/claude-oturum.js");
SEKMELER.cizim.mcp["aml-tekniker"].env.AML_BRIDGE_ORIGINS = "file://";
const soru = process.argv[2];
let metin = "";
const o = new Oturum("cizim", (e) => {
  if (e.tip === "metin") metin += e.metin; else if (e.tip !== "bitti") console.log(JSON.stringify(e));
  if (e.tip === "bitti" || e.tip === "hata") setTimeout(() => { console.log("\nYANIT:\n" + metin); o.durdur(); process.exit(0); }, 300);
});
const _i = o._isle.bind(o); o._isle = (m) => { if (m.type === "system") console.log("SYS:", JSON.stringify({sub: m.subtype, mcp: m.mcp_servers, tools: m.tools && m.tools.length, tl: m.tools}).slice(0, 900)); _i(m); };
o.hazirla = async (t0, ot) => {
  let jeton; for (let i = 0; i < 60 && !jeton; i++) { try { if (fs.statSync(SEKMELER.cizim.jetonDosyasi).mtimeMs >= t0 - 2000) jeton = fs.readFileSync(SEKMELER.cizim.jetonDosyasi, "utf8").trim(); } catch (e) {} await new Promise(r => setTimeout(r, 250)); }
  const ws = new WebSocket("ws://127.0.0.1:" + ot.port, { origin: "file://" });
  ws.on("open", () => ws.send(JSON.stringify({ type: "hello", token: jeton })));
  ws.on("message", (d) => { const m = JSON.parse(d); if (m.type === "ready") return; console.log("SAYFA ÇAĞRI:", m.tool, JSON.stringify(m.args));
    const r = m.tool === "proje_ozet" ? { dosya: "", adetler: { kolon: 0, kiris: 0, doseme: 0, asik: 0, temel: 0, bag: 0, yid: 0 }, akslar: { x: 0, y: 0, kot: 0 } } : { tamam: true };
    ws.send(JSON.stringify({ id: m.id, result: r })); });
  await new Promise(r => setTimeout(r, 1500));
};
o.gonder(soru).then((r) => console.log(r));
setTimeout(() => { console.log("zaman aşımı"); o.durdur(); process.exit(1); }, 150000);

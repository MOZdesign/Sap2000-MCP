const fs = require("fs");
const { Oturum, SEKMELER } = require("C:/prefabrik-3d-viewer/panel/claude-oturum.js");
const o = new Oturum("cizim", (e) => { if (e.tip !== "metin") console.log(JSON.stringify(e)); if (e.tip === "bitti" || e.tip === "hata") setTimeout(() => { o.durdur(); process.exit(0); }, 300); });
o.hazirla = async (t0) => { for (let i = 0; i < 40; i++) { try { if (fs.statSync(SEKMELER.cizim.jetonDosyasi).mtimeMs >= t0 - 2000) { console.log("jeton dosyası geldi"); return; } } catch (e) {} await new Promise((r) => setTimeout(r, 250)); } console.log("JETON YOK"); };
o.gonder("proje_ozet aracını çağır ve sonucu tek cümleyle söyle.").then(console.log);
setTimeout(() => { console.log("zaman aşımı"); o.durdur(); process.exit(1); }, 120000);

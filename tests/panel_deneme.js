// Panel oturum yöneticisini Electron olmadan dener (abonelikten kısa bir istek harcar).
const { Oturum, claudeBul } = require("C:/prefabrik-3d-viewer/panel/claude-oturum.js");
console.log("claude:", claudeBul());
const o = new Oturum("statik", (e) => { console.log(JSON.stringify(e)); if (e.tip === "bitti" || e.tip === "hata") { setTimeout(() => { o.durdur(); process.exit(0); }, 200); } });
console.log(o.gonder(process.argv[2] || "Açık SAP2000 modelinin bilgisini al."));
setTimeout(() => { console.log("zaman aşımı"); o.durdur(); process.exit(1); }, 120000);

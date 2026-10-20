// Regression: render the actual dashboard chart with supplied Huanuco data.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { createRequire } = require("node:module");
const root = path.resolve(__dirname, "..");
const appRequire = createRequire(path.join(root, "frontend/package.json"));
const React = appRequire("react");
const { renderToStaticMarkup } = appRequire("react-dom/server");
const charts = appRequire("recharts");
const ts = appRequire("typescript");
const source = fs.readFileSync(path.join(root, "frontend/components/dashboard.tsx"), "utf8");
const jsx = source.match(/<ComposedChart[\s\S]*?<\/ComposedChart>/)[0]
  .replace("<ComposedChart ", '<ComposedChart width={800} height={300} ');
const read = name => JSON.parse(fs.readFileSync(path.join(root, name), "utf8"));
const selected = r => r.PRODUCTO === "PAPA" && r.DEPARTAMENTO === "HUANUCO";
const historical = read("historial_departamento.json").filter(selected);
const year = r => Object.entries(r).find(([k,v]) => k.startsWith("A") && Number.isInteger(v))[1];
const prediction = read("predicciones_departamento.json").find(r => selected(r) && year(r) === 2027);
assert(historical.length > 5 && prediction);
const chart = historical.map(r => ({year: year(r), rendimiento: r.rendimiento_promedio, produccion: r.produccion_total}));
chart.at(-1).proyeccion = chart.at(-1).rendimiento;
chart.push({year: 2027, proyeccion: prediction.rendimiento_promedio, produccion: prediction.produccion_total});
for (const section of ["resumen", "evolucion", "produccion"]) {
  const context = {React, ...charts, section, chart, forecast:{yield_value:prediction.rendimiento_promedio}, number:n=>String(n), module:{exports:{}}};
  const compiled = ts.transpileModule(`module.exports = function Chart(){return (${jsx});}`, {compilerOptions:{jsx:ts.JsxEmit.React, module:ts.ModuleKind.CommonJS}}).outputText;
  vm.runInNewContext(compiled, context);
  const svg = renderToStaticMarkup(React.createElement(context.module.exports));
  if(section === "produccion") assert(svg.includes("recharts-bar-rectangle"), "Missing production bars");
  else {
    assert.equal((svg.match(/recharts-line-curve/g)||[]).length, 2, "Expected historical and forecast curves");
    if(section === "resumen") assert(svg.includes("recharts-area-area"), "Missing production area");
  }
  assert(svg.includes("2027"), "The projection year must remain visible");
  console.log(`${section}: Huanuco chart rendered successfully`);
}

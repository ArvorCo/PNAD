"""Escala de renda fixa, com ausência distinta de renda baixa."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_escala_renda_preserva_ausentes_extremos_e_direcao():
    subprocess.run(
        ["node", "-e", r"""
const fs = require('fs'), vm = require('vm'), assert = require('assert');
global.window = globalThis;
vm.runInThisContext(fs.readFileSync('docs/assets/politize_se_mapa/renda.js', 'utf8'));
const r = RendaMapa, rgb = c => [1, 3, 5].map(i => parseInt(c.slice(i, i+2), 16));
assert.equal(r.cor(null), r.cor(undefined));
assert.equal(r.cor(NaN), r.cor(null));
assert.notEqual(r.cor(0), r.cor(null));
assert.equal(r.cor(0), r.cor(2000));
assert.equal(r.cor(15000), r.cor(6500));
assert.notEqual(r.cor(2200), r.cor(3100));
assert.notEqual(r.cor(3100), r.cor(5000));
for (const [value, red] of [[2200, true], [6000, false]]) {
  const c = rgb(r.cor(value)); assert.equal(c[0] > c[2], red);
}
assert.equal(r.cor(0, 'renda_ate2'), r.cor(6500));
assert.equal(r.cor(100, 'renda_ate2'), r.cor(2000));
const antes = r.cor(3770);
// Não há domínio recalculado ao trocar município, zoom ou filtro.
for (const v of [2000, 14780, 3770]) r.cor(v);
assert.equal(r.cor(3770), antes);
"""],
        cwd=ROOT,
        check=True,
    )

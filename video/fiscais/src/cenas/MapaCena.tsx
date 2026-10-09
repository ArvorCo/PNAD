import { useMemo } from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Caixa, Chip, Entrada, Texto, Titulo } from "../componentes/Caixa";
import { Contador } from "../componentes/Contador";
import { Mapa } from "../componentes/Mapa";
import { decimal, inteiro, rampa } from "../componentes/util";
import { useFormato } from "../formato";
import { quadro, type Cena } from "../plano";
import { COR, MONO } from "../tema";
import type { Dados } from "../tipos";

/** Centro da caixa envolvente de um caminho SVG, para posicionar rótulos de UF. */
const centroDe = (d: string): [number, number] => {
  const numeros = d.match(/-?\d+(\.\d+)?/g)?.map(Number) ?? [];
  let x0 = Infinity;
  let x1 = -Infinity;
  let y0 = Infinity;
  let y1 = -Infinity;
  for (let i = 0; i + 1 < numeros.length; i += 2) {
    x0 = Math.min(x0, numeros[i]);
    x1 = Math.max(x1, numeros[i]);
    y0 = Math.min(y0, numeros[i + 1]);
    y1 = Math.max(y1, numeros[i + 1]);
  }
  return [(x0 + x1) / 2, (y0 + y1) / 2];
};

const NOMES_UF: Record<string, string> = { MA: "Maranhão", PA: "Pará", BA: "Bahia" };

/** Mapa nacional: onde o nível alta se concentra, os municípios e o achado contrário. */
export const MapaCena: React.FC<{ cena: Cena; dados: Dados }> = ({ cena, dados }) => {
  const frame = useCurrentFrame();
  const { vertical, margem, largura, altura } = useFormato();
  const p = cena.palavras;
  const centros = useMemo(
    () => Object.fromEntries(dados.mapa.ufs.map((u) => [u.uf, centroDe(u.d)])) as Record<string, [number, number]>,
    [dados.mapa.ufs],
  );
  const ufsTop = [...dados.por_uf].sort((a, b) => b.locais_alta - a.locais_alta).slice(0, 3);
  const qUf = ufsTop.map((u, i) => quadro(p, NOMES_UF[u.uf] ?? u.uf, 4 + i * 1.5));
  const qTaxa = quadro(p, "proporção", 9);
  const qMun = dados.municipios.map((m, i) => quadro(p, m.municipio.split(" ")[0], 14 + i * 1.6));
  const qAchado = quadro(p, "achado", 24);
  const qRural = quadro(p, "Três", 27);
  const qAldeia = quadro(p, "quinhentas", 30);
  const qUrna = quadro(p, "quatrocentas", 33);
  const qLado = quadro(p, "SETENTA", 41);
  const qProtege = quadro(p, "fiscal", 46);
  const paraTaxa = [...dados.por_uf].sort((a, b) => b.taxa_pct - a.taxa_pct)[0];
  const rotulos: Record<string, string> = {};
  ufsTop.forEach((u, i) => {
    if (frame >= qUf[i]) {
      rotulos[u.uf] = `${u.uf} ${u.locais_alta}`;
    }
  });
  const trocaPainel = rampa(frame, qAchado - 8, qAchado + 6);
  const mapaTamanho = vertical ? largura - 2 * margem - 60 : altura - 420;
  const explic = dados.resumo.explicacao_por_codigo;
  const n78 = dados.contrario.find((t) => t.includes("Flávio com 90%"))?.match(/(\d+) das/)?.[1];

  const painelRanking = (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, opacity: 1 - trocaPainel }}>
      <Entrada inicio={0} de="direita">
        <Titulo tamanho={vertical ? 40 : 44}>Onde o nível alta se concentra</Titulo>
      </Entrada>
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
        {ufsTop.map((u, i) => (
          <Entrada key={u.uf} inicio={qUf[i]} de="direita">
            <Caixa cor={COR.alta} style={{ padding: "14px 20px", minWidth: 150 }}>
              <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: 44, color: COR.alta }}>{u.locais_alta}</div>
              <Texto tamanho={18} cor={COR.suave}>locais em {NOMES_UF[u.uf] ?? u.uf}</Texto>
            </Caixa>
          </Entrada>
        ))}
      </div>
      <Entrada inicio={qTaxa} de="direita">
        <Caixa cor={COR.tealClaro} style={{ padding: "14px 20px" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
            <Contador valor={paraTaxa.taxa_pct} inicio={qTaxa} casas={1} sufixo="%" tamanho={44} cor={COR.tealClaro} />
            <Texto tamanho={20} cor={COR.suave}>das seções do {paraTaxa.uf} sinalizadas, a maior taxa do país</Texto>
          </div>
        </Caixa>
      </Entrada>
      <Entrada inicio={qMun[0]} de="direita">
        <Chip cor={COR.ouro} tamanho={16}>municípios que mais pedem fiscal</Chip>
      </Entrada>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {dados.municipios.map((m, i) => (
          <Entrada key={m.municipio} inicio={qMun[i]} de="direita">
            <div style={{ display: "grid", gridTemplateColumns: "44px 1fr auto", gap: 12, alignItems: "center", fontFamily: MONO, fontSize: vertical ? 20 : 22, color: COR.tinta, borderBottom: `1px solid ${COR.linha}`, padding: "6px 0" }}>
              <span style={{ color: COR.ouro, fontWeight: 700 }}>{String(i + 1).padStart(2, "0")}</span>
              <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {m.municipio} <span style={{ color: COR.suave }}>({m.uf})</span>
              </span>
              <span style={{ color: COR.suave }}>
                <span style={{ color: COR.alta }}>{m.alta} alta</span> · {inteiro(m.secoes)} seções
              </span>
            </div>
          </Entrada>
        ))}
      </div>
    </div>
  );

  const painelContrario = (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, opacity: trocaPainel }}>
      <Entrada inicio={qAchado} de="direita">
        <Chip cor={COR.outros} solido tamanho={18}>o achado que anda junto com a lista</Chip>
      </Entrada>
      {[
        [qRural, explic.zona_rural, "seções em zona rural", COR.outros],
        [qAldeia, explic.aldeia, "em aldeia indígena", COR.outros],
        [qUrna, explic.urna_trocada, "tiveram urna trocada", COR.outros],
      ].map(([q, v, rotulo, cor]) => (
        <Entrada key={String(rotulo)} inicio={Number(q)} de="direita">
          <div style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
            <Contador valor={Number(v)} inicio={Number(q)} tamanho={vertical ? 52 : 60} cor={String(cor)} />
            <Texto tamanho={vertical ? 22 : 26}>{String(rotulo)}</Texto>
          </div>
        </Entrada>
      ))}
      <Entrada inicio={qLado} de="direita">
        <Caixa cor={COR.flavio}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
            <Contador valor={Number(n78 ?? 0)} inicio={qLado} tamanho={vertical ? 56 : 64} cor={COR.flavio} />
            <Texto tamanho={vertical ? 22 : 24}>seções do critério 1 são de Flávio com 90% ou mais</Texto>
          </div>
        </Caixa>
      </Entrada>
      <Entrada inicio={qProtege} de="baixo">
        <Titulo tamanho={vertical ? 34 : 38} cor={COR.tealClaro}>O fiscal que vigia uma seção protege os dois votos.</Titulo>
      </Entrada>
    </div>
  );

  return (
    <AbsoluteFill style={{ padding: `${vertical ? 170 : 150}px ${margem}px`, flexDirection: vertical ? "column" : "row", gap: 30, alignItems: vertical ? "center" : "flex-start" }}>
      <div style={{ position: "relative", width: mapaTamanho, height: vertical ? mapaTamanho * 0.86 : mapaTamanho, flex: "none", overflow: "visible" }}>
        <div style={{ position: "absolute", top: vertical ? -mapaTamanho * 0.08 : 0, left: 0 }}>
          <Mapa mapa={dados.mapa} tamanho={mapaTamanho} inicio={0} inicioPontos={10} rotulos={rotulos} centros={centros} />
        </div>
        <div style={{ position: "absolute", left: vertical ? undefined : 10, right: vertical ? 0 : undefined, top: vertical ? 0 : undefined, bottom: vertical ? undefined : 0, display: "flex", flexDirection: vertical ? "column" : "row", gap: vertical ? 4 : 18, fontFamily: MONO, fontSize: 16, color: COR.suave, letterSpacing: 1 }}>
          <span><span style={{ color: COR.alta }}>●</span> alta</span>
          <span><span style={{ color: COR.media }}>●</span> média</span>
          <span><span style={{ color: COR.baixa }}>·</span> baixa (amostra)</span>
          <span>{decimal(dados.resumo.pct_sinalizadas)}% do eleitorado</span>
        </div>
      </div>
      <div style={{ position: "relative", flex: 1, minWidth: 0, alignSelf: "stretch" }}>
        <div style={{ position: "absolute", inset: 0 }}>{painelRanking}</div>
        {frame >= qAchado - 8 ? <div style={{ position: "absolute", inset: 0 }}>{painelContrario}</div> : null}
      </div>
    </AbsoluteFill>
  );
};

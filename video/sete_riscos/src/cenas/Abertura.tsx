// Cena 0.1: uma seção real de Barcarena (PA) com Lula acima de noventa por cento, a contagem do
// país nos dois sentidos, a frase da casa e "só quem está na sala vê".
import { useCurrentFrame } from "remotion";
import { CartaoSecao } from "../componentes/CartaoSecao";
import { Contador } from "../componentes/Contador";
import { Area, Etiqueta, Surge } from "../componentes/Quadro";
import { RiscoFundo } from "../componentes/Risco";
import { ritmo } from "../componentes/ritmo";
import { FRASES_CASA } from "../componentes/textos";
import { decimal, rampa } from "../componentes/util";
import { useFormato } from "../formato";
import { COR, FONTE, MONO } from "../tema";
import type { CenaProps } from "./registro";

/** Corte de `secoes_lula_90` e `secoes_flavio_90` (CONTRATO.md, seção 3): noventa por cento. */
const LIMIAR = 90;

const Contagem: React.FC<{ valor: number; q: number; fim: number; cor: string; rotulo: string }> = ({ valor, q, fim, cor, rotulo }) => {
  const { t, vertical } = useFormato();
  return (
    <Surge inicio={q}>
      <div style={{ display: "flex", flexDirection: "column", gap: t(6), padding: `${t(14)}px ${t(22)}px`, borderLeft: `6px solid ${cor}`, background: "rgba(6,11,26,0.6)", borderRadius: 14 }}>
        <Contador valor={valor} inicio={q} duracao={Math.max(24, fim - q)} tamanho={t(vertical ? 110 : 100)} cor={cor} />
        <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 32 : 28), lineHeight: 1.15, color: COR.tinta }}>{rotulo}</div>
      </div>
    </Surge>
  );
};

export const Abertura: React.FC<CenaProps> = ({ cena, dados, g: gBruto }) => {
  const frame = useCurrentFrame();
  const { vertical, t } = useFormato();
  const g = ritmo(cena, gBruto);
  const e = dados.exemplos.frente_1;
  const lf = dados.lula_frente;
  // A seção esmaece um pouco quando o país entra, para o olho ir às contagens.
  const recua = 1 - 0.35 * rampa(frame, g.pais, g.pais + 20);

  const secao = (
    <div style={{ display: "flex", flexDirection: "column", gap: t(16), opacity: recua }}>
      <Surge inicio={g.barcarena} de="esquerda">
        <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 30 : 26), letterSpacing: 4, color: COR.tealClaro }}>
          {e.municipio.toUpperCase()} · {e.uf}
        </div>
      </Surge>
      <div style={{ minHeight: t(vertical ? 360 : 360) }}>
        <CartaoSecao exemplo={e} inicio={g.secao} />
      </div>
      <div style={{ display: "flex", gap: t(12), flexWrap: "wrap" }}>
        <Surge inicio={g.rural}>
          <Etiqueta cor={COR.tealClaro} tamanho={24}>
            seção rural
          </Etiqueta>
        </Surge>
        <Surge inicio={g.comparecimento}>
          <Etiqueta cor={COR.ouro} tamanho={24}>
            comparecimento {decimal(e.comparecimento_pct, 2)}%
          </Etiqueta>
        </Surge>
      </div>
    </div>
  );

  const pais = (
    <div style={{ display: "flex", flexDirection: "column", gap: t(vertical ? 18 : 16) }}>
      <Surge inicio={g.pais}>
        <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 30 : 26), letterSpacing: 4, color: COR.suave }}>NO PAÍS</div>
      </Surge>
      <div style={{ display: "flex", flexDirection: vertical ? "row" : "column", gap: t(16) }}>
        <div style={{ flex: 1 }}>
          <Contagem valor={lf.secoes_lula_90} q={g.lula90} fim={g.fimLula} cor={COR.lula} rotulo={`seções com Lula acima de ${LIMIAR}%`} />
        </div>
        <div style={{ flex: 1 }}>
          <Contagem valor={lf.secoes_flavio_90} q={g.flavio} fim={g.fimFlavio} cor={COR.flavio} rotulo={`seções com Flávio acima de ${LIMIAR}%`} />
        </div>
      </div>
      <Surge inicio={g.atipicidade}>
        <div style={{ display: "flex", gap: t(16), alignItems: "stretch" }}>
          <div style={{ width: t(8), borderRadius: t(4), background: COR.ouro, flex: "none" }} />
          <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 44 : 38), lineHeight: 1.12, color: COR.tinta, textWrap: "balance" }}>{FRASES_CASA[0]}</div>
        </div>
      </Surge>
    </div>
  );

  const fecho = (
    <Surge inicio={g.ninguem}>
      <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", alignItems: vertical ? "flex-start" : "baseline", gap: t(vertical ? 6 : 22) }}>
        <span style={{ fontFamily: FONTE, fontWeight: 500, fontSize: t(vertical ? 36 : 32), color: COR.suave }}>Ninguém sabe o que aconteceu lá dentro.</span>
        <span style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 66 : 58), letterSpacing: -1, color: COR.tinta, opacity: rampa(frame, g.so, g.so + 10) }}>
          Só quem está na sala <span style={{ color: COR.tealClaro, textShadow: `0 0 ${30 * rampa(frame, g.ve, g.ve + 12)}px ${COR.tealClaro}` }}>VÊ</span>.
        </span>
      </div>
    </Surge>
  );

  return (
    <>
      <RiscoFundo ids={["rua_escola_amanhecer_still", "rio_amazonia_escola"]} opacidade={0.55} veu={0.85} />
      <Area style={{ justifyContent: "center", gap: t(vertical ? 34 : 28) }}>
        <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: t(vertical ? 30 : 44), alignItems: vertical ? "stretch" : "flex-start" }}>
          <div style={{ flex: vertical ? "none" : "1.15 1 0", minWidth: 0 }}>{secao}</div>
          <div style={{ flex: vertical ? "none" : "1 1 0", minWidth: 0 }}>{pais}</div>
        </div>
        {fecho}
      </Area>
    </>
  );
};

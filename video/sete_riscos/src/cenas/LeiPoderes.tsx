// Cena 1.1: os seis poderes que a lei dá ao fiscal credenciado, cada um na palavra dita, com o
// fiscal na cadeira ao lado e o fecho "nada disso depende de favor".
import { Clipe } from "../componentes/Clipe";
import { temClipe } from "../componentes/ClipeSeHouver";
import { Area, Surge } from "../componentes/Quadro";
import { RiscoFundo, RiscoLei } from "../componentes/Risco";
import { ritmo } from "../componentes/ritmo";
import { useFormato } from "../formato";
import { COR, FONTE, MONO } from "../tema";
import type { IdLeiFiscal } from "../tipos";
import type { CenaProps } from "./registro";

/** Gatilho de cada item de `lei_fiscal`, na ordem da narração. */
const GATILHO: Record<IdLeiFiscal, string> = {
  fiscalizar: "fiscalizar",
  dois: "dois",
  credencial: "credencial",
  impugnar: "impugnar",
  copia: "copia",
  ate_a_junta: "junta",
};

export const LeiPoderes: React.FC<CenaProps> = ({ cena, dados, g: gBruto }) => {
  const { vertical, t } = useFormato();
  const g = ritmo(cena, gBruto);
  const itens = dados.lei_fiscal.map((item) => ({ texto: item.texto, referencia: item.referencia, q: g[GATILHO[item.id]] ?? g.fiscalizar }));
  const temFiscal = temClipe("fiscal_cadeira", vertical);

  const quadroClipe = temFiscal ? (
    <Surge inicio={g.inicio} de="zoom" style={{ height: vertical ? t(330) : t(440) }}>
      <div style={{ position: "relative", height: "100%", borderRadius: 20, overflow: "hidden", border: `2px solid ${COR.ouro}`, boxShadow: "0 30px 80px rgba(0,0,0,0.5)" }}>
        <Clipe id="fiscal_cadeira" fim="repetir" veu={0.35} />
        <div style={{ position: "absolute", left: t(18), bottom: t(16), fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 28 : 24), letterSpacing: 3, color: COR.tinta, background: "rgba(6,11,26,0.78)", padding: `${t(6)}px ${t(14)}px`, borderRadius: 10 }}>
          FISCAL COM CREDENCIAL
        </div>
      </div>
    </Surge>
  ) : null;

  const fecho = (
    <Surge inicio={g.tudo}>
      <div style={{ display: "flex", gap: t(16), alignItems: "stretch" }}>
        <div style={{ width: t(8), borderRadius: t(4), background: COR.ouro, flex: "none" }} />
        <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 50 : 44), lineHeight: 1.1, color: COR.tinta, textWrap: "balance" }}>
          Tudo isso está na lei. Nada disso depende de <span style={{ color: COR.ouro }}>favor</span>.
        </div>
      </div>
    </Surge>
  );

  const cartao = <RiscoLei titulo="O QUE A LEI GARANTE AO FISCAL" itens={itens} inicio={g.inicio} tamanho={vertical ? 27 : 28} />;

  return (
    <>
      {vertical ? <RiscoFundo ids={["fiscal_cadeira"]} opacidade={0.25} /> : null}
      <Area style={{ justifyContent: "center" }}>
        {vertical ? (
          <div style={{ display: "flex", flexDirection: "column", gap: t(24) }}>
            {quadroClipe}
            {cartao}
            {fecho}
          </div>
        ) : (
          <div style={{ display: "flex", gap: t(40), alignItems: "center" }}>
            <div style={{ flex: "1.3 1 0", minWidth: 0 }}>{cartao}</div>
            <div style={{ flex: "1 1 0", minWidth: 0, display: "flex", flexDirection: "column", gap: t(30) }}>
              {quadroClipe}
              {fecho}
            </div>
          </div>
        )}
      </Area>
    </>
  );
};

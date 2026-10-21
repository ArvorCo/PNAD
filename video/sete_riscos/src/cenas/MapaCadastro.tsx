import { Chip, Texto, Titulo } from "../componentes/Caixa";
import { IconeCheck, IconeFiscal, IconeLei } from "../componentes/Icones";
import { MidiaAusente } from "../componentes/MidiaAusente";
import { BarraUrl, Navegador } from "../componentes/Navegador";
import { Area, Etiqueta, Surge, useArea } from "../componentes/Quadro";
import { Still } from "../componentes/Still";
import { CAPTURAS } from "../dados";
import { useFormato } from "../formato";
import { COR, MONO } from "../tema";
import type { CenaProps } from "./registro";

/** Still da página de cadastro: o primeiro still registrado, ou o arquivo sem nome de still. */
const CADASTRO = "cap_fiscaisdopl";
const capturaCadastro = CAPTURAS.fiscaisdopl;
const stillCadastro = capturaCadastro ? Object.keys(capturaCadastro.stills)[0] : undefined;

/** "2026-10-24" → "24/10". */
const diaMes = (iso: string): string => `${iso.slice(8, 10)}/${iso.slice(5, 7)}`;

type Requisito = { texto: string; q: number };

/**
 * Como ser fiscal: o site de cadastro do partido com o prazo do próprio site, os requisitos e a
 * credencial expedida pelo partido, com o artigo da lei.
 */
export const MapaCadastro: React.FC<CenaProps> = ({ g, dados }) => {
  const { vertical, t } = useFormato();
  const a = useArea();
  const credencial = dados.lei_fiscal.find((l) => l.id === "credencial");
  const requisitos: Requisito[] = [
    { texto: "mais de 18 anos", q: g.dezoito },
    { texto: "não ser mesário", q: g.mesario },
    { texto: "não ser candidato", q: g.candidato },
  ];
  const larguraNav = vertical ? a.largura : Math.min(a.largura * 0.52, ((a.altura - t(46)) * 16) / 9);
  const pagina = (
    <Surge inicio={g.fiscais - 6} de="esquerda">
      <Navegador url={dados.cadastro.site} largura={larguraNav} proporcao={vertical ? 16 / 10 : 16 / 9} cor={COR.ouro}>
        {capturaCadastro ? (
          // No 9:16 o still é vertical: mostra o topo da página (título e prazo), não o meio.
          <div style={{ position: "absolute", left: 0, top: 0, width: "100%", height: vertical ? (larguraNav * 16) / 9 : "100%" }}>
            <Still id={CADASTRO} nome={stillCadastro} de={1} ate={1.04} />
          </div>
        ) : (
          <MidiaAusente motivo={`${CADASTRO}: captura ainda não registrada em capturas.json`} />
        )}
      </Navegador>
    </Surge>
  );

  const tam = vertical ? 36 : 28;
  const coluna = (
    <div style={{ display: "flex", flexDirection: "column", gap: t(vertical ? 22 : 18), minWidth: 0 }}>
      <Surge inicio={g.vinte} de="baixo">
        <div style={{ display: "flex", flexDirection: "column", gap: t(8) }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: t(14), flexWrap: "wrap" }}>
            <Titulo tamanho={vertical ? 72 : 50}>
              cadastro até <span style={{ color: COR.ouro }}>{diaMes(dados.cadastro.prazo)}</span>
            </Titulo>
          </div>
          <Surge inicio={g.prazo}>
            <Etiqueta cor={COR.ouro} tamanho={vertical ? 24 : 22}>
              prazo do próprio site, não da Justiça Eleitoral
            </Etiqueta>
          </Surge>
        </div>
      </Surge>
      <div style={{ display: "flex", flexDirection: vertical ? "row" : "column", flexWrap: "wrap", gap: t(vertical ? 18 : 10) }}>
        {requisitos.map((r) => (
          <Surge key={r.texto} inicio={r.q} de="esquerda">
            <div style={{ display: "flex", alignItems: "center", gap: t(12) }}>
              <IconeCheck tamanho={t(tam + 12)} cor={COR.outros} />
              <Texto tamanho={tam} style={{ fontWeight: 700 }}>
                {r.texto}
              </Texto>
            </div>
          </Surge>
        ))}
      </div>
      <Surge inicio={g.credencial} de="baixo">
        <div
          style={{
            display: "flex",
            gap: t(18),
            alignItems: "center",
            background: "rgba(12,26,58,0.88)",
            border: `1px solid ${COR.linha}`,
            borderTop: `4px solid ${COR.ouro}`,
            borderRadius: 16,
            padding: `${t(16)}px ${t(22)}px`,
          }}
        >
          <IconeLei tamanho={t(vertical ? 64 : 54)} cor={COR.ouro} />
          <div style={{ display: "flex", flexDirection: "column", gap: t(4), minWidth: 0 }}>
            <Texto tamanho={vertical ? 36 : 30} style={{ fontWeight: 700 }}>
              Credencial expedida pelo partido
            </Texto>
            <span style={{ fontFamily: MONO, fontSize: t(vertical ? 28 : 22), color: COR.ouro }}>{credencial?.referencia ?? "Lei 9.504/1997, art. 65, § 2º"}</span>
          </div>
        </div>
      </Surge>
      <Surge inicio={g.cadastrese} de="zoom">
        <div style={{ display: "flex", alignItems: "center", gap: t(14) }}>
          <IconeFiscal tamanho={t(vertical ? 64 : 54)} cor={COR.ouro} />
          <Titulo tamanho={vertical ? 52 : 38} cor={COR.ouro}>
            Cadastre-se e peça a credencial.
          </Titulo>
        </div>
      </Surge>
    </div>
  );

  const barra = (
    <div style={{ display: "flex", alignItems: "center", gap: t(16), flexWrap: "wrap" }}>
      <Chip cor={COR.ouro} solido tamanho={vertical ? 26 : 22}>
        seja fiscal
      </Chip>
      <BarraUrl url={dados.cadastro.site} inicio={g.fiscais - 8} cor={COR.ouro} tamanho={vertical ? 44 : 38} />
    </div>
  );

  if (vertical) {
    return (
      <Area style={{ gap: t(26) }}>
        {barra}
        {pagina}
        {coluna}
      </Area>
    );
  }
  return (
    <Area style={{ gap: t(26) }}>
      {barra}
      <div style={{ display: "flex", gap: t(44), alignItems: "flex-start", flex: 1, minHeight: 0 }}>
        {pagina}
        <div style={{ flex: 1, minWidth: 0 }}>{coluna}</div>
      </div>
    </Area>
  );
};

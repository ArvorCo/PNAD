# Mídia do vídeo "Sete riscos, um fiscal"

Clipes de 8 s e stills que ilustram as cenas (contrato, seção 4). Tudo sai de
`scripts/video-sete-riscos-midia.py`, que chama o `openclaw` local e normaliza com ffmpeg; quando o
`openclaw` recusa, `--mflux` gera o still local (FLUX2 Klein 9B) e o vídeo vira Ken Burns.

| Arquivo | O que guarda |
|---|---|
| `manifesto.json` | Itens (id, tipo, modelo preferido, prompt, negativo, segundos, formatos, som, cenas), estilo comum, enquadramento por formato e a ordem de provedores. É a fonte; edite aqui. |
| `cache.json` | Estado por `<id>_<fmt>`: chave, origem (`openclaw` ou `manual`), estado (`pronto` ou `pendente`), modelo e provedor que geraram, erro resumido quando pendente. |
| `sondagem.json` | Última sondagem dos provedores, com o erro completo de cada um (sem segredos). Vale por 6 horas. |
| `entrada/` | Onde cai o arquivo feito à mão: `entrada/<id>_<fmt>.<ext>`. |
| `brutos/` | Saída crua dos provedores, para renormalizar sem pagar de novo. Não versionar. |
| `../public/midia/<id>_<fmt>.mp4\|png` | Arquivo final: 1920×1080 ou 1080×1920, 30 fps, h264 crf 18, yuv420p, sem áudio. |
| `../src/dados/midia.json` | `{ "<id>": { "tipo", "formatos", "segundos" } }`, só com o que existe em disco. `recorte_9x16: true` quando o retrato saiu do 16x9. Imagem tem `segundos` 0. |

## Prompt e cache

Prompt enviado = prompt do item + enquadramento do formato + estilo (o do item, se houver,
senão o comum) + `Avoid:` + negativo. A chave de cache é o sha256 de
`[prompt enviado, negativo, segundos, modelo do manifesto, formato]`, 12 caracteres. Mudou o
prompt, o arquivo é refeito na próxima execução; o arquivo antigo fica até o novo chegar.

## Rodar

```bash
python3 scripts/video-sete-riscos-midia.py --sondar          # um clipe de 4 s e uma imagem por provedor
python3 scripts/video-sete-riscos-midia.py                   # stills, depois vídeos 16x9, depois 9x16
python3 scripts/video-sete-riscos-midia.py --imagens         # só stills
python3 scripts/video-sete-riscos-midia.py --videos --formato 16x9
python3 scripts/video-sete-riscos-midia.py --so santinhos_calcada,viela_noite --forcar
python3 scripts/video-sete-riscos-midia.py --faltando        # o que falta, com o prompt pronto para colar
python3 scripts/video-sete-riscos-midia.py --absorver        # normaliza o que está em entrada/
python3 scripts/video-sete-riscos-midia.py --recortar        # 9x16 pelo centro do 16x9, onde faltar
```

No máximo duas gerações simultâneas. Provedor que falha por cota, crédito, autenticação ou
modelo indisponível sai da execução inteira; recusa por política só pula o item naquele
provedor. Provedor reprovado na sondagem das últimas 6 horas nem é tentado: depois de
resolver cota ou crédito, rode `--sondar` de novo antes de gerar.

## Arquivo feito à mão

1. `--faltando` lista cada `<id>_<fmt>` pendente, o nome de destino e o prompt completo.
2. Gere em Gemini web (Veo 3.1 para vídeo, Nano Banana Pro para imagem), CapCut (Seedance)
   ou Grok Imagine (bom para gerar o still e animar com o mesmo prompt). Vídeo de 8 s, sem
   áudio; imagem em 2K ou mais. Qualquer proporção serve: o normalizador escala cobrindo o
   quadro e recorta ao centro, então mantenha o assunto no meio.
3. Salve como `entrada/<id>_<fmt>.<ext>` (vídeo: mp4, mov, webm, mkv, m4v; imagem: png, jpg,
   jpeg, webp). Exemplo: `entrada/van_eleitores_16x9.mp4`.
4. Rode `--absorver`. Se só o 16x9 de um item chegou, o 9x16 sai recortado ao centro e
   `midia.json` marca `recorte_9x16`. Um 9x16 próprio que chegue depois substitui o recorte.

Absorver de novo o mesmo arquivo não refaz nada (o cache guarda o sha256 da entrada).

## Reaproveitado da masterclass

Treze itens vêm de `video/masterclass` (hard link em `public/midia`, manifesto e cache copiados
com `origem: manual`, só o campo `cenas` mudou): `fila_secao`, `urna_mesa_lacre`,
`boletim_impressora`, `maos_boletim_porta`, `fiscal_cadeira`, `escola_bangu_aerea`,
`rio_amazonia_escola`, `qr_celular`, `atas_mesa_lampada`, `teclado_urna_macro`, `secao_vazia`,
`boletim_porta` e `mapa_fundo_textura`. O `bruto` deles aponta para a entrada da masterclass.

## Plano B local (`--mflux`)

```bash
python3 scripts/video-sete-riscos-midia.py --mflux                      # tudo o que falta
python3 scripts/video-sete-riscos-midia.py --mflux --so viela_noite --semente 7 --forcar
```

Still 2048×1152 ou 1152×2048 por formato (duas gerações, sem recorte), FLUX2 Klein 9B, 4
passos, quantização 8, binário `~/anaconda3/envs/diffusionkit/bin/mflux-generate-flux2`, cerca
de 100 s por imagem. Prompt = prompt do item + enquadramento + `estilo_mflux`, sem a lista de
proibições (o FLUX desenha o que é negado). Vídeo = Ken Burns do still: `zoompan` de 1,0 a 1,08
ao centro, 240 quadros a 30 fps, com o still ampliado quatro vezes antes para o movimento não
tremer. O cache guarda `origem: mflux`, prompt, semente e o bruto em `brutos/`. Toda imagem é
olhada antes de aceitar: texto legível, rosto nítido, bandeira ou artefato grosseiro pedem outra
semente. Um clipe de verdade (CapCut, Grok) que chegue em `entrada/` substitui o Ken Burns pelo
`--absorver`.

## Situação em 21/10/2026

A sondagem reprovou de novo os seis provedores do `openclaw` (`sondagem.json`): Sora 2 HTTP
404, gpt-image-2 HTTP 400 (rota Codex com `gpt-5.5`), Veo 3.1 e Gemini Image HTTP 429 (cota),
OpenRouter HTTP 402 (sem créditos). Os dez itens novos (oito vídeos, dois stills, nos dois
formatos) saíram pelo `--mflux`, 46 de 46 arquivos em disco e nada em `--faltando`.
Revisão visual reprovou e refez: placa com letras na rua da escola e na fachada do
entardecer, papel impresso com pseudotexto na impressora (prompts reescritos pedindo superfície
lisa e papel em branco), emblema de montadora na van 16x9 (semente 9090). O 9x16 do caderno saiu
com caligrafia quase legível duas vezes e virou recorte central do 16x9 aprovado
(`recorte_de: 16x9`). Sete reaproveitados da masterclass têm 5,03 s, não 8 s. `entrada/` desta pasta ainda não tem regra de LFS no
`.gitattributes` da raiz (só a da masterclass tem).

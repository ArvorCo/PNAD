# Genial/Quaest nacional — anexo territorial de junho de 2026

`Quaest_Bairros_062026.pdf` foi recuperado do registro público PesqEle
`BR-07661/2026` em 16 de julho de 2026. O arquivo foi criado em 10 de junho às
23:04:27 e assinado às 23:04:53 (UTC−3), tem 17 páginas e SHA-256
`f135a6d704438850571fbff0faac0cfa2704625af8412fff690b9645961277e8`.

O anexo contém 334 setores, 120 municípios e 2.004 entrevistas, sempre seis por
setor. `quaest_bairros_0626.csv` é a extração reprodutível usada na comparação
com julho. Os demais documentos de junho permanecem como fontes locais da
auditoria [`docs/quaest_100626.html`](../../../../docs/quaest_100626.html).

Reprodução:

```bash
python3 -m pip install -e '.[audit]'
python3 scripts/quaest-territory-audit.py
```

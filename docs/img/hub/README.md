# Fundo do social card da home

`brasil_fundo.jpg` é uma imagem gerada localmente com FLUX 2 Klein 9B (mflux, Apple Silicon),
sem direitos de terceiros. Serve só de fundo ao card `hub` de `scripts/social-cards.py`.
Não é fotografia de lugar real; não usar como ilustração documental.

Prompt (inglês, como enviado ao modelo):

> Cinematic aerial photograph of a dense Brazilian metropolis at dusk from high altitude:
> endless grid of rooftops, hillside favela and glass towers side by side, winding highways
> with light trails, low warm sun breaking through dark storm clouds, deep blue and amber
> tones, moody documentary realism, high detail, no text, no logos, no people.

Parâmetros: 1360×768, 4 passos, quantização 8, semente 20261028.
Para regerar o card: `python3 scripts/social-cards.py --only hub`.

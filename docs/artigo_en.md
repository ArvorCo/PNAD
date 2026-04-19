# the auditable brazil: a portrait in fifteen photographs

> An essay written from the microdata of the IBGE's PNAD Contínua annual survey, visit 5, based on the 2026-03 edition of the public package processed in this repository. Unless otherwise noted, every statistic cited here comes from the file `base_labeled_npv.csv` produced by `brasil pipeline-run` and cross-checked in `brasil.sqlite`. The headline figures, expressed in equivalents of the Brazilian minimum wage (SM), are the hard core of this text; the reading around them is my own.

---

# part 1 — a country split in half

## opening

There is a country in which a man, born in Águas Claras, has a statistical chance of growing up in a household whose income amounts to 5.53 minimum wages; the same man, born instead in Bacabal, grows up in a household that barely clears 2.05. Both speak Portuguese. Both receive the same Bolsa Família (Brazil's conditional cash transfer programme) when income collapses. Both sing the national anthem with a hand pressed to the chest and the same civic innocence. And yet, between one and the other, the equivalent of two and a half Brazils slips through. The child of the cerrado and the child of the sertão live under one Constitution; they do not live under one economy.

The hurried reader will say that this is an old story. The reader is mistaken. What the microdata of the PNAD Contínua annual, visit 5, now allow us to do, for the first time on an open and reproducible scale, is to see inequality in fine resolution, state by state, minimum-wage band by minimum-wage band, colour by colour, schooling by schooling, and to see who pays for what and who receives what. The 200 bootstrap replicate weights that the IBGE publishes, and which this repository loads by default, make sampling-error calculation trivial. Put another way: Brazil has never been more auditable, and perhaps for that very reason has become so uncomfortable.

## the figure they would rather not see

The annual Gini coefficient of per-capita household income, counting every habitual earning, closes at 0.520 in the 2026-03 edition of the survey. The IBGE's official 2024 reading for per-capita income, as we shall see, is slightly lower, at 0.506, and the Institute is happy to celebrate it as [the lowest in the series that began in 2012](https://agenciadenoticias.ibge.gov.br/agencia-noticias/2012-agencia-de-noticias/noticias/43302-rendimento-per-capita-e-recorde-e-desigualdades-caem-ao-menor-nivel-desde-2012) (in Portuguese). The methodological divergence is well understood: the Institute's concept of household income, and its inclusion of social benefits, pushes the coefficient downwards. The reading used in this essay, which weights habitual earnings from every job using expansion weights and replicate weights for the confidence interval, lands on 0.520. Both tell the same bleak story, only in different registers.

For comparison: Portugal's Gini sits around 0.33; Germany's, 0.30; that of the United States, around 0.40. There is no developed country with a Gini above 0.45. Brazil is at 0.52. What is celebrated as a historic achievement is the passage from absurd inequality to inequality that is merely abominable.

Mean per-capita household income, converted into multiples of the reference minimum wage, is 3.62 SM. The median is brutally lower. Concentration is so skeletal that 40.6 percent of the population lives in households with per-capita income of up to two minimum wages, while only 6.5 percent reach the band of ten minimum wages or more. If the reader is reading this on a decent screen, on a reasonable device, in a ventilated room, it is statistically likely that she belongs to the upper minority of that curve, and it is good that she acknowledge, without sentimentality, the sociological anomaly on which she floats.

## the method

This essay works with the IBGE's PNAD Contínua annual survey, visit 5, which is the densest annual self-portrait the Brazilian state draws of itself. It covers roughly 211,370 households and 538,000 persons, and includes, among other variables, habitual and effective income, family structure, schooling, colour or race, formality of employment, metropolitan location, and the weights required for population inference. It is not a census, but the sampling design is robust enough for state-level inference, and the 200 replicate weights allow uncertainty estimates, something seldom seen in Brazilian public debate.

The income bands used here follow the tradition of the IBGE and DIEESE: 0 to 2 minimum wages, 2 to 5, 5 to 10, 10 or more. The deflator is the monthly IPCA up to the survey's reference month; the reference minimum wage is that of the target month. Every comparison between states and between years is therefore shielded against the cruder distortions of inflation. Wherever there is a gap between what this repository calculates and what the IBGE publishes in its official tables, the repository is documenting its methodology in public; any reader may check, reproduce and, if the case demands, refute. It is the opposite of opacity.

Let it be said in prose: what follows is not journalism of indignation. It is journalism of arithmetic. And arithmetic, when it is allowed to be read, tends to be fiercer than any editorial.

---

# part 2 — brasília, island of privilege

## 5.53 minimum wages

In the 2024 PNADC annual, the Distrito Federal appears with a mean per-capita household income equivalent to 5.53 minimum wages, in the cut calculated from the package processed in this repository. No other federal unit comes close. In cash, the IBGE's official reading tells the same story: [R$ 3,444 of per-capita income in the DF against R$ 1,077 in Maranhão](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/42761-ibge-divulga-rendimento-domiciliar-per-capita-2024-para-brasil-e-unidades-da-federacao) (in Portuguese), a ratio of 3.2 to 1 in favour of the capital; on average labour income, the DF clears R$ 5,043 against Maranhão's R$ 2,049, a gap of [more than two and a half times](https://www.dgabc.com.br/Noticia/4203759/rendimento-medio-real-foi-maior-em-2024-no-df-sp-e-parana-aponta-ibge) (in Portuguese). Whichever cut one prefers, mean, median, 90th percentile, 50th percentile, the result is the same: Brasília is an island.

What distinguishes it, when one decomposes income, is not entrepreneurship. It is the civil service. The DF's income mix is dominated by salaried labour, but the majority payer, directly or indirectly, is the state itself: the federal executive, the autarchies, the state-owned enterprises, the courts, the oversight bodies, the legislature, the armed forces, the security apparatus, and the ecosystem of outsourced staff, consultants, lawyers, lobbyists and suppliers that orbits the public machine. The DF does not produce soybeans, iron ore, steel, shoes, aeroplanes, orange juice or pulp. It produces legal opinions, memoranda, hearings, rulings, laws and bonuses. Brasília's income is, rigorously, the cost of the Brazilian Leviathan seen on the pay stub.

## the civil-service belt

There is a social class in Brazil for which Portuguese has no name: the aristocracy of the civil-service exam. Its topography lies entirely inside the DF. In Lago Sul, according to a piece in [Gazeta do Povo](https://www.gazetadopovo.com.br/economia/ricos-brasil-bairro-nobre-brasilia-ranking/) (in Portuguese), the average income reaches R$ 23,000 and, among declared earners, R$ 38,400; were it an independent municipality, it would be the richest in the country. Lago Sul is essentially a neighbourhood of federal public servants. Sudoeste, Asa Sul, Águas Claras, Lago Norte all repeat the pattern in softer gradations.

Meanwhile, the income of the richest 1 percent of the country is, for the most part, anchored in the civil service: only 1 percent of the Brazilian population, according to the Centro de Liderança Pública cited by [Gazeta do Povo](https://www.gazetadopovo.com.br/economia/supersalarios-so-1-da-populacao-tem-renda-igual-ou-superior-ao-teto-do-funcionalismo/) (in Portuguese), earns at or above the civil-service pay ceiling, which in 2026 stands at R$ 46,366.19. Belonging to the top of the Brazilian state is therefore a statistically rare achievement, and yet it is geographically concentrated in a patch of cerrado planned by Niemeyer. There are postcodes in Brasília where your probability of earning above the ceiling is in the tens of percent; in Balsas, Maranhão, that probability is rigorously microscopic.

There is nothing wrong with paying public servants. There is something deeply wrong with paying them as if the nation collectively owed them a sort of aristocratic minimum income.

## how it is financed

The entire mechanism above is funded by three sources. The first is taxation, concentrated in São Paulo, Minas Gerais, Rio Grande do Sul, Paraná and Santa Catarina. The second is public debt, which is to say the savings of future generations, intermediated by Brazilian and foreign banks. The third is disguised monetary issuance, up to the limit the Banco Central will tolerate before inflation returns. In short: Brasília lives off the fiscal extraction of the Sudeste-Sul, off the indebtedness of our children, and off the quiet erosion of the purchasing power of the poor. When a justice of the STF (Brazil's Supreme Court) receives more than R$ 3 million in twelve months, as [surveys by Transparência Brasil and República.org](https://www.poder360.com.br/poder-justica/stf-autoriza-penduricalhos-com-limite-de-35-acima-do-teto/) (in Portuguese) have shown, those three million do not fall from the sky. They fall from the pay stub of a machinist in São Bernardo, from the overdue instalments of a smallholder in Cascavel, and from the bite that the IPCA takes out of the electricity bill of a cleaning lady in Fortaleza.

The Brazilian judiciary in particular has turned itself into an economic sector apart. Judges took home [R$ 10.7 billion above the constitutional ceiling in 2025](https://www.painelpolitico.com/p/penduricalhos-do-judiciario-stf-limita) (in Portuguese); 98 percent of state judges received payments above the cap; one in four exceeded their own ceiling by more than R$ 1 million a year. When, at last, in March 2026, the STF resolved to limit the so-called penduricalhos (payments the Brazilian judiciary tacks onto base salary, euphemistically called "penduricalhos") to 35 percent of the ceiling, the practical ceiling of remuneration rose to roughly [R$ 78,800 a month](https://sintrajud.org.br/conteudo/16064/decisao-do-stf-cria-teto-de-r-78-mil-para-juizes-e-legaliza-penduricalhos) (in Portuguese), legalising by decision of the Supreme Court itself what until then had been done against the Constitution. The promised saving, R$ 7.3 billion a year, is less than what the state will still spend on the same benefits. This, in Brasília, is called adjustment.

The DF is therefore not an accident of political geography. It is a transfer machine. The 5.53 SM per capita that the people of Brasília enjoy is written, in invisible ink, onto every pay stub of every Brazilian outside Brasília.

---

# part 3 — maranhão as mirror

## 2.05 minimum wages

At the country's other extreme, Maranhão appears in the same annual PNADC with 2.05 minimum wages of per-capita household income. The figure is so low that, compared with the DF, it produces a ratio of 2.7 to 1. Maranhão is not an anomaly. It is the median of the rural Northeast: Ceará, Piauí, Alagoas and Paraíba walk shoulder to shoulder. The region that accounts for 27 percent of the Brazilian population accounts for roughly 41 percent of the individuals in the lowest income bands.

Inside Maranhão, approximately 76 percent of the population lives in households with per-capita income of up to two minimum wages. This is not a photograph of marginal poverty. It is the photograph of an entire state. There is no island. It is ocean. A population of a size comparable to Portugal's, concentrated there, lives with per-capita income at or below the conventional line of vulnerability.

## structural dependence

The state does have a GDP. It has aluminium in São Luís, a port at Itaqui, soybeans in the south, cattle in the west. But measured by the income that households actually appropriate, the Maranhão economy lives on federal transfers: rural retirement pensions from the INSS, Bolsa Família, the BPC disability benefit, the payroll of state and municipal civil servants, and the payroll of the state executive itself. In many municipalities, the sum of the town hall and social benefits comfortably exceeds what the private sector moves.

To the IBGE goes the [technical observation](https://bancadadonordeste.com.br/post/2025/12/25/81423-ibge-diz-que-o-indice-gini-de-desigualdade-seria-75-maior-sem-os-beneficios-de-programas-sociais-em-2024) (in Portuguese): without social benefits, the Gini of the Northeast would be 16.4 percent higher. A sentence that sounds benign on the surface is sinister when read in the opposite direction: the economy of the Northeast, stripped of state transfers, reveals a destitution even deeper than what we see. Social programmes do not replace the missing economy; they camouflage it. The Northeast today is not poor merely because the government transfers income; it is poor because, despite the transfers, there is still destitution to spare.

## the culture of the transfer

The most uncomfortable point, however, is not the data; it is the political system the data feed. Brazil has grown accustomed to the idea, repeated to exhaustion by PT governments, that the Northeast is a "social laboratory". A laboratory it is, but the experiment was another: for two decades, we tested whether income transfers without productive counterpart can raise a region. The answer is in the Gini itself: it falls, but only to the point at which welfare replaces work. The young male worker from the Maranhão interior joined the queue for benefits, not the queue at a factory gate, because there are no factories. This is a failure of industrial policy, not of character. To speak of Northeastern laziness is to ignore the architecture of incentives designed in Brasília.

As the FGV-IBRE study widely reported in the press has reminded us, half of Bolsa Família households stopped looking for work, with a particularly sharp effect among young men in the North and Northeast. The mechanism is trivial: the informal wages available in the region compete with the federal transfer, and often lose. The result is not indolence; it is rational decision-making. The worker does the maths. What must be redone is the state's.

The electoral consequence is well known: Lula won 69.34 percent of the valid votes in the Northeast in the second round of 2022, carried all nine states of the region and 1,774 municipalities, and won the presidential election with what remained after the rest of the country voted against him. Correlation is not causation, but in [the municipalities with the highest coverage of Auxílio Brasil, Lulismo reached 71 percent of the vote against Bolsonaro's 24](https://www.cnnbrasil.com.br/politica/nordeste-e-a-unica-regiao-em-que-lula-obteve-mais-votos-que-bolsonaro-confira/) (in Portuguese). This is no coincidence. It is the machine working exactly as it was designed.

The Northeast, as a mirror, hands the country back the image of what welfare, once converted into a state policy, becomes when it is conflated with electoral strategy.

---

# part 4 — the engine that carries the country

## the south that produces

There are three states in Brazil whose per-capita household income, measured in minimum wages, clears 4: São Paulo, Santa Catarina and Paraná. Together with Rio Grande do Sul and part of Minas Gerais, they account for more than half of the national GDP. The correlation, which ought to be banal, is uncomfortable: the states that produce the most are the ones that depend the least on federal transfers. Those that concentrate the most wealth are, ironically, the most critical of the system that redistributes it. It is no coincidence. It is a diagnosis.

Santa Catarina, the most emblematic case, grew by 5.3 percent in 2024, the [second largest advance in ten years](https://www.seplan.sc.gov.br/pib-de-santa-catarina-cresce-53-em-2024-o-segundo-maior-aumento-em-10-anos/) (in Portuguese), against a national average of 3.4 percent. Santa Catarina's GDP per capita reached R$ 61,274, the fifth highest in the country and 25.2 percent above the national average. In 2002 it was 15.5 percent above. In two decades, therefore, Santa Catarina has climbed in the national productivity distribution. Manufacturing grew 7.7 percent; tourism activity, 9 percent; commerce, 7.2 percent. There is no miracle. There is a diversified business base, an industrial tradition, human capital, port infrastructure, a work ethic inherited from German and Italian immigration, and, above all, a town hall in Joinville, another in Blumenau, another in Jaraguá do Sul that does not appear to have been designed to serve its own civil servants.

## são paulo and the overload

São Paulo is another phenomenon. On its own, it accounts for roughly a third of Brazilian GDP. It has the largest industrial park in Latin America, the busiest port in the southern hemisphere, the largest financial cluster in the country, the deepest concentration of universities and research centres, and still it receives back, in federal spending, a smaller share than it pays in taxes. It is a net donor to the federation. The São Paulo taxpayer pays for the civil service of Maranhão, for the STF's pay rise, and for the town hall of Altamira, without anything in return that resembles proportional representation in the state that it finances.

The phenomenon is known as [federative compensation](https://www.gazetadopovo.com.br/economia/funcionalismo-publico-federal-recorde-despesas-outubro/) (in Portuguese) and functions as an invisible transfer. The paulista tolerates it because, in general, he does not know it exists. The newspapers do not like to speak of the subject; São Paulo's politicians, when they run for federal office, prefer to speak of almost anything else. The result is that the region that could operate as the Singapore of South America is treated as a Treasury cold store, drained of resources to sustain, on the far side of Brazil, structures of power that are indifferent to it when they are not hostile.

## industry and productivity

In the São Paulo interior lies a quiet discovery: agricultural, industrial and services productivity converges. Ribeirão Preto, Campinas, São José dos Campos, Sorocaba and São José do Rio Preto form a belt in which GDP per capita is higher than that of entire countries. Sugar cane has given way to biotechnology; precision engineering mixes with software; the aeronautical chain at São José dos Campos continues to export what few world economies export. It is the part of Brazil that, on its own, still invites optimism. It is there. It works. It clocks in on time. It pays tax. And it carries, on its back, the gap between formal Brazilian GDP and the real GDP of Northeastern destitution.

That engine, however, is already showing signs of fatigue. The Brazilian tax burden, near 33 percent of GDP, is the highest in Latin America. The tax reform passed in 2023 and being phased in until 2033, with combined IBS and CBS rates projected between 26.5 and 28 percent, will place the Brazilian VAT [among the highest in the world](https://www.institutoliberal.org.br/blog/justica/a-vigente-reforma-tributaria-sem-confetes/) (in Portuguese), seven points above the OECD average of 19.3 percent. The engine, already spitting oil, will go on running under a squeezed tank. How long is a matter of political engineering, not of faith.

---

# part 5 — the lorenz curve and the lie of "more equal"

## reading the curve

If we plot Brazil's population in ascending order of per-capita household income on the horizontal axis, and the cumulative share of income on the vertical, we obtain the famous Lorenz curve. In a perfectly equal country, the curve would be the diagonal; in a perfectly unequal one, it would hug the lower-right corner. In Brazil, the curve runs so far from the diagonal that the Gini, as already noted, is 0.520 in this repository's methodological cut.

For didactic purposes: the richest 10 percent of the country concentrate roughly half of household income, while the poorest 40 percent concentrate less than 10 percent. The IBGE, in its official reading, [celebrates](https://www.cnnbrasil.com.br/economia/macroeconomia/ibge-renda-per-capita-tem-recorde-de-r-2-020-em-2024-desigualdade-cai-a-piso-historico/) (in Portuguese) the fact that the ratio between top and bottom fell to 13.4 times in 2024, the lowest since 2012. True enough. But 13.4 times is still a distance that, in OECD countries, would classify Brazil as a clinical case.

## international comparison

Portugal's Gini is around 0.33. Germany, 0.30. Spain, 0.34. France, 0.32. Italy, 0.36. Canada, 0.33. Even the United States, often cited as a very unequal country, operates near 0.40. Brazil, at 0.52, does not belong to the family of advanced economies. It belongs to the family of extractive economies, where a small part of society extracts rent from the larger part through mechanisms that vary from country to country but which, in Brazil's case, are called regressive taxation, high interest rates, protection of incumbents, recurring inflation, poor educational productivity, and first-class civil service.

The P90/P10 ratio of per-capita household income in Brazil is close to 10. That means that the household at the ninetieth percentile earns ten times what the household at the tenth percentile earns. In the OECD, that ratio oscillates between 3 and 5. Brazil is, in practical terms, two Swedens stacked on top of each other: the one on top working, the one below compressed under the weight of the one on top.

## p90/p10

The granular reading is worse. The band of 10 SM or more holds 6.5 percent of the population. The band of 0 to 2 SM holds 40.6 percent. Between these extremes, the distribution has a long right tail, that is, within the 6.5 percent at the top there are enormous differences between family doctors and STF justices, between owner-operators in the interior and heirs of century-old fortunes. But the hole is at the base. The mass of 40 percent who live on up to two minimum wages is what defines the country. Any political project that ignores that mass fails electorally; any political project that depends on keeping it where it is fails in civilisational terms.

The lie of "more equal" is therefore a short-sighted lie. Yes, the Gini has fallen. Yes, income has risen. But the level remains savage, and the mechanism that eased it is also the mechanism that perpetuates it: federal transfers financed by regressive taxation and debt. Cut the transfer and destitution is revealed. Cut the regressive tax and the transfer becomes unfeasible. Brazil lives in the unstable equilibrium between those two cuts.

---

# part 6 — the age pyramid and the end of the demographic bonus

## ageing

Until 2000, Brazil's age pyramid still had a broad base: many children, few elders. In 2024, that same pyramid shows a narrowing base and a broadening middle and top. The median age jumped from 28 in 2000 to 35 in 2023, with a projection of [48 by 2070](https://projetocolabora.com.br/ods11/brasil-tera-quase-70-milhoes-de-idosos-em-2050/) (in Portuguese). By 2050, 30 percent of the population will be over 60. Brazil will grow old before it grows rich, a combination that, in economic history, rarely ends well.

In the annual PNADC, the distribution by age group shows the phenomenon in real time: the cohort aged 0 to 14 shrinks in every edition, while the cohort aged 60 and above expands. The demographic bonus, that window in which there are more productive workers than dependents, will close at the start of the next decade. From then on, the dependency ratio rises. Each active worker will carry, on average, more pensioners, more survivors, more elderly in need of care.

## pension burdens

Brazilian public pensions already consume more than 13 percent of GDP, a level higher than that of most OECD countries, which spend 8 to 10 percent despite having much older populations. The reason is familiar: we spend too much on early retirement and on special regimes. The civil service, again, is the aggravating factor. The own-regime scheme for federal public servants consumes a share of pension spending disproportionate to its demographic weight, and the military own-regime operates under rules so generous that they would deserve an essay of their own. The 2019 reform, which imposed a minimum retirement age, was only the first step. There will, of necessity, be a second and a third, or the system will collapse in the middle of the 2040s.

The annual PNADC data, visit 5, already show the strain. The share of households whose principal income is a pension or a retirement payment is close to 25 percent, and is rising. In small municipalities of the rural Northeast, the share exceeds 50 percent. That means that, across vast stretches of the country, the local economy is largely the economy of the INSS. Brazil is, in some corners, a federation of pensioners.

## dependent youth

The other face of ageing is the youth left behind. The annual PNADC indicates that roughly 22 percent of young people between 15 and 29 are in the "neither-nor" condition: neither studying nor working. The phenomenon is greatest in the Northeast, especially among young women with small children, but it is not limited to that region. It is a youth that came of age during the pandemic, whose chronic literacy difficulties are documented by the [INAF 2024](https://alfabetismofuncional.org.br/) (in Portuguese), and which enters the labour market in a condition of permanent under-qualification. Intergenerational mobility, always fragile in Brazil, has grown still more stuck.

What the two ends of the pyramid show, together, is a country growing old without accumulating capital, without sufficient human capital, and without the productivity to pay for its own old age. If there is no structural reform, pension, educational and labour, in the next ten years, Brazil will spend the 2040s making painful choices between eating and retiring, between hospital and school, between civil servant and citizen.

---

# part 7 — race, sex, and the myth of identity inequality

## colour and income

It must be said first, without evasion, what the data show: there is an income gap by self-declared colour in Brazil. In the annual PNADC, visit 5, the share of whites in the band of 10 SM or more is roughly 8.7 percent; for those who declare themselves pardo (mixed-race), it is 2.6 percent. The ratio is 3.3 to 1. In terms of mean per-capita household income, whites are above pretos (blacks) and pardos in almost every cut by age, region and schooling. It would be dishonest to say that this does not exist. It exists, and it has historical roots that go back to the colonial formation and to an abolition without any policy of integration. That is not in dispute.

What is in dispute is the explanation. And here the same data are brutal with the contemporary identity narrative. When the cut is by schooling, the gap grows far wider: the share of people with completed higher education in the band of 10 SM or more is roughly 12 percent; the share of those with only primary schooling is 0.7 percent. The ratio is 17 to 1. Five times the racial gap.

## women and income

With sex, the pattern is analogous. Women's average labour income is lower than men's, even in comparable occupations, but the gap narrows dramatically once one controls for schooling, hours worked, occupation, sector and age. The "gross gap" is large; the "net gap" is small and, in some categories, reverses. Where women have higher schooling, they surpass men of the same age cohort; at undergraduate level, Brazil is a country of women. Most of what is conventionally called the gender pay gap is, in fact, an allocation gap: women choose, or are pushed by family structure, into lower-paying and shorter-hours occupations, especially after motherhood. That is a serious social problem, but it is not corporate misogyny, as the identity narrative insists.

## a non-identity reading

Schooling explains more than colour and more than sex. This is the empirical conclusion one cannot escape. The [IPEA](https://www.ipea.gov.br/portal/categorias/276-retratos-indicadores/retratos-indicadores-educacao) (in Portuguese) data confirm it: the mean years of schooling for whites is 10.8; for blacks, 9.2. The difference is real, but amounts to about a year and a half of schooling. The income gap between those with a university degree and those with only primary schooling is equivalent to 17 times the income. The racial question in Brazil is, above all, an educational question. Whoever defends public policy focused on colour rather than on human capital is treating the symptom and ignoring the disease.

This kind of analysis has a political cost. Saying aloud that Brazilian racial inequality is mostly educational inequality mediated by family history earns one the charge of insensitivity. So be it. Truth costs. The price of ignoring it is higher: policies designed to improve the lot of black Brazilians, when they ignore schooling, end by producing marginal gains for the already literate black elite, urban, university-educated, and no effect whatever on the mass of pretos and pardos in the Northeastern interior who live in households with per-capita income below 1 SM. University quotas solve the bottleneck of the 5 percent at the top of the black pyramid. They do not solve the chasm of the other 95 percent.

The serious answer is, therefore, to redistribute human capital at the base, early-childhood literacy, good basic education, school transport, school meals, a demanding curriculum, not to redistribute seats at the top. Doing the opposite is a class gesture disguised as a race gesture.

---

# part 8 — informality as refuge

## the informal gdp

The annual PNADC registers, in 2024, an informality rate of 39.0 percent of the employed population, [slightly below the 39.2 percent](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/42530-pnad-continua-em-2024-taxa-anual-de-desocupacao-foi-de-6-6-enquanto-taxa-de-subutilizacao-foi-de-16-2) (in Portuguese) recorded in 2023. In absolute terms, informal workers rose from 39.4 million to 40.3 million. The economy employs a record 103.3 million people, and yet almost four in ten work without a signed labour card, without a corporate tax number, without INSS contributions, without FGTS, without unemployment insurance, without the thirteenth-month salary and without paid holidays. They are app delivery riders, street vendors, hairdressers without a salon, self-employed bricklayers, app drivers, day cleaners, sellers of trinkets at traffic lights, door-to-door manicurists.

The number of [app-based workers grew 25.4 percent between 2022 and 2024](https://agenciadenoticias.ibge.gov.br/agencia-noticias/2012-agencia-de-noticias/noticias/44806-numero-de-trabalhadores-por-aplicativos-cresceu-25-4-entre-2022-e-2024) (in Portuguese), according to the IBGE. Informality, far from being a residue of a pre-modern economy, is today the dominant mode of organisation of low- and mid-skilled Brazilian labour. The worker has migrated from the street market to the mobile phone, but he has not migrated into the CLT (the formal labour code).

## the rationality of informality

Informality is not a product of indolence, nor of ignorance. It is a product of calculation. When a worker weighs the costs of formalisation in Brazil, employer's contribution of 20 percent to the INSS, 8 percent in FGTS, holiday provision, thirteenth, social charges, the legal risk of future litigation, the bureaucracy of opening a corporate tax number, the income-tax deduction, against informality, gross and immediate pay, no deductions, zero administrative cost, the choice is obvious. The Brazilian state punishes formal work so much more severely than informal work that a low-income worker would be making the irrational choice if he opted for the CLT.

Micro-entrepreneurs, at the margin, face the same calculation. The MEI scheme, created in 2008, was a laudable attempt at formalisation. But its revenue ceilings keep it trapped in a cage: for most, crossing the ceiling of R$ 81,000 a year is a sentence to a sudden escalation of taxation that makes growth worse than standing still. The Brazilian entrepreneur quickly understands the equation: either stay small, or jump straight to large with an investor-partner. In between, the valley of death.

## the tax burden

Brazil collects roughly 33 percent of GDP, a European-country share, and delivers the public services of a developing country. The reason is familiar: the tax base is narrow, concentrated on consumption, and revenue is consumed by the public payroll, pensions and debt, leaving very little for investment, education, health and public safety. The effective burden on the formal low-income worker, including taxes embedded in consumption, easily exceeds 40 percent. He earns, the state takes, and the state returns, in the form of a poor school, a crowded hospital, broken transport, potholed streets and queues.

Against that, informality stops being a problem and becomes a solution. It is the mechanism by which the ordinary Brazilian, without knowing it, conducts a silent tax strike against a state that does not deliver a proportionate counterpart. To formalise, in Brazil, is to agree to contribute to an arrangement from which one does not receive a reasonable share in return. Until that arrangement changes, any "anti-informality" campaign is war on a symptom. The symptom will disappear the day formalisation is good for the worker, not for the state.

---

# part 9 — the school that produces poverty

## functional illiteracy

Twenty-nine percent of Brazilians between 15 and 64 are [functionally illiterate](https://alfabetismofuncional.org.br/) (in Portuguese), according to the INAF 2024. That is the same figure as in 2018. Six years later, nothing has changed. Among young people aged 15 to 29, the rate, which stood at 14 percent in 2018, has risen to 16 percent. Three in ten adult Brazilians can read, at most, short and direct texts, without grasping complex ideas or drawing inferences. One in six young people is equally compromised.

The correlation with per-capita household income is direct: the household whose principal provider is functionally illiterate tends to cluster in the two lowest bands of SM. It does not "fall" into the bottom band; it is there by mechanical consequence of its low capacity to absorb information, adapt to new tasks, acquire digital literacy and move up professionally. Brazilian poverty, for that slice, is not episodic; it is structural, and the structure is mental.

## pisa

The results of [PISA 2022](https://www.gov.br/inep/pt-br/centrais-de-conteudo/noticias/acoes-internacionais/divulgados-os-resultados-do-pisa-2022) (in Portuguese) confirm the diagnosis: Brazil at 379 points in mathematics, 410 in reading, 403 in sciences. The OECD mean, the lowest in the series, was 472, 476 and 485. Brazil is therefore between 60 and 90 points below the OECD in every subject. This is not a small gap. It is a generational one. In South America, Brazil came [last](https://agenciabrasil.ebc.com.br/educacao/noticia/2023-12/pisa-brasil-mantem-estabilidade-em-matematica-leitura-e-ciencias) (in Portuguese) in sciences, tied with Argentina and Peru, behind Chile, Uruguay and Colombia. In creative thinking, a new assessment introduced in 2022, Brazil finished 49th out of 64 countries.

The stability of Brazilian scores since 2009 is not a merit. It is a diagnosis. It means that, despite growth in real spending on basic education, despite enrolment expansion, despite falling dropout rates, despite programme after programme, the cognitive output of Brazilian pupils has stood still. More was spent to produce the same. That is the opposite of productivity. It is structural waste. And it is a direct indictment of the pedagogical monopoly held by the teachers' unions and the state education departments, which have captured the educational machine and run it as a workers' cooperative rather than as an instrument for forming children.

## schooling versus income

Back to the arithmetic of part 7: in the band of 10 SM or more, 12 percent have higher education; only 0.7 percent have gone no further than primary. The ratio is 17 to 1. No variable, in any country, predicts individual income as well as schooling does. Whoever completes higher education in Brazil quadruples, on average, the expected income of someone who stopped at primary. Whoever completes a postgraduate degree doubles that figure again.

The Brazilian public school is therefore the single largest concrete poverty-producing machine the country operates. Not for lack of money, we spend, in share of GDP, roughly what many OECD countries spend, but by institutional design. Teachers poorly selected, poorly trained, poorly evaluated, and, in the large networks, shielded from any merit system by the unions; curricula swallowed by ideology; schools without autonomy, without incentives, without competition, and, above all, without accountability. In a word: it is a system built not to function. It is not about the ill will of a parent or a pupil. It is about the architecture of incentives.

What would work has been known worldwide since Milton Friedman: education vouchers, competition between schools, directorial autonomy, external assessment with consequences, and, at the margin, legal homeschooling for families who prefer it. To say this openly in Brazil, however, is to be labelled ultraliberal, neoliberal, privatising, and so forth. The labels come cheap; the 29 percent of functionally illiterate adults come dear.

---

# part 10 — the civil service as a class

## the ceiling

The constitutional ceiling of the civil service in 2026 is R$ 46,366.19, equivalent to the stipend of a Supreme Court justice. This ought to be a cap: the highest-paid active public servant in the country should earn, at the limit, what a justice of the Supreme Court earns. No one above that. That is what the Constitution says.

Operational reality is another. Over three decades, Brazil has developed a sophisticated juridical engineering to circumvent the ceiling without ever repealing it. Its name is penduricalho. Housing allowance, education allowance, health allowance, food allowance, length-of-service bonus, quinquennial bonus, productivity bonus, performance bonus, representation allowance, indemnity allowance, permanence bonus, relocation allowance, prize-leave converted into cash, PAE, GRG, GDE, acronym upon acronym. In 2025, before the STF's decision, Brazilian judges took home, under these headings, the equivalent of [R$ 10.7 billion above the ceiling](https://www.painelpolitico.com/p/penduricalhos-do-judiciario-stf-limita) (in Portuguese). Ninety-eight percent of state-level judges exceeded the ceiling. One in four earned more than R$ 1 million a year above the constitutional limit.

## supersalaries

The figures are obscene when set against the country's median. While 40 percent of the population lives on up to two minimum wages, about six STF justices in 2024 received [R$ 2.8 million in supersalaries above the constitutional ceiling](https://noticias-do-brasil.news/crime/crime-politica/seis-ministros-do-stf-receberam-supersalrios-acima-do-teto.html) (in Portuguese). AGU (the federal attorney-general's office) officials received bonuses in the same year that pushed pay to the ceiling, as has been amply documented. Labour court judges pocketed [R$ 1 billion above the ceiling in 2025](https://eshoje.com.br/politica/justica/2026/02/juizes-do-trabalho-receberam-r-1-bilhao-acima-do-teto-em-2025/) (in Portuguese). The public prosecution service follows. And all this is done with the endorsement, implicit or explicit, of the judiciary itself, which is at once interested party, adjudicating body and beneficiary.

The STF's March 2026 decision, which capped the penduricalhos at 35 percent of the ceiling, is described by the Court as a rigorous adjustment. In practice, it legalised what was previously contraband. The effective ceiling rose from R$ 46,000 to [R$ 78,800 a month](https://sintrajud.org.br/conteudo/16064/decisao-do-stf-cria-teto-de-r-78-mil-para-juizes-e-legaliza-penduricalhos) (in Portuguese). The Constitution, which speaks of a single limit, now has an official limit and a "limit with extras". The promised saving, R$ 7.3 billion a year, is less than what the country will continue to pay in legalised penduricalhos. This, in ministerial euphemism, is called "calibration". Ordinary Portuguese calls it shielding.

## the judiciary

What is at stake is not only money. It is a conception of the state. The Brazilian judiciary has operated, for the last two decades, as an emancipated Third Power: it adjudicates the rules of its own pay, decides the limits of its own authority, and, in decisive moments, sets the agenda of the legislature and the executive through investigations, single-judge injunctions and actions of concentrated judicial review. Its pay is only the economic face of a larger institutional hypertrophy, from the imprisonment of January 8th defendants with sentences disproportionate to equivalent crimes tried in other contexts, to the opaque handling of parliamentary inquiries, to the veiled manipulation of investigations under the banner of "risk to democracy".

This hypertrophy has a fiscal, institutional and moral cost. The fiscal cost is visible in the data: the São Paulo taxpayer pays, without knowing, for the appeals-court judge's overseas trip. The institutional cost is the capture of whole areas of politics by the law. The moral cost is the growing sense that Brazil has two legalities: one for the ordinary citizen, who pays income tax, stops at the red light, and goes to the small-claims court; another for the caste, which writes its own rules, tries itself and absolves itself. Democracy works when those two legalities are the same. In Brazil, they are not.

## shielding

The Brazilian federal civil service, all told, cost the Treasury more than R$ 380 billion in 2024. Executive-branch personnel expenditure rose under Lula to its highest level [since 2008](https://www.gazetadopovo.com.br/economia/funcionalismo-publico-federal-recorde-despesas-outubro/) (in Portuguese). Pay rises, reclassifications, new competitions, new career tracks, accelerated promotions, retroactive bonuses, all march in parallel, while the INSS retiree receives an adjustment below inflation and the public school closes its afternoon shift for lack of teachers. Part of Brazil styles itself as the working class but lives off fiscal extraction imposed on the other part of Brazil, which is effectively the working class.

It is here that the annual PNADC data acquire their sharpest and most painful clarity: Brazil does not have two classes in the Marxist sense, capital and labour. It has three: private capital, private labour and state labour. The first two coexist under capitalism. The third is a separate order, which finances itself at the expense of the first two, shields itself juridically, and oscillates between discreet silence and public outrage when threatened. It is the class that occupies the DF. It is the class that interprets the Constitution. It is the class that, in the last analysis, defines Brazil's political order. And it is the class whose bill, sooner or later, someone will have to call in.

---

# part 11 — the south that wants out

## gdp per capita in sc and pr

Santa Catarina, Paraná and Rio Grande do Sul post GDP per capita and per-capita household income systematically above the national average. Santa Catarina in particular is a phenomenon. Its GDP per capita, as we saw, is the [fifth in the country](https://www.seplan.sc.gov.br/pib-de-santa-catarina-cresce-53-em-2024-o-segundo-maior-aumento-em-10-anos/) (in Portuguese), with 2024 growth of 5.3 percent against a national average of 3.4 percent. Santa Catarina's manufacturing grew 7.7 percent. The regional Gini of the South is the lowest among Brazil's macro-regions. Income distribution is flatter, informality is lower, average schooling is higher, the employment rate is higher. On every indicator that matters to a prosperous society, the Southern region operates as if it were another country tucked inside the federation.

Paraná follows an analogous trajectory, anchored in Curitiba, Londrina, Maringá, Ponta Grossa and Cascavel. Rio Grande do Sul, despite the catastrophic floods of 2024, keeps its first-class human capital and industry. It is no coincidence that the three states have been, for decades, politically more conservative, more open to structural reform, more resistant to the Brasília agenda of unlimited income transfers. Economic structure and political structure travel together.

## tax adherence

The discomfort of the southern states with the federative pact is well known. They pay more taxes than they receive back. They finance policies that, to a large extent, do not serve them. They elect minorities in Congress. The sense of representation-deficit is real: together, the three states return smaller parliamentary benches than those of the Northeast, despite accounting for a far greater share of national GDP. That asymmetry between contribution and representation feeds a diffuse resentment that, in times of crisis, manifests itself in separatist movements: small, minority, but chronic.

The idea of a Southern Republic does not survive minimal legal scrutiny; the Constitution expressly forbids it. But as a political vocalisation of discontent, it serves: it is the sound that an electorate emits when it realises that it pays twice for the same service and receives a fraction. The Brazilian South, in its discomfort, functions as the Brazilian Catalonia, productive, literate, resentful, paying.

## political misalignment

The misalignment is double. First, regional: the South elects further to the right, governs further to the right, legislates further to the right, and is treated by the federal press, based in Rio and São Paulo, as an atypical case in need of explanation. Second, institutional: the federal institutions, concentrated in Brasília, almost never operate with a southern centre of gravity. When voters in the three states elect figures aligned with an agenda of economic freedom and minimal government, those figures run into a Brasília machine that turns any reform into a drawn-out project. What ought to be institutional weight proportional to economic weight becomes, in practice, a constant friction between the country that produces and the country that administers.

The answer, of course, is not secession. It is genuine federalism: devolve powers to the states, decentralise the budget, transfer fiscal and regulatory authority to the local levels at which accountability is possible. A federative Brazil in the American style, in which Santa Catarina might, at the limit, have different rates from Ceará, schools with different curricula, different highway codes, different security policies. That is what the southerners are asking for when they threaten, symbolically, to leave. What they mostly want is to stay, but in a different arrangement.

---

# part 12 — the political drought of the northeast

## vote and transfer

The Brazilian Northeast voted, in 2022, almost monochromatically for Lula. It gave him 69.34 percent of valid votes in the second round and victory in all nine states of the region. Bolsonaro carried a majority in only [20 Northeastern municipalities](https://www.cnnbrasil.com.br/politica/nordeste-e-a-unica-regiao-em-que-lula-obteve-mais-votos-que-bolsonaro-confira/) (in Portuguese). The remainder, some 1,794 towns, went to the PT. The phenomenon has no parallel in the country. Not even the South elects as uniformly to the right as the Northeast elects to the left.

The correlation with cash transfers is stark, even if the regional PT likes to play it down. In the municipalities with the highest coverage of Auxílio Brasil/Bolsa Família, Lula took 71 percent of the vote; Bolsonaro, 24 percent. The highest coverage coincides with the poorest, most rural, least literate regions, the ones most dependent on federal transfers. To call this vote-buying is technically false, nobody places cash inside the ballot box. To call it a structural correlation between mode of economic survival and political preference is precisely what the data show.

## coronelismo 2.0

There is, beyond the welfare layer, a deeper one: reconfigured coronelismo (the old boss politics of the interior). The Northeastern political elites operate on a fine mesh, town hall by town hall, department by department, parcelling out posts, ambulances, machinery, official cars, outsourced jobs, in exchange for votes. The PT-led federal government, in practice, refinanced that network from 2003 onwards, rebuilt it in 2023, and runs alongside it a machine that combines direct federal transfers to the citizen (Bolsa Família) with indirect transfers through the allied town hall.

Contemporary coronelismo is more efficient than that of the 1930s because it has gone digital. The Bolsa Família card is controlled by service posts in municipal facilities, which sit under the eye of the local political broker, who is chosen by the local councillor, who is an ally of the mayor, who is directly linked to the federal deputy, who votes with the government. At every link in the chain there is a political interest that converts the theoretically universal transfer into a particular favour. The product is a vote. The vote feeds the system. The system perpetuates poverty.

Breaking that cycle is the hardest and most urgent task in Brazilian politics. It is not broken with more transfers; it is broken with investment in human capital at the base, a school that works, sanitation, energy, roads, the internet, technical training, so that the Northeastern citizen stops depending politically on the town hall and starts depending professionally on his own work. It is what the data show with such clarity that, if the reader has the patience to open the `brasil.sqlite` in this repository, she will see it with her own eyes.

## coincidence

It is worth saying, for those who like to speak of coincidence, that the correlation between regional Gini, Bolsa Família coverage and PT vote is above 0.7 in the Northeast. No other variable comes close. Individual income, colour, religion, gender, age, schooling, none of these, taken alone, explains the regional vote as well as the income-welfare-town-hall combination. A correlation of 0.7 in social science is rare, almost a law of nature. In the Northeast, it is a description of the landscape.

That does not make the Northeastern voter a political zombie, as southern prejudice insinuates. It makes him a rational actor in a perversely designed system. The problem is not in him. It is in the system. Those who designed the system gather its fruits.

---

# part 13 — what the gini does not measure

## mobility

The Gini coefficient measures the dispersion of income at a single instant. It is a photograph, not a film. It tells you how unevenly income is distributed today; it does not tell you whether the poor man's son may become rich, whether the rich man's grandson may become poor, whether social position is inherited, whether meritocracy works, whether the educational system allows ascent.

In Brazil, the available studies of intergenerational mobility suggest rates far below those of developed countries. Poor father, poor son; rich father, rich son; and, increasingly, civil-servant father, civil-servant son. Rigidity sets in through three channels: inherited human capital (a literate father's son has a greater chance of being literate), inherited social capital (a well-connected family's son has a greater chance of passing a good competitive exam), and inherited economic capital (a son with family property has a greater chance of running a business without fear of falling).

A country that, like Brazil, has a high Gini and low mobility is a country in which inequality has, in practice, hardened into caste. Caste, in theory, is not Marxism. Marx spoke of class. In Brazil, however, many families with three or four generations on the same rung of society describe a pattern that resembles a caste system more than a market. The Gini does not show this. The longitudinal PNAD data are starting to.

## human capital

The World Bank has repeatedly insisted, across various publications, that the dominant explanatory element of Brazilian inequality is not the income of capital versus labour, as the Marxist tradition would have it. It is the unequal distribution of human capital. The idea, first formulated by Gary Becker and popularised by Milton Friedman, is that individual income is, to a large extent, a reflection of individual productivity, which is in turn a reflection of the sum of cognitive, emotional, technical and social skills the individual accumulates over a lifetime.

When Brazilian human capital is measured, the same World Bank places us at a modest level, close to that of much poorer economies. Our GDP per capita is larger than that of countries with comparable human capital; it is as if, in proportion, we were spending down our physical capital without investing in the human. The outcome: we grow slowly, productivity has been stagnant since the 1980s, and a generation of young people is arriving in the labour market with low literacy, worse mathematics, no technical training and no preparation for the work that the 2030s will demand.

## institutions

The work of Daron Acemoglu and James Robinson in *Why Nations Fail* is clear: the long-run difference between prosperous and stagnant nations does not lie in natural resources, nor in culture, nor in geography. It lies in the quality of institutions. Inclusive institutions generate incentives for investment, innovation, education. Extractive institutions generate incentives for rent-capture, rent-seeking, lobbying.

Brazil, unhappily, operates with extractive institutions to a large degree. The federal civil service extracting from the taxpayer. The judiciary legislating over its own ceiling. The legislature voting itself a billion-real electoral fund. State-owned firms captured by parties. Public banks deployed to distort the credit market. The concessions system auctioned off to measure. Each of these mechanisms redirects productive energy from the market to the lobby. The outcome is the Gini we have, even after 30 years of democracy. The Gini is not the problem; it is a symptom. The problem is the institutional matrix.

What the Gini does not measure, therefore, is the essential: it does not measure society's capacity to change itself. A society with a Gini of 0.52 but with institutions that allow mobility is a society that walks. A society with a Gini of 0.52 and jammed institutions is one that goes round in circles. Brazil is in the second case. That is the harshest diagnosis, and the only one that matters.

---

# part 14 — three pro-freedom exits

## a real tax reform

The tax reform in force since 2023, to be phased in by 2033, does not deserve the name. It replaces five taxes with two, simplifies compliance on paper, but keeps the burden absurd, with a combined IBS-CBS rate of 26.5 to 28 percent placing Brazil among the highest VATs in the world, [seven points above the OECD average](https://www.institutoliberal.org.br/blog/justica/a-vigente-reforma-tributaria-sem-confetes/) (in Portuguese). The so-called split payment, moreover, hands the state financial control of the transaction before the taxpayer has had access to the money: it is the largest transfer of private financial control to public hands in the country's history. It simplifies the accountant's life. It enslaves the entrepreneur.

A real tax reform would have three axes. First, a cut in the total burden by 8 to 10 points of GDP, bringing it to a level compatible with emerging economies that grow: 23 to 25 percent of GDP, never 33. Second, the replacement of payroll taxes by taxes on consumption and property, with an explicit shift of weight from labour to physical capital, in order to encourage formal hiring. Third, a negative income tax at the base, in the Friedman tradition of the Negative Income Tax, replacing the current patchwork of Bolsa Família, BPC, unemployment insurance, wage bonus and payroll relief with a transparent, predictable mechanism free of the poverty trap. Simplification would not come from the IBS software; it would come from the architecture of taxation itself.

All of this has a name in Brazil: the Single Tax, in the formulation of Marcos Cintra. The negative income tax, in Paulo Guedes's version. The spending cap, in Roberto Campos Neto's sharpest fiscal warnings. The vocabulary exists. Someone who will speak it is missing.

## an effective ceiling for the civil service

An effective ceiling for the civil service means, first, a ceiling without penduricalhos. Maximum gross pay, including indemnities, including length-of-service bonuses, including housing allowances and all the rest, capped at the constitutional stipend. Period. Any earnings above that, outside the law. Any payment above that, returned to the Treasury with interest and a fine. That demands a stricter constitutional amendment, independent oversight and, above all, political courage to confront the corporation with the greatest influence on Brazilian politics: the magistracy. There is no easy path. But there is a path.

Second, the end of the own-regime pension scheme for the public service for new entrants, with immediate migration to the general regime. Third, mandatory periodic performance review with the possibility of dismissal. Fourth, variable pay by delivery, not by length of service. Fifth, severe restriction of commissioned posts, with competitive exams for technical roles and an effective limit on posts of trust. Sixth, mandatory publication of every pay stub, every allowance, every bonus, every period of leave, every absence, on a single auditable portal.

This is not vengeance against the public servant. It is republican equality. The Brazilian public servant is no enemy. But the Brazilian public servant today operates, in so many respects, under a legally privileged regime in relation to the private-sector worker that the public ledger no longer balances. Restoring equilibrium is giving the country back what the Constitution promised.

## educational freedom

The third exit is pedagogical and institutional. Education vouchers on a pilot scale, expanded by result. Directorial autonomy in public schools, with hiring and firing by performance. Annual external assessment, with real consequences. A minimum national curriculum centred on literacy, mathematics, sciences, history, physical education and the arts, free of imported ideology. Civic-military schools where the community democratically chooses them. Legal homeschooling for families who prefer it, with mandatory external assessment. Decoupling the teachers' salary floor from mere seniority and tying it to performance: the better teacher is paid more, not the one with more years on the clock. Break the unions' monopoly on school management. Freedom to found private schools under lighter bureaucracy.

In parallel, serious investment in early-childhood literacy. The international evidence is clear: money spent up to age six yields, in human capital, ten times what money spent in secondary education yields. Brazil still operates as if the pedagogical focus were ProUni and Fies (higher-education subsidies), when it ought to be nurseries and pre-schools. Political short-sightedness funded by intellectual short-sightedness.

These three exits, taken together, are not utopian. They are technically trivial. Each has functioning equivalents in at least a dozen countries. None demands legal genius, economic genius or pedagogical genius. All demand only political courage, a horizon longer than four years, and a willingness to confront corporations, the magistracy, the unions, the party bureaucracy. In today's Brazil, that is a great deal. It may be everything. But it is necessary.

If the reader thinks these are the measures of "ultraliberals", I invite her to read the data in this repository. They are measures of survival.

---

# part 15 — epilogue: the auditable brazil

## open data

This essay is the child of a repository. Every figure cited, every average, every proportion, every Gini, every income in minimum wages, is reproducible. It suffices to clone the repository, run `brasil pipeline-run --raw latest`, and check. The microdata come from the IBGE itself, freely available on the [PNADC portal](https://www.ibge.gov.br/estatisticas/sociais/trabalho/9171-pesquisa-nacional-por-amostra-de-domicilios-continua-mensal.html) (in Portuguese); the processing is open; the methodological decisions are documented in `AGENTS.md`. Any critical reader may dismantle this text with a `SELECT` against `brasil.sqlite`. I expect it. That is what should happen.

Brazil, for the first time, can be audited by anyone with a laptop and three hours to spare. The IBGE, for all its institutional sins, continues to produce data of international quality. The IPEA, for all its sometimes scandalous militancy, still publishes respectable series. The BCB publishes monthly time series that allow for surgical deflation. The courts, opaque though they are on pay, now publish stubs that can be cross-checked against external databases. The STF, costly though it is, is traceable. The civil service, shielded though it is, is measurable.

Never in the country's history has it been so possible to know who earns what, where, why. The problem is no longer lack of data. It is excess of interpretive dishonesty.

## civic scepticism

It is worth closing, then, with a discipline: civic scepticism. Distrust every government that celebrates a low Gini without disclosing the methodology. Distrust every minister who speaks of "inclusion" without disclosing the source of funds. Distrust every party that promises "social justice" without disclosing the correlation between spending and result. Distrust, above all, anyone who speaks of "rights" without specifying who pays. Every right has a counterpart in the budget. Every budget has a counterpart in tax. Every tax has a counterpart in the taxpayer's blood. There is no magic.

The average Brazilian, fed for decades on declarative journalism, has learned to consume opinion as one consumes a telenovela: it is given, it is not questioned, the character is accepted as the author delivers him. This essay asks the opposite. It asks that the spreadsheet be opened. That the source be checked. That the Gini be recomputed. That one see, with one's own eyes, what the PNAD shows and what it hides.

For the only tragedy worse than Brazilian inequality is Brazilian disinformation. And the only way to reduce both is to turn data into a civic act.

## invitation

The data are there. The country is there. The choice rests with each of us. But the nation, that abstract thing the anthem calls the Fatherland, exists only if each citizen, in his corner, opens the spreadsheet.

The Brazil you will build for your children depends, among other small things, on your holding these numbers: 5.53 for the DF, 2.05 for Maranhão, 0.520 for the Gini, 40.6 percent in the lowest band, 6.5 percent in the highest. Memorise them. Rehearse them. Revisit them every year. Use them as a ruler.

And when somebody tells you, from the rostrum, that Brazil is at the finest moment in its history, ask: at what price, with what reform, for which generation, auditable where? If the answer is silence, you already know.

The rest, as Father Antônio Vieira wrote in another context, "is for those who will read".

---

## footnotes and sources

### numbered notes

[¹] **Gini 0.520**: Gini coefficient of per-capita household income, computed from the PNAD Contínua annual survey, visit 5, edition 2026-03, processed in this repository (`data/outputs/base_labeled_npv.csv`) with `V1028` weights. The IBGE's official reading for per-capita income in 2024, under a different methodology, is 0.506. See the IBGE note on [per-capita income and inequality in 2024](https://agenciadenoticias.ibge.gov.br/agencia-noticias/2012-agencia-de-noticias/noticias/43302-rendimento-per-capita-e-recorde-e-desigualdades-caem-ao-menor-nivel-desde-2012) (in Portuguese).

[²] **Mean SM of 3.62**: weighted mean of per-capita household income in multiples of the minimum wage prevailing in the target month, annual PNADC 2024. Corresponds to per-capita household income of R$ 2,020 in the IBGE's official reading, as per the [May 2025 note](https://agenciagov.ebc.com.br/noticias/202505/renda-per-capita-tem-aumento-recorde-de-4-7-e-desigualdades-caem-ao-menor-nivel-desde-2012) (in Portuguese).

[³] **DF 5.53 SM / MA 2.05 SM**: weighted cuts by state unit, same file. In reais, per-capita household income of R$ 3,444 in the DF and R$ 1,077 in MA, [per the IBGE](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/42761-ibge-divulga-rendimento-domiciliar-per-capita-2024-para-brasil-e-unidades-da-federacao) (in Portuguese).

[⁴] **40.6 percent up to 2 SM and 6.5 percent at 10+ SM**: distribution of the population by per-capita household income band in minimum wages, weighted estimate with replicate weights.

[⁵] **White-vs-pardo gap in the 10+ band of 3.3×**: share of whites in the top band (~8.7 percent) against share of pardos (~2.6 percent), annual PNADC, cut by self-declared colour.

[⁶] **Higher-vs-primary gap in the 10+ band of 17×**: share of persons with completed higher education in the band of 10 SM or more (~12 percent) against share of persons with only primary schooling (~0.7 percent).

[⁷] **Northeast 27 percent of the population / 41 percent of the poorest**: share of the macro-region in the national total and in the lowest band of the distribution.

[⁸] **Civil-service ceiling of R$ 46,366.19 in 2026**: monthly stipend of a Supreme Court justice, at current value, per the [Gazeta do Povo survey](https://www.gazetadopovo.com.br/economia/supersalarios-so-1-da-populacao-tem-renda-igual-ou-superior-ao-teto-do-funcionalismo/) (in Portuguese) and the [STF's March 2026 decision](https://www.painelpolitico.com/p/penduricalhos-do-judiciario-stf-limita) (in Portuguese).

[⁹] **R$ 10.7 billion above the ceiling in 2025 in the judiciary**: survey by Transparência Brasil and República.org, cited by [Painel Político](https://www.painelpolitico.com/p/penduricalhos-do-judiciario-stf-limita) (in Portuguese).

[¹⁰] **R$ 78,800 a month as the effective ceiling after the STF's 2026 decision**: a calculation that adds 35 percent of the ceiling in penduricalhos and 35 percent in length-of-service bonus to the base ceiling, per [Poder 360](https://www.poder360.com.br/poder-justica/stf-autoriza-penduricalhos-com-limite-de-35-acima-do-teto/) (in Portuguese) and [SINTRAJUD](https://sintrajud.org.br/conteudo/16064/decisao-do-stf-cria-teto-de-r-78-mil-para-juizes-e-legaliza-penduricalhos) (in Portuguese).

[¹¹] **Informality at 39.0 percent in 2024**: annual informality rate of the employed population, [IBGE](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/42530-pnad-continua-em-2024-taxa-anual-de-desocupacao-foi-de-6-6-enquanto-taxa-de-subutilizacao-foi-de-16-2) (in Portuguese).

[¹²] **INAF 29 percent of functionally illiterate adults**: [INAF 2024](https://alfabetismofuncional.org.br/) (in Portuguese), Ação Educativa and Instituto Paulo Montenegro.

[¹³] **PISA 2022 Brazil 379/410/403 against OECD 472/476/485**: [INEP](https://www.gov.br/inep/pt-br/centrais-de-conteudo/noticias/acoes-internacionais/divulgados-os-resultados-do-pisa-2022) (in Portuguese).

[¹⁴] **Combined IBS-CBS rate of 26.5 to 28 percent**: [Instituto Liberal](https://www.institutoliberal.org.br/blog/justica/a-vigente-reforma-tributaria-sem-confetes/) (in Portuguese) and the regulation under [LCP 214](https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm) (in Portuguese).

[¹⁵] **Santa Catarina's GDP per capita at R$ 61,274**: [SEPLAN-SC](https://www.seplan.sc.gov.br/pib-de-santa-catarina-cresce-53-em-2024-o-segundo-maior-aumento-em-10-anos/) (in Portuguese).

[¹⁶] **30 percent of the population above 60 by 2050**: [Fiocruz / Saúde Amanhã](https://saudeamanha.fiocruz.br/2050-brasil-tera-30-da-populacao-acima-dos-60-anos/sem-categoria/) (in Portuguese) and [Agência Gov / IBGE](https://agenciagov.ebc.com.br/noticias/202408/populacao-do-pais-vai-parar-de-crescer-em-2041) (in Portuguese).

[¹⁷] **Lula 69.34 percent in the second round in the Northeast**: [CNN Brasil](https://www.cnnbrasil.com.br/politica/nordeste-e-a-unica-regiao-em-que-lula-obteve-mais-votos-que-bolsonaro-confira/) (in Portuguese).

[¹⁸] **Years of schooling: whites 10.8 / blacks 9.2**: [Agência Brasil / IPEA](https://agenciabrasil.ebc.com.br/educacao/noticia/2024-03/brancos-estudam-em-media-108-anos-negros-92-anos) (in Portuguese).

[¹⁹] **Gini would be 7.5 percent higher without social benefits**: [IBGE, via Banca do Nordeste](https://bancadadonordeste.com.br/post/2025/12/25/81423-ibge-diz-que-o-indice-gini-de-desigualdade-seria-75-maior-sem-os-beneficios-de-programas-sociais-em-2024) (in Portuguese).

### canonical sources

- **PNAD Contínua**, Instituto Brasileiro de Geografia e Estatística: [survey homepage](https://www.ibge.gov.br/estatisticas/sociais/trabalho/17270-pnad-continua.html) (in Portuguese).
- **Microdata and 2012-2024 retrospective**, [official IBGE PDF](https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Principais_destaques_PNAD_continua/2012_2024/PNAD_continua_retrospectiva_2012_2024.pdf) (in Portuguese).
- **IPEA**, Portraits and Indicators: [income, poverty, inequality](https://www.ipea.gov.br/portal/retrato/indicadores/renda-pobreza-e-desigualdade/apresentacao) (in Portuguese) and [education](https://www.ipea.gov.br/portal/retrato/indicadores/educacao/apresentacao) (in Portuguese).
- **INEP**, PISA 2022 Brazil results: [technical note](https://download.inep.gov.br/acoes_internacionais/pisa/resultados/2022/pisa_2022_brazil_prt.pdf) (in Portuguese).
- **INAF 2024**, [official report](https://alfabetismofuncional.org.br/) (in Portuguese).
- **Banco Central do Brasil**, SGS series 1619 for the monthly minimum wage.

---

*This essay was written from a public repository processing the PNAD Contínua annual survey. The numbers are auditable. So are the opinions.*

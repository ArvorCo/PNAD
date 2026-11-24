// A lista e o download usam o mesmo CSV, ordenado pelo total de repetições.
(() => {
  const painel = document.getElementById('consulta-ids');
  const busca = painel.querySelector('input');
  const controles = painel.querySelector('fieldset');
  const corpo = painel.querySelector('tbody');
  const status = painel.querySelector('[role="status"]');
  const [anterior, proxima] = painel.querySelectorAll('button');
  const tamanho = 15;
  let todos = [], filtrados = [], pagina = 0;

  function mostrar() {
    const inicio = pagina * tamanho;
    const linhas = filtrados.slice(inicio, inicio + tamanho);
    const fmt = n => n.toLocaleString('pt-BR');
    status.textContent = linhas.length
      ? `Exibindo ${fmt(inicio + 1)} a ${fmt(inicio + linhas.length)} de ${fmt(filtrados.length)} identificadores.`
      : 'Nenhum código encontrado.';
    corpo.replaceChildren();
    for (const valores of linhas) {
      const linha = corpo.insertRow();
      for (const valor of valores) linha.insertCell().textContent = valor;
    }
    anterior.disabled = pagina === 0;
    proxima.disabled = inicio + tamanho >= filtrados.length;
  }
  busca.addEventListener('input', () => {
    const termo = busca.value.trim().toUpperCase();
    filtrados = todos.filter(([id]) => id.includes(termo));
    pagina = 0;
    mostrar();
  });
  anterior.addEventListener('click', () => { pagina--; mostrar(); });
  proxima.addEventListener('click', () => { pagina++; mostrar(); });

  async function carregar() {
    try {
      const resposta = await fetch(painel.querySelector('a[download]').href);
      if (!resposta.ok) throw Error('CSV indisponível');
      const [cabecalho, ...linhas] = (await resposta.text()).trimEnd().split(/\r?\n/);
      const colunas = 'ID de auditoria,Total de repetições,Seções 1º T,Repetições 1º T,Seções 2º T,Repetições 2º T,';
      if (!cabecalho.startsWith(colunas) || !linhas.length) throw Error('Cabeçalho inesperado');
      todos = linhas.map(linha => {
        // As seis primeiras colunas são um pseudônimo e cinco inteiros. UFs vêm depois.
        const [id, total, s1, r1, s2, r2] = linha.split(',', 6);
        if (!/^M-[0-9A-F]{12}$/.test(id) || ![total,s1,r1,s2,r2].every(v => /^\d+$/.test(v))) {
          throw Error('Registro inesperado');
        }
        return [id, s1, r1, s2, r2, total];
      });
      filtrados = todos;
      controles.disabled = false;
      mostrar();
    } catch {
      status.textContent = 'A consulta não carregou. A lista completa está disponível no link para o CSV.';
    }
  }
  carregar();
})();

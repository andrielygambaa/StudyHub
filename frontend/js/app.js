// Etapa 1: testa a conexão com o banco usando Fetch na rota /api/health.
// Nas próximas etapas, os módulos do StudyHub vão consumir as rotas Flask da mesma forma.

async function verificarConexao() {
  const status = document.getElementById("status");
  try {
    const resposta = await fetch("/api/health");
    const dados = await resposta.json();

    if (resposta.ok && dados.status === "ok") {
      status.textContent = `Banco conectado (${dados.total_tabelas} tabelas)`;
      status.className = "status ok";
    } else {
      status.textContent = dados.mensagem || "Falha na conexão com o banco.";
      status.className = "status erro";
    }
  } catch (erro) {
    status.textContent = "Não foi possível falar com o servidor Flask.";
    status.className = "status erro";
  }
}

verificarConexao();

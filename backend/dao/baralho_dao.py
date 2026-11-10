from dao.base_dao import BaseDAO
from dao.cartao_dao import CartaoDAO
from models.baralho import Baralho


class BaralhoDAO(BaseDAO):
    TABELA = "baralho"
    MODELO = Baralho
    NOME_ENTIDADE = "Baralho"

    def inserir(self, baralho):
        novo_id, _ = self._executar(
            "INSERT INTO baralho (usuario_id, materia_id, nome) VALUES (?, ?, ?)",
            (baralho.usuario_id, baralho.materia_id, baralho.nome),
        )
        return self.exigir(novo_id)

    def atualizar(self, baralho):
        self._executar(
            "UPDATE baralho SET nome = ?, materia_id = ? WHERE id = ?",
            (baralho.nome, baralho.materia_id, baralho.id),
        )
        return self.exigir(baralho.id)

    def buscar_com_cartoes(self, id):
        """Devolve o baralho já com a lista de cartões carregada."""
        baralho = self.exigir(id)
        baralho.definir_cartoes(CartaoDAO(self._conn).listar_do_baralho(id))
        return baralho

    def listar_resumo_do_usuario(self, usuario_id, hoje):
        linhas = self._linhas(
            """SELECT b.id, b.usuario_id, b.materia_id, b.nome, b.criado_em,
                      m.nome AS materia, m.cor,
                      (SELECT COUNT(*) FROM cartao c WHERE c.baralho_id = b.id) AS total_cartoes,
                      (SELECT COUNT(*) FROM cartao c
                        WHERE c.baralho_id = b.id AND c.proxima_revisao <= ?) AS para_revisar
                 FROM baralho b JOIN materia m ON m.id = b.materia_id
                WHERE b.usuario_id = ?
                ORDER BY b.nome""",
            (hoje, usuario_id),
        )
        return [dict(linha) for linha in linhas]

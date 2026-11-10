from dao.base_dao import BaseDAO
from models.cartao import Cartao


class CartaoDAO(BaseDAO):
    TABELA = "cartao"
    MODELO = Cartao
    NOME_ENTIDADE = "Cartão"

    def inserir(self, cartao):
        novo_id, _ = self._executar(
            """INSERT INTO cartao (baralho_id, frente, verso, intervalo_dias, proxima_revisao)
               VALUES (?, ?, ?, ?, ?)""",
            (cartao.baralho_id, cartao.frente, cartao.verso,
             cartao.intervalo_dias, cartao.proxima_revisao.isoformat()),
        )
        return self.exigir(novo_id)

    def atualizar_conteudo(self, cartao):
        self._executar(
            "UPDATE cartao SET frente = ?, verso = ? WHERE id = ?",
            (cartao.frente, cartao.verso, cartao.id),
        )
        return self.exigir(cartao.id)

    def atualizar_revisao(self, cartao):
        """Grava o novo agendamento (intervalo e próxima revisão)."""
        self._executar(
            "UPDATE cartao SET intervalo_dias = ?, proxima_revisao = ? WHERE id = ?",
            (cartao.intervalo_dias, cartao.proxima_revisao.isoformat(), cartao.id),
        )

    def listar_do_baralho(self, baralho_id):
        linhas = self._linhas("SELECT * FROM cartao WHERE baralho_id = ? ORDER BY id", (baralho_id,))
        return [Cartao.de_linha(linha) for linha in linhas]

    def listar_pendentes_do_usuario(self, usuario_id, hoje):
        linhas = self._linhas(
            """SELECT c.* FROM cartao c JOIN baralho b ON b.id = c.baralho_id
                WHERE b.usuario_id = ? AND c.proxima_revisao <= ?
                ORDER BY c.proxima_revisao, c.id""",
            (usuario_id, hoje),
        )
        return [Cartao.de_linha(linha) for linha in linhas]

    def contar_pendentes_do_usuario(self, usuario_id, hoje):
        return self._escalar(
            """SELECT COUNT(*) FROM cartao c JOIN baralho b ON b.id = c.baralho_id
                WHERE b.usuario_id = ? AND c.proxima_revisao <= ?""",
            (usuario_id, hoje),
        )

    def usuario_do_cartao(self, cartao_id):
        return self._escalar(
            "SELECT b.usuario_id FROM cartao c JOIN baralho b ON b.id = c.baralho_id WHERE c.id = ?",
            (cartao_id,),
        )

    def inserir_revisao(self, revisao):
        self._executar(
            "INSERT INTO revisao_cartao (cartao_id, acertou) VALUES (?, ?)",
            (revisao.cartao_id, int(revisao.acertou)),
        )

    def contar_revisoes(self, usuario_id):
        return self._escalar(
            """SELECT COUNT(*) FROM revisao_cartao r
                 JOIN cartao c ON c.id = r.cartao_id
                 JOIN baralho b ON b.id = c.baralho_id
                WHERE b.usuario_id = ?""",
            (usuario_id,),
        )

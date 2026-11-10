from dao.base_dao import BaseDAO
from models.xp_log import XPLog


class XPLogDAO(BaseDAO):
    TABELA = "xp_log"
    MODELO = XPLog
    NOME_ENTIDADE = "Registro de XP"

    def inserir(self, registro):
        novo_id, _ = self._executar(
            "INSERT INTO xp_log (usuario_id, origem, pontos, descricao) VALUES (?, ?, ?, ?)",
            (registro.usuario_id, registro.origem, registro.pontos, registro.descricao),
        )
        return self.exigir(novo_id)

    def listar_do_usuario(self, usuario_id, limite=20):
        linhas = self._linhas(
            "SELECT * FROM xp_log WHERE usuario_id = ? ORDER BY id DESC LIMIT ?",
            (usuario_id, limite),
        )
        return [XPLog.de_linha(linha) for linha in linhas]

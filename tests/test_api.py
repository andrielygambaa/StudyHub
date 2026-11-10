"""Testes de integração da API (Flask + SQLite temporário).

Execução (a partir da raiz do repositório):
    python -m unittest discover -s tests -v
"""

import itertools
import logging
import unittest
from datetime import date, timedelta
from unittest.mock import patch

import _ambiente  # noqa: F401  (configura o caminho do backend e o banco de teste)
from app import app
from dao.conquista_dao import ConquistaDAO
from db import Conexao
from init_db import criar_banco
from services.gamificacao_service import GamificacaoService

_contador = itertools.count(1)


def setUpModule():
    criar_banco(reset=True)


class ApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()

    # --- atalhos ------------------------------------------------------------
    def chamar(self, metodo, url, corpo=None, status=200):
        resposta = getattr(self.client, metodo)(url, json=corpo)
        self.assertEqual(resposta.status_code, status, f"{metodo.upper()} {url} -> {resposta.get_data(as_text=True)}")
        return resposta.get_json(silent=True)

    def get(self, url, status=200):
        return self.chamar("get", url, status=status)

    def post(self, url, corpo=None, status=201):
        return self.chamar("post", url, corpo, status)

    def put(self, url, corpo, status=200):
        return self.chamar("put", url, corpo, status)

    def patch_(self, url, corpo, status=200):
        return self.chamar("patch", url, corpo, status)

    def delete(self, url, status=204):
        return self.chamar("delete", url, status=status)

    def novo_usuario(self):
        n = next(_contador)
        return self.post("/api/usuarios", {"nome": f"Aluno {n}", "email": f"aluno{n}@teste.com"})

    def materia(self, nome="Matemática"):
        return next(m for m in self.get("/api/materias") if m["nome"] == nome)

    def sessao(self, usuario_id, duracao=25, **extra):
        corpo = {"materia_id": self.materia()["id"], "duracao_min": duracao, **extra}
        return self.post(f"/api/usuarios/{usuario_id}/sessoes", corpo)


class TestBasico(ApiTestCase):
    def test_health(self):
        dados = self.get("/api/health")
        self.assertEqual(dados["status"], "ok")
        self.assertEqual(dados["total_tabelas"], 10)

    def test_erros_sempre_em_json(self):
        self.assertIn("erro", self.get("/api/rota-que-nao-existe", status=404))
        self.assertIn("erro", self.chamar("delete", "/api/conquistas", status=405))
        resposta = self.client.post("/api/usuarios", data="texto solto", content_type="text/plain")
        self.assertEqual(resposta.status_code, 400)
        self.post("/api/usuarios", ["lista"], status=400)


class TestUsuarios(ApiTestCase):
    def test_crud_completo(self):
        criado = self.post("/api/usuarios", {"nome": "  Maria  ", "email": "MARIA@Teste.com"})
        self.assertEqual(criado["nome"], "Maria")
        self.assertEqual(criado["email"], "maria@teste.com")
        self.assertEqual((criado["xp_total"], criado["nivel"]), (0, 1))

        uid = criado["id"]
        self.assertEqual(self.get(f"/api/usuarios/{uid}")["email"], "maria@teste.com")
        self.assertIn(uid, [u["id"] for u in self.get("/api/usuarios")])

        atualizado = self.put(f"/api/usuarios/{uid}", {"nome": "Maria Silva"})
        self.assertEqual(atualizado["nome"], "Maria Silva")
        self.assertEqual(atualizado["email"], "maria@teste.com")

        self.delete(f"/api/usuarios/{uid}")
        self.get(f"/api/usuarios/{uid}", status=404)

    def test_validacoes_e_conflitos(self):
        self.post("/api/usuarios", {"nome": "", "email": "a@b.com"}, status=400)
        self.post("/api/usuarios", {"nome": "Ana", "email": "sem-arroba"}, status=400)
        self.post("/api/usuarios", {"nome": "Ana"}, status=400)
        usuario = self.novo_usuario()
        self.post("/api/usuarios", {"nome": "Outro", "email": usuario["email"]}, status=409)
        outro = self.novo_usuario()
        self.put(f"/api/usuarios/{outro['id']}", {"email": usuario["email"]}, status=409)
        self.get("/api/usuarios/999999", status=404)


class TestMaterias(ApiTestCase):
    def test_catalogo_inicial_e_crud(self):
        self.assertGreaterEqual(len(self.get("/api/materias")), 9)
        nome = f"Artes {next(_contador)}"
        criada = self.post("/api/materias", {"nome": nome, "cor": "#FF8800"})
        self.assertEqual(criada["cor"], "#ff8800")
        self.post("/api/materias", {"nome": nome}, status=409)
        self.post("/api/materias", {"nome": "Sociologia", "cor": "laranja"}, status=400)
        renomeada = self.put(f"/api/materias/{criada['id']}", {"nome": nome + " (Visuais)"})
        self.assertTrue(renomeada["nome"].endswith("(Visuais)"))
        self.delete(f"/api/materias/{criada['id']}")
        self.get(f"/api/materias/{criada['id']}", status=404)

    def test_materia_em_uso_nao_pode_ser_excluida(self):
        usuario = self.novo_usuario()
        materia = self.post("/api/materias", {"nome": f"Em uso {next(_contador)}"})
        self.post(f"/api/usuarios/{usuario['id']}/topicos", {"materia_id": materia["id"], "titulo": "Algo"})
        self.delete(f"/api/materias/{materia['id']}", status=409)


class TestPlanner(ApiTestCase):
    def test_status_avanca_e_gera_xp_e_conquista(self):
        usuario = self.novo_usuario()
        uid = usuario["id"]
        topico = self.post(f"/api/usuarios/{uid}/topicos",
                           {"materia_id": self.materia()["id"], "titulo": "Funções do 2º grau"})
        self.assertEqual(topico["status"], "nao_visto")
        tid = topico["id"]

        passo1 = self.patch_(f"/api/topicos/{tid}/status", {"status": "estudando"})
        self.assertIsNone(passo1["gamificacao"])

        passo2 = self.patch_(f"/api/topicos/{tid}/status", {"status": "revisado"})
        gam = passo2["gamificacao"]
        self.assertEqual(gam["pontos"], 15)
        self.assertEqual([c["codigo"] for c in gam["conquistas_desbloqueadas"]], ["primeiro_topico"])
        self.assertEqual(gam["xp_total"], 35)          # 15 do tópico + 20 de bônus
        self.assertEqual(self.get(f"/api/usuarios/{uid}")["xp_total"], 35)

        # não dá para voltar atrás nem ganhar XP de novo
        self.patch_(f"/api/topicos/{tid}/status", {"status": "estudando"}, status=400)
        repetido = self.patch_(f"/api/topicos/{tid}/status", {"status": "revisado"})
        self.assertIsNone(repetido["gamificacao"])
        self.post(f"/api/topicos/{tid}/avancar", status=400)
        self.assertEqual(self.get(f"/api/usuarios/{uid}")["xp_total"], 35)

    def test_avancar_e_filtros(self):
        uid = self.novo_usuario()["id"]
        mat = self.materia("Física")["id"]
        a = self.post(f"/api/usuarios/{uid}/topicos", {"materia_id": mat, "titulo": "Cinemática"})
        self.post(f"/api/usuarios/{uid}/topicos", {"materia_id": self.materia()["id"], "titulo": "Logaritmos"})
        self.assertEqual(self.post(f"/api/topicos/{a['id']}/avancar", status=200)["topico"]["status"], "estudando")

        self.assertEqual(len(self.get(f"/api/usuarios/{uid}/topicos")), 2)
        self.assertEqual(len(self.get(f"/api/usuarios/{uid}/topicos?materia_id={mat}")), 1)
        self.assertEqual(len(self.get(f"/api/usuarios/{uid}/topicos?status=estudando")), 1)
        self.get(f"/api/usuarios/{uid}/topicos?status=outro", status=400)

        editado = self.put(f"/api/topicos/{a['id']}", {"titulo": "Cinemática vetorial"})
        self.assertEqual(editado["titulo"], "Cinemática vetorial")
        self.delete(f"/api/topicos/{a['id']}")
        self.get(f"/api/topicos/{a['id']}", status=404)

    def test_validacoes(self):
        uid = self.novo_usuario()["id"]
        self.post(f"/api/usuarios/{uid}/topicos", {"titulo": "Sem matéria"}, status=400)
        self.post(f"/api/usuarios/{uid}/topicos", {"materia_id": 99999, "titulo": "X"}, status=404)
        self.post(f"/api/usuarios/{uid}/topicos", {"materia_id": self.materia()["id"], "titulo": " "}, status=400)
        self.post("/api/usuarios/99999/topicos", {"materia_id": 1, "titulo": "X"}, status=404)


class TestPomodoro(ApiTestCase):
    def test_sessao_concluida_gera_xp_e_conquista(self):
        uid = self.novo_usuario()["id"]
        resposta = self.sessao(uid, 25)
        self.assertTrue(resposta["sessao"]["concluida"])
        gam = resposta["gamificacao"]
        self.assertEqual(gam["pontos"], 10)
        self.assertEqual([c["codigo"] for c in gam["conquistas_desbloqueadas"]], ["primeira_sessao"])
        self.assertEqual(gam["xp_total"], 30)

        interrompida = self.sessao(uid, 25, concluida=False)
        self.assertIsNone(interrompida["gamificacao"])
        self.assertEqual(self.get(f"/api/usuarios/{uid}")["xp_total"], 30)

    def test_listagem_filtros_e_exclusao(self):
        uid = self.novo_usuario()["id"]
        primeira = self.sessao(uid, 25)["sessao"]
        self.sessao(uid, 50)
        hoje = date.today().isoformat()
        amanha = (date.today() + timedelta(days=1)).isoformat()
        self.assertEqual(len(self.get(f"/api/usuarios/{uid}/sessoes")), 2)
        self.assertEqual(len(self.get(f"/api/usuarios/{uid}/sessoes?de={hoje}")), 2)
        self.assertEqual(len(self.get(f"/api/usuarios/{uid}/sessoes?de={amanha}")), 0)
        self.get(f"/api/usuarios/{uid}/sessoes?de=ontem", status=400)

        xp_antes = self.get(f"/api/usuarios/{uid}")["xp_total"]
        self.delete(f"/api/sessoes/{primeira['id']}")
        self.get(f"/api/sessoes/{primeira['id']}", status=404)
        self.assertEqual(self.get(f"/api/usuarios/{uid}")["xp_total"], xp_antes)   # o extrato de XP permanece

    def test_validacoes(self):
        uid = self.novo_usuario()["id"]
        mat = self.materia()["id"]
        url = f"/api/usuarios/{uid}/sessoes"
        self.post(url, {"materia_id": mat, "duracao_min": 0}, status=400)
        self.post(url, {"materia_id": mat, "duracao_min": 500}, status=400)
        self.post(url, {"materia_id": mat, "duracao_min": "abc"}, status=400)
        self.post(url, {"duracao_min": 25}, status=400)
        self.post(url, {"materia_id": 99999, "duracao_min": 25}, status=404)
        self.post("/api/usuarios/99999/sessoes", {"materia_id": mat, "duracao_min": 25}, status=404)

    def test_vinculo_com_topico(self):
        dono = self.novo_usuario()["id"]
        outro = self.novo_usuario()["id"]
        fis = self.materia("Física")["id"]
        topico = self.post(f"/api/usuarios/{dono}/topicos", {"materia_id": fis, "titulo": "Dinâmica"})

        # a matéria é herdada do tópico quando não for informada
        sessao = self.post(f"/api/usuarios/{dono}/sessoes", {"topico_id": topico["id"], "duracao_min": 25})
        self.assertEqual(sessao["sessao"]["materia_id"], fis)
        # matéria diferente da do tópico
        self.post(f"/api/usuarios/{dono}/sessoes",
                  {"topico_id": topico["id"], "materia_id": self.materia()["id"], "duracao_min": 25}, status=400)
        # tópico de outro usuário
        self.post(f"/api/usuarios/{outro}/sessoes", {"topico_id": topico["id"], "duracao_min": 25}, status=400)

    def test_transacao_atomica(self):
        """Se a gamificação falhar, a sessão também não é gravada."""
        uid = self.novo_usuario()["id"]
        logging.disable(logging.CRITICAL)
        try:
            with patch.object(GamificacaoService, "conceder_xp", side_effect=RuntimeError("falha simulada")):
                resposta = self.client.post(f"/api/usuarios/{uid}/sessoes",
                                            json={"materia_id": self.materia()["id"], "duracao_min": 25})
        finally:
            logging.disable(logging.NOTSET)
        self.assertEqual(resposta.status_code, 500)
        self.assertEqual(self.get(f"/api/usuarios/{uid}/sessoes"), [])
        self.assertEqual(self.get(f"/api/usuarios/{uid}")["xp_total"], 0)


class TestFlashcards(ApiTestCase):
    def test_repeticao_espacada_e_xp(self):
        uid = self.novo_usuario()["id"]
        baralho = self.post(f"/api/usuarios/{uid}/baralhos",
                            {"materia_id": self.materia()["id"], "nome": "Fórmulas"})
        bid = baralho["id"]
        c1 = self.post(f"/api/baralhos/{bid}/cartoes", {"frente": "Delta?", "verso": "b²-4ac"})
        self.assertEqual(c1["intervalo_dias"], 1)
        self.assertEqual(c1["proxima_revisao"], date.today().isoformat())
        self.assertEqual(len(self.get(f"/api/baralhos/{bid}/revisar")), 1)

        # acertou: intervalo dobra, XP e primeira conquista de cartão
        r1 = self.post(f"/api/cartoes/{c1['id']}/revisao", {"acertou": True}, status=200)
        self.assertEqual(r1["cartao"]["intervalo_dias"], 2)
        self.assertEqual(r1["cartao"]["proxima_revisao"], (date.today() + timedelta(days=2)).isoformat())
        self.assertEqual(r1["gamificacao"]["pontos"], 3)
        self.assertEqual([c["codigo"] for c in r1["gamificacao"]["conquistas_desbloqueadas"]], ["primeiro_cartao"])
        self.assertEqual(r1["gamificacao"]["xp_total"], 13)
        self.assertEqual(self.get(f"/api/baralhos/{bid}/revisar"), [])
        self.assertEqual(self.get(f"/api/usuarios/{uid}/cartoes/pendentes"), [])

        # errou: volta para 1 dia (amanhã), vale 1 XP
        c2 = self.post(f"/api/baralhos/{bid}/cartoes", {"frente": "Bhaskara?", "verso": "(-b±√Δ)/2a"})
        r2 = self.post(f"/api/cartoes/{c2['id']}/revisao", {"acertou": False}, status=200)
        self.assertEqual(r2["cartao"]["intervalo_dias"], 1)
        self.assertEqual(r2["cartao"]["proxima_revisao"], (date.today() + timedelta(days=1)).isoformat())
        self.assertEqual(r2["gamificacao"]["pontos"], 1)
        self.assertFalse(r2["revisao"]["acertou"])

        self.post(f"/api/cartoes/{c2['id']}/revisao", {}, status=400)
        self.post(f"/api/cartoes/{c2['id']}/revisao", {"acertou": "talvez"}, status=400)
        self.post("/api/cartoes/99999/revisao", {"acertou": True}, status=404)

    def test_baralho_cartoes_e_exclusao(self):
        uid = self.novo_usuario()["id"]
        bid = self.post(f"/api/usuarios/{uid}/baralhos",
                        {"materia_id": self.materia("Inglês")["id"], "nome": "Vocabulário"})["id"]
        cartao = self.post(f"/api/baralhos/{bid}/cartoes", {"frente": "House", "verso": "Casa"})
        self.post(f"/api/baralhos/{bid}/cartoes", {"frente": "Dog", "verso": "Cachorro"})

        detalhe = self.get(f"/api/baralhos/{bid}")
        self.assertEqual(len(detalhe["cartoes"]), 2)
        self.assertEqual(detalhe["para_revisar_hoje"], 2)
        resumo = self.get(f"/api/usuarios/{uid}/baralhos")
        self.assertEqual((resumo[0]["total_cartoes"], resumo[0]["para_revisar"], resumo[0]["materia"]),
                         (2, 2, "Inglês"))

        editado = self.put(f"/api/cartoes/{cartao['id']}", {"verso": "Casa/Lar"})
        self.assertEqual(editado["verso"], "Casa/Lar")
        self.put(f"/api/baralhos/{bid}", {"nome": "Vocabulário A1"})
        self.delete(f"/api/cartoes/{cartao['id']}")
        self.assertEqual(len(self.get(f"/api/baralhos/{bid}/cartoes")), 1)
        self.delete(f"/api/baralhos/{bid}")
        self.get(f"/api/baralhos/{bid}", status=404)
        self.post(f"/api/baralhos/{bid}/cartoes", {"frente": "a", "verso": "b"}, status=404)

    def test_validacoes(self):
        uid = self.novo_usuario()["id"]
        self.post(f"/api/usuarios/{uid}/baralhos", {"nome": "Sem matéria"}, status=400)
        self.post(f"/api/usuarios/{uid}/baralhos", {"materia_id": 99999, "nome": "X"}, status=404)
        bid = self.post(f"/api/usuarios/{uid}/baralhos", {"materia_id": 1, "nome": "Ok"})["id"]
        self.post(f"/api/baralhos/{bid}/cartoes", {"frente": "só frente"}, status=400)


class TestGamificacao(ApiTestCase):
    def test_nivel_5_por_xp_de_sessoes(self):
        """Quatro sessões longas levam ao nível 5, que paga seu próprio bônus."""
        uid = self.novo_usuario()["id"]
        for _ in range(3):
            self.sessao(uid, 240)
        ultima = self.sessao(uid, 240)["gamificacao"]      # 4 x 96 XP + 20 de bônus = 404 (nível 5)

        self.assertEqual([c["codigo"] for c in ultima["conquistas_desbloqueadas"]], ["nivel_5"])
        self.assertEqual(ultima["xp_bonus_conquistas"], 100)
        self.assertEqual(ultima["xp_total"], 504)
        self.assertEqual(ultima["nivel"], 6)
        self.assertTrue(ultima["subiu_de_nivel"])

        codigos = {i["conquista"]["codigo"] for i in self.get(f"/api/usuarios/{uid}/conquistas")}
        self.assertEqual(codigos, {"primeira_sessao", "nivel_5"})

    def _usuario_com_xp(self, xp):
        uid = self.novo_usuario()["id"]
        with Conexao() as conn:
            conn.execute("UPDATE usuario SET xp_total = ? WHERE id = ?", (xp, uid))
        return uid

    def test_bonus_de_uma_conquista_leva_ao_nivel_5(self):
        """370 XP + 10 da sessão = 380 (nível 4); o bônus de 20 da 1ª sessão chega a 400 (nível 5)."""
        uid = self._usuario_com_xp(370)
        gam = self.sessao(uid, 25)["gamificacao"]
        self.assertEqual([c["codigo"] for c in gam["conquistas_desbloqueadas"]], ["primeira_sessao", "nivel_5"])
        self.assertEqual(gam["xp_total"], 500)             # 370 + 10 + 20 + 100
        self.assertEqual(gam["xp_bonus_conquistas"], 120)

    def test_cadeia_nao_depende_da_ordem_do_catalogo(self):
        """Mesmo se 'nivel_5' for avaliada ANTES da conquista que paga o bônus, ela é desbloqueada
        na repetição do laço de verificar_conquistas."""
        original = ConquistaDAO.listar_todas
        uid = self._usuario_com_xp(370)
        with patch.object(ConquistaDAO, "listar_todas", lambda self: list(reversed(original(self)))):
            gam = self.sessao(uid, 25)["gamificacao"]
        self.assertEqual([c["codigo"] for c in gam["conquistas_desbloqueadas"]], ["primeira_sessao", "nivel_5"])
        self.assertEqual(gam["xp_total"], 500)

    def test_dez_sessoes(self):
        uid = self.novo_usuario()["id"]
        for _ in range(9):
            self.sessao(uid, 25)
        decima = self.sessao(uid, 25)["gamificacao"]
        self.assertEqual([c["codigo"] for c in decima["conquistas_desbloqueadas"]], ["dez_sessoes"])
        self.assertEqual(decima["xp_total"], 170)          # 10 x 10 + 20 + 50

    def test_catalogo_e_extrato(self):
        self.assertEqual(len(self.get("/api/conquistas")), 7)
        uid = self.novo_usuario()["id"]
        self.sessao(uid, 25)
        extrato = self.get(f"/api/usuarios/{uid}/xp")
        self.assertEqual([e["origem"] for e in extrato["extrato"]], ["conquista", "pomodoro"])
        self.assertEqual(extrato["usuario"]["xp_total"], sum(e["pontos"] for e in extrato["extrato"]))
        self.get(f"/api/usuarios/{uid}/xp?limite=0", status=400)


class TestDashboardECascata(ApiTestCase):
    def test_dashboard(self):
        uid = self.novo_usuario()["id"]
        mat = self.materia()["id"]
        self.sessao(uid, 25)
        topico = self.post(f"/api/usuarios/{uid}/topicos", {"materia_id": mat, "titulo": "Limites"})
        self.post(f"/api/topicos/{topico['id']}/avancar", status=200)
        bid = self.post(f"/api/usuarios/{uid}/baralhos", {"materia_id": mat, "nome": "Cálculo"})["id"]
        self.post(f"/api/baralhos/{bid}/cartoes", {"frente": "lim", "verso": "limite"})

        d = self.get(f"/api/usuarios/{uid}/dashboard")
        self.assertEqual(d["usuario"]["id"], uid)
        self.assertEqual(d["pomodoro"]["minutos_na_semana"], 25)
        self.assertEqual(len(d["pomodoro"]["minutos_por_dia"]), 7)
        self.assertEqual(d["pomodoro"]["minutos_por_dia"][-1], {"data": date.today().isoformat(), "minutos": 25})
        self.assertEqual(d["pomodoro"]["minutos_por_materia"][0]["materia"], "Matemática")
        self.assertEqual(d["planner"]["progresso_por_materia"][0]["total"], 1)
        self.assertEqual(d["planner"]["progresso_por_materia"][0]["estudando"], 1)
        self.assertEqual(d["flashcards"]["cartoes_para_revisar_hoje"], 1)
        self.assertEqual(d["gamificacao"]["conquistas_desbloqueadas"], 1)
        self.assertEqual(d["gamificacao"]["total_conquistas"], 7)
        self.get("/api/usuarios/99999/dashboard", status=404)

    def test_excluir_usuario_apaga_tudo_dele(self):
        uid = self.novo_usuario()["id"]
        mat = self.materia()["id"]
        self.sessao(uid, 25)
        self.post(f"/api/usuarios/{uid}/topicos", {"materia_id": mat, "titulo": "X"})
        bid = self.post(f"/api/usuarios/{uid}/baralhos", {"materia_id": mat, "nome": "B"})["id"]
        cid = self.post(f"/api/baralhos/{bid}/cartoes", {"frente": "a", "verso": "b"})["id"]
        self.post(f"/api/cartoes/{cid}/revisao", {"acertou": True}, status=200)

        self.delete(f"/api/usuarios/{uid}")
        with Conexao() as conn:
            for tabela in ("sessao_estudo", "topico", "baralho", "xp_log", "usuario_conquista"):
                total = conn.execute(f"SELECT COUNT(*) FROM {tabela} WHERE usuario_id = ?", (uid,)).fetchone()[0]
                self.assertEqual(total, 0, tabela)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM cartao WHERE id = ?", (cid,)).fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM revisao_cartao WHERE cartao_id = ?", (cid,)).fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()

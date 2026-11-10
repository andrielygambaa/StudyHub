"""Testes das classes do domínio (não usam banco de dados).

Execução (a partir da raiz do repositório):
    python -m unittest discover -s tests -v
"""

import unittest
from datetime import date, timedelta

import _ambiente  # noqa: F401  (configura o caminho do backend e o banco de teste)
from erros import ValidacaoErro
from models import Baralho, Cartao, SessaoEstudo, Topico, Usuario
from services.gamificacao_service import GamificacaoService


class TestUsuario(unittest.TestCase):
    def test_nivel_sobe_a_cada_100_xp(self):
        usuario = Usuario("Ana", "ana@teste.com")
        self.assertEqual(usuario.calcular_nivel(), 1)
        usuario.adicionar_xp(99)
        self.assertEqual(usuario.calcular_nivel(), 1)
        usuario.adicionar_xp(1)
        self.assertEqual(usuario.calcular_nivel(), 2)
        usuario.adicionar_xp(150)
        self.assertEqual(usuario.calcular_nivel(), 3)
        self.assertEqual(usuario.xp_para_proximo_nivel(), 50)

    def test_xp_deve_ser_positivo(self):
        with self.assertRaises(ValidacaoErro):
            Usuario("Ana", "ana@teste.com").adicionar_xp(0)

    def test_validacoes(self):
        with self.assertRaises(ValidacaoErro):
            Usuario("   ", "ana@teste.com")
        with self.assertRaises(ValidacaoErro):
            Usuario("Ana", "email-invalido")
        self.assertEqual(Usuario("Ana", "ANA@Teste.COM").email, "ana@teste.com")


class TestTopico(unittest.TestCase):
    def test_status_so_avanca(self):
        topico = Topico(1, 1, "Funções")
        self.assertTrue(topico.mudar_status("estudando"))
        self.assertFalse(topico.mudar_status("estudando"))
        self.assertTrue(topico.mudar_status("revisado"))
        with self.assertRaises(ValidacaoErro):
            topico.mudar_status("estudando")

    def test_avancar_status(self):
        topico = Topico(1, 1, "Funções")
        topico.avancar_status()
        self.assertEqual(topico.status, "estudando")
        topico.avancar_status()
        self.assertEqual(topico.status, "revisado")
        with self.assertRaises(ValidacaoErro):
            topico.avancar_status()

    def test_status_invalido(self):
        with self.assertRaises(ValidacaoErro):
            Topico(1, 1, "Funções").mudar_status("qualquer")


class TestSessao(unittest.TestCase):
    def test_duracao_valida(self):
        with self.assertRaises(ValidacaoErro):
            SessaoEstudo(1, 1, 0)
        with self.assertRaises(ValidacaoErro):
            SessaoEstudo(1, 1, 241)
        self.assertEqual(SessaoEstudo(1, 1, 25).duracao_min, 25)

    def test_pontos_da_sessao(self):
        self.assertEqual(GamificacaoService.pontos_sessao(25), 10)
        self.assertEqual(GamificacaoService.pontos_sessao(50), 20)
        self.assertEqual(GamificacaoService.pontos_sessao(1), 1)


class TestCartao(unittest.TestCase):
    def test_acertos_dobram_o_intervalo(self):
        cartao = Cartao(1, "Delta?", "b²-4ac", id=1)
        hoje = date(2026, 11, 10)
        esperado = [2, 4, 8]
        for dias in esperado:
            cartao.registrar_revisao(True, hoje)
            self.assertEqual(cartao.intervalo_dias, dias)
            self.assertEqual(cartao.proxima_revisao, hoje + timedelta(days=dias))

    def test_erro_volta_para_um_dia(self):
        cartao = Cartao(1, "f", "v", id=1, intervalo_dias=16)
        cartao.registrar_revisao(False, date(2026, 11, 10))
        self.assertEqual(cartao.intervalo_dias, 1)
        self.assertEqual(cartao.proxima_revisao, date(2026, 11, 11))

    def test_intervalo_tem_limite(self):
        cartao = Cartao(1, "f", "v", id=1, intervalo_dias=300)
        cartao.registrar_revisao(True)
        self.assertEqual(cartao.intervalo_dias, 365)

    def test_revisao_devolve_registro(self):
        revisao = Cartao(1, "f", "v", id=7).registrar_revisao(True)
        self.assertEqual(revisao.cartao_id, 7)
        self.assertTrue(revisao.acertou)

    def test_acertou_deve_ser_booleano(self):
        with self.assertRaises(ValidacaoErro):
            Cartao(1, "f", "v", id=1).registrar_revisao("talvez")


class TestBaralho(unittest.TestCase):
    def test_cartoes_para_revisar(self):
        hoje = date(2026, 11, 10)
        vencido = Cartao(1, "a", "b", id=1, proxima_revisao=hoje - timedelta(days=1))
        de_hoje = Cartao(1, "c", "d", id=2, proxima_revisao=hoje)
        futuro = Cartao(1, "e", "f", id=3, proxima_revisao=hoje + timedelta(days=3))
        baralho = Baralho(1, 1, "Fórmulas")
        baralho.definir_cartoes([vencido, de_hoje, futuro])
        self.assertEqual([c.id for c in baralho.cartoes_para_revisar(hoje)], [1, 2])


if __name__ == "__main__":
    unittest.main()

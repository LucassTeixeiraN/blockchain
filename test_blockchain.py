import copy
import unittest

from blockchain import (
    Blockchain, Bloco, HASH_ANTERIOR_GENESE, REGISTRO_GENESE,
    criar_registro, serializar_canonico,
)


def reg(n=1):
    return criar_registro("certificado", f"aluno-{n:03d}", f"Conclusão da disciplina {n}")


def cadeia(dif=1, n=3):
    c = Blockchain(dificuldade=dif)
    for i in range(1, n + 1):
        c.adicionar_bloco([reg(i)], timestamp=1000 + i)
    return c


class TestSerializacaoEHash(unittest.TestCase):
    def test_serializacao_canonica_independe_da_ordem(self):
        a = {"b": 1, "a": {"y": 2, "x": 3}}
        b = {"a": {"x": 3, "y": 2}, "b": 1}
        self.assertEqual(serializar_canonico(a), serializar_canonico(b))
        self.assertEqual(serializar_canonico(a), '{"a":{"x":3,"y":2},"b":1}')

    def test_unicode_preservado_e_nan_rejeitado(self):
        self.assertIn("ç", serializar_canonico({"k": "ç"}))
        for ruim in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                serializar_canonico({"k": ruim})

    def test_hash_deterministico_e_64_hex(self):
        b = Bloco(1, 5, [reg()], "0" * 64, 1)
        self.assertEqual(b.calcular_hash(), b.calcular_hash())
        self.assertEqual(len(b.calcular_hash()), 64)

    def test_hash_muda_com_um_caractere(self):
        b1 = Bloco(1, 5, [criar_registro("a", "aluno-001", "nota A")], "0" * 64, 1)
        b2 = Bloco(1, 5, [criar_registro("a", "aluno-001", "nota B")], "0" * 64, 1)
        self.assertNotEqual(b1.calcular_hash(), b2.calcular_hash())

    def test_hash_nao_inclui_campo_hash(self):
        b = Bloco(1, 5, [reg()], "0" * 64, 1)
        self.assertNotIn("hash", b.conteudo_para_hash())
        antes = b.calcular_hash()
        b.hash = "qualquer"
        self.assertEqual(antes, b.calcular_hash())


class TestRegistro(unittest.TestCase):
    def test_registro_valido_normaliza(self):
        self.assertEqual(
            criar_registro(" t ", " aluno-1 ", " d "),
            {"tipo": "t", "participante": "aluno-1", "descricao": "d"},
        )

    def test_campo_vazio_rejeitado(self):
        for args in (("", "a", "b"), ("a", "  ", "b"), ("a", "b", "")):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    criar_registro(*args)

    def test_tipo_incorreto_rejeitado(self):
        for args in ((1, "a", "b"), ("a", None, "b"), ("a", "b", ["x"])):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    criar_registro(*args)


class TestGeneseEMineracao(unittest.TestCase):
    def test_genese_valida(self):
        g = Blockchain(1).blocos[0]
        self.assertEqual(g.indice, 0)
        self.assertEqual(g.timestamp, 0)
        self.assertEqual(g.hash_anterior, HASH_ANTERIOR_GENESE)
        self.assertEqual(g.registros, [REGISTRO_GENESE])
        self.assertEqual(g.hash, g.calcular_hash())

    def test_mineracao_satisfaz_dificuldade(self):
        for d in (1, 2, 3):
            with self.subTest(d=d):
                b = Bloco(1, 1, [reg()], "0" * 64, d)
                tentativas = b.minerar()
                self.assertTrue(b.hash.startswith("0" * d))
                self.assertEqual(b.hash, b.calcular_hash())
                self.assertEqual(tentativas, b.nonce + 1)

    def test_dificuldade_fora_do_intervalo(self):
        for d in (0, 7, -1):
            with self.subTest(d=d):
                with self.assertRaises(ValueError):
                    Blockchain(d)
                with self.assertRaises(ValueError):
                    Bloco(1, 1, [reg()], "0" * 64, d)
        for d in (True, 1.5, "2"):
            with self.subTest(d=d):
                with self.assertRaises(TypeError):
                    Blockchain(d)

    def test_dificuldade_fora_do_intervalo_na_validacao(self):
        c = cadeia()
        c.blocos[1].dificuldade = 7
        self.assertFalse(c.validar())


class TestCadeia(unittest.TestCase):
    def test_tres_blocos_encadeados_e_validos(self):
        c = cadeia(1, 3)
        self.assertEqual(len(c.blocos), 4)
        for i in range(1, 4):
            self.assertEqual(c.blocos[i].indice, i)
            self.assertEqual(c.blocos[i].hash_anterior, c.blocos[i - 1].hash)
        self.assertEqual(c.ultimo_bloco, c.blocos[-1])
        self.assertTrue(c.validar())

    def test_registro_adulterado_rejeitado(self):
        c = cadeia()
        c.blocos[1].registros[0]["descricao"] = "adulterado"
        self.assertFalse(c.validar())

    def test_hash_anterior_adulterado_rejeitado(self):
        c = cadeia()
        c.blocos[2].hash_anterior = "f" * 64
        self.assertFalse(c.validar())

    def test_nonce_adulterado_rejeitado(self):
        c = cadeia()
        c.blocos[2].nonce += 1
        self.assertFalse(c.validar())

    def test_prova_invalida_rejeitada(self):
        c = cadeia(2)
        b = c.blocos[3]
        b.nonce = 0
        while b.calcular_hash().startswith("00"):
            b.nonce += 1
        b.hash = b.calcular_hash()  # hash coerente, mas sem PoW
        self.assertFalse(c.validar())

    def test_indice_e_genese_adulterados(self):
        c = cadeia()
        c.blocos[1].indice = 5
        self.assertFalse(c.validar())
        c = cadeia()
        c.blocos[0].registros[0]["descricao"] = "outra"
        c.blocos[0].minerar()
        self.assertFalse(c.validar())

    def test_remocao_de_bloco_intermediario_rejeitada(self):
        c = cadeia()
        del c.blocos[1]
        self.assertFalse(c.validar())

    def test_remineracao_parcial_nao_conserta(self):
        c = cadeia()
        c.blocos[1].registros[0]["descricao"] = "adulterado"
        c.blocos[1].minerar()
        self.assertFalse(c.validar())  # bloco 2 aponta para o hash antigo

    def test_remineracao_total_torna_valida_novamente(self):
        c = cadeia()
        c.blocos[1].registros[0]["descricao"] = "adulterado"
        c.blocos[1].minerar()
        for i in range(2, len(c.blocos)):
            c.blocos[i].hash_anterior = c.blocos[i - 1].hash
            c.blocos[i].minerar()
        self.assertTrue(c.validar())

    def test_nao_adiciona_em_cadeia_invalida(self):
        c = cadeia()
        c.blocos[1].nonce += 1
        with self.assertRaises(ValueError):
            c.adicionar_bloco([reg(9)])

    def test_validar_nao_conserta(self):
        c = cadeia()
        c.blocos[1].registros[0]["descricao"] = "x"
        antes = copy.deepcopy(c.blocos)
        self.assertFalse(c.validar())
        self.assertEqual(antes, c.blocos)

    def test_entradas_copiadas(self):
        c = Blockchain(1)
        regs = [reg()]
        c.adicionar_bloco(regs, timestamp=1)
        regs[0]["descricao"] = "mudou depois"
        regs.append(reg(2))
        self.assertEqual(len(c.ultimo_bloco.registros), 1)
        self.assertNotEqual(c.ultimo_bloco.registros[0]["descricao"], "mudou depois")
        self.assertTrue(c.validar())

    def test_registros_invalidos_na_inclusao(self):
        c = Blockchain(1)
        for ruim in ([], [{"tipo": "a"}], [{"tipo": "", "participante": "a", "descricao": "b"}], "x"):
            with self.subTest(ruim=ruim):
                with self.assertRaises((ValueError, TypeError)):
                    c.adicionar_bloco(ruim)
        self.assertEqual(len(c.blocos), 1)

    def test_timestamp_injetado_reproduzivel(self):
        h = []
        for _ in range(2):
            c = Blockchain(1)
            c.adicionar_bloco([reg()], timestamp=123)
            h.append(c.ultimo_bloco.hash)
        self.assertEqual(h[0], h[1])


class TestDiagnostico(unittest.TestCase):
    def test_cadeia_integra_sem_problemas(self):
        self.assertEqual(cadeia().diagnosticar(), [])

    def test_aponta_bloco_e_motivo(self):
        c = cadeia()
        c.blocos[1].registros[0]["descricao"] = "x"
        c.blocos[1].minerar()
        p = c.diagnosticar()
        self.assertEqual(len(p), 1)
        self.assertIn("bloco 2", p[0])
        self.assertIn("hash_anterior", p[0])

    def test_registro_adulterado_aponta_hash(self):
        c = cadeia()
        c.blocos[1].registros[0]["descricao"] = "x"
        self.assertTrue(any("bloco 1" in m and "hash armazenado" in m for m in c.diagnosticar()))

    def test_cadeia_vazia(self):
        c = cadeia()
        c.blocos.clear()
        self.assertFalse(c.validar())
        self.assertEqual(c.diagnosticar(), ["cadeia vazia"])


if __name__ == "__main__":
    unittest.main()

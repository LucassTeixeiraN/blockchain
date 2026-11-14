"""Demonstração obrigatória: gênese + 3 blocos, ataque controlado,
comparação de dificuldades e execução dos testes."""
import subprocess
import sys
import time

from blockchain import Bloco, Blockchain, criar_registro


def titulo(t):
    print(f"\n=== {t} ===")


def resumo(c):
    for b in c.blocos:
        print(f"  #{b.indice} nonce={b.nonce:<6} ant={b.hash_anterior[:10]}.. hash={b.hash[:10]}..")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    titulo("1. Criar gênese e três blocos (dificuldade 2)")
    c = Blockchain(dificuldade=2)
    eventos = [
        ("certificado", "aluno-017", "Certificado de Introdução à Criptografia"),
        ("conclusao", "aluno-021", "Conclusão da disciplina de Redes"),
        ("certificado", "aluno-033", "Certificado de Estruturas de Dados"),
    ]
    for i, (t, p, d) in enumerate(eventos, 1):
        c.adicionar_bloco([criar_registro(t, p, d)], timestamp=1_700_000_000 + i)
    resumo(c)

    titulo("2. Validar a cadeia original")
    print("  válida?", c.validar())

    titulo("3. Adulterar um registro antigo (bloco 1)")
    c.blocos[1].registros[0]["participante"] = "aluno-999"
    print("  válida?", c.validar(), "(esperado: False)")
    for p in c.diagnosticar():
        print("  diagnóstico:", p)

    titulo("4. Reminerar SOMENTE o bloco alterado")
    c.blocos[1].minerar()
    print("  hash do bloco 1 agora é coerente, mas o bloco 2 aponta para o hash antigo")
    print("  válida?", c.validar(), "(esperado: False)")
    for p in c.diagnosticar():
        print("  diagnóstico:", p)

    titulo("5. Reconstruir todos os elos posteriores")
    for i in range(2, len(c.blocos)):
        c.blocos[i].hash_anterior = c.blocos[i - 1].hash
        c.blocos[i].minerar()
    resumo(c)
    print("  válida?", c.validar(), "(esperado: True)")
    print("  => Quem controla a única cópia reescreve o histórico sem ser notado.")
    print("     Sem cópias independentes (âncora externa) e consenso, não há")
    print("     imutabilidade; apenas evidência de adulteração em cópias isoladas.")

    titulo("6. Comparar dificuldades (média de 5 minerações por nível)")
    for d in (1, 2, 3):
        tentativas, t0 = 0, time.perf_counter()
        for k in range(5):
            b = Bloco(1, k, [criar_registro("t", "aluno-001", f"amostra {k}")], "0" * 64, d)
            tentativas += b.minerar()
        dt = time.perf_counter() - t0
        print(f"  dificuldade {d}: média {tentativas / 5:8.1f} tentativas, {dt:.3f}s no total")

    titulo("7. Executar os testes")
    subprocess.run([sys.executable, "-m", "unittest", "-v"])

    titulo("8. Por que isto não é uma blockchain distribuída segura")
    print("  Um único processo/arquivo decide qual cadeia é válida: não há nós,")
    print("  rede P2P, consenso, identidade/assinatura nem custo econômico de reescrita.")
    print("  Dificuldade baixa e uso didático: não utilizar em produção.")


if __name__ == "__main__":
    main()

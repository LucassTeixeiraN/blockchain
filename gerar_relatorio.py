"""Gera relatorio.pdf (requer reportlab, apenas para gerar o PDF)."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String

ss = getSampleStyleSheet()
corpo = ParagraphStyle("c", parent=ss["BodyText"], fontSize=10.5, leading=14.5, spaceAfter=6)
h1 = ParagraphStyle("h", parent=ss["Heading2"], fontSize=12.5, spaceBefore=10, spaceAfter=4)

S = []
def P(t): S.append(Paragraph(t, corpo))
def H(t): S.append(Paragraph(t, h1))

S.append(Paragraph("Relatório técnico – Blockchain didática", ss["Title"]))
P("<i>Introdução à Criptografia – Projeto bônus.</i>")
P("<i>Nome: Lucas Gabriel Teixeira do Nascimento - JC3033091</i>")

H("0. Modelo de dados, arquitetura e bibliotecas")
P("Cada bloco tem: <b>indice, timestamp, registros, hash_anterior, nonce, dificuldade e hash</b>. "
  "Um registro é um dicionário fictício com <i>tipo, participante</i> (pseudônimo, ex.: aluno-017) e "
  "<i>descricao</i>, todos textos não vazios. Fluxo: registros → JSON canônico → SHA-256 → "
  "busca do nonce (PoW) → encadeamento e validação.")


def diagrama():
    d = Drawing(480, 78)
    nomes = ["Gênese", "Bloco 1", "Bloco 2", "Bloco 3"]
    sub = ["ant = 64 zeros", "ant = hash(0) | nonce", "ant = hash(1) | nonce", "ant = hash(2) | nonce"]
    for i, (n, s) in enumerate(zip(nomes, sub)):
        x = 4 + i * 120
        d.add(Rect(x, 14, 100, 50, strokeColor=colors.HexColor("#1f4e79"),
                   fillColor=colors.HexColor("#dce9f7"), rx=4, ry=4))
        d.add(String(x + 50, 44, n, textAnchor="middle", fontName="Helvetica-Bold", fontSize=10))
        d.add(String(x + 50, 26, s, textAnchor="middle", fontSize=6.5))
        if i < 3:
            d.add(Line(x + 100, 39, x + 120, 39, strokeColor=colors.black))
            d.add(Polygon([x + 120, 39, x + 114, 42, x + 114, 36], fillColor=colors.black))
    d.add(String(240, 2, "cada bloco guarda o hash do anterior; alterar um elo quebra o seguinte",
                 textAnchor="middle", fontSize=7))
    return d


S.append(diagrama())
S.append(Spacer(1, 6))
lib = [["Biblioteca / função", "Papel no projeto"],
       ["dataclasses.dataclass", "cria a classe Bloco"],
       ["json.dumps (sort_keys, separators, ensure_ascii, allow_nan)", "serialização canônica"],
       ["str.encode('utf-8')", "texto → bytes para o hash"],
       ["hashlib.sha256 / hexdigest", "hash de 64 dígitos hexadecimais"],
       ["time.time / time.perf_counter", "timestamp / duração da mineração"],
       ["str.startswith", "verifica a regra de PoW"],
       ["copy.deepcopy", "evita mutação das entradas"],
       ["unittest", "testes automatizados"]]
lt = Table(lib, colWidths=[8.5*cm, 7.5*cm])
lt.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                        ("FONTSIZE", (0, 0), (-1, -1), 8.5)]))
S.append(lt)

H("1. Quais campos entram no hash e por quê?")
P("Entram <b>indice, timestamp, registros, hash_anterior, nonce e dificuldade</b>; o campo <b>hash</b> "
  "fica de fora, pois ele é o resultado do cálculo (incluí-lo seria circular). Cada campo protegido "
  "torna detectável a sua alteração: os registros são o conteúdo; hash_anterior forma o elo; "
  "indice e timestamp fixam posição e instante declarado; nonce prova o trabalho; dificuldade "
  "impede que um bloco troque a regra sem mudar o hash.")

H("2. Por que a serialização precisa ser canônica?")
P("O SHA-256 recebe bytes. Dois dicionários logicamente iguais, mas com chaves inseridas em ordens "
  "diferentes ou com espaços distintos, gerariam textos diferentes e, portanto, hashes diferentes — "
  "uma cadeia íntegra seria reprovada. Usamos <font face='Courier'>json.dumps(sort_keys=True, "
  "separators=(',',':'), ensure_ascii=False, allow_nan=False)</font> e UTF-8: a mesma estrutura gera "
  "sempre os mesmos bytes, e NaN/infinito (sem representação JSON válida) são rejeitados. A regra é "
  "uma convenção didática, não um padrão universal entre linguagens.")

H("3. O que muda quando a dificuldade aumenta?")
P("Cada zero hexadecimal adicional multiplica por cerca de 16 o número médio de tentativas. Na nossa "
  "demonstração (média de 5 minerações por nível; os valores variam a cada execução):")
t = Table([["Dificuldade", "Tentativas médias (observadas)", "Esperado (16^d)"],
           ["1", "≈ 19", "16"], ["2", "≈ 259", "256"], ["3", "≈ 4.593", "4.096"]],
          colWidths=[3*cm, 6.5*cm, 4*cm])
t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                       ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                       ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
S.append(t); S.append(Spacer(1, 6))
P("A verificação continua barata (um único hash), enquanto a busca cresce exponencialmente: é a "
  "assimetria da prova de trabalho. Dificuldade 4 já tende a ~65 mil tentativas; 6 é limite máximo.")

H("4. Por que recalcular somente o bloco adulterado não conserta a cadeia?")
P("Ao alterar o bloco <i>k</i> e reminerá-lo, seu hash muda. O bloco <i>k+1</i> ainda guarda no campo "
  "hash_anterior o hash antigo; o validador compara os dois e reprova. O defeito só desaparece se "
  "todos os blocos posteriores forem atualizados e reminerados, em cascata. A demonstração e o teste "
  "<i>test_remineracao_parcial_nao_conserta</i> mostram esse comportamento.")

H("5. Como o controlador único reconstrói toda a cadeia?")
P("Quem tem acesso ao arquivo/estrutura pode alterar o registro, reminerar o bloco, atualizar "
  "hash_anterior de cada sucessor e reminerar todos. Com dificuldade baixa o custo é desprezível e a "
  "cadeia volta a ser plenamente válida (etapa 5 da demo). Uma cópia externa confiável (âncora), "
  "como o hash do último bloco guardado fora do controle do atacante, revelaria a reconstrução: o "
  "hash final divergiria do registrado.")

H("6. Quem decide a cadeia válida nesta implementação?")
P("O próprio programa local: <i>validar()</i> aplica regras sobre a única cópia existente. Não há "
  "outra parte para contestar; o controlador do arquivo é a autoridade de fato.")

H("7. O que falta para uma rede distribuída com consenso real?")
P("Múltiplos nós independentes (P2P) mantendo cópias; um protocolo de propagação de blocos; uma regra de "
  "consenso para escolher entre cadeias concorrentes (ex.: maior trabalho acumulado) e custo "
  "econômico/incentivos que tornem a reescrita inviável; identidade e assinaturas digitais para "
  "autoria; gestão e proteção de chaves; modelo de ameaça e análise da implementação. Nada disso "
  "existe aqui.")

H("8. Hash, mineração ou encadeamento escondem o conteúdo?")
P("Não. Os registros ficam em texto claro dentro do bloco; hash é resumo, não cifra, e oferece "
  "integridade, não confidencialidade. Além disso, hash não anonimiza dados previsíveis (nomes, "
  "documentos, notas), que podem ser descobertos por tentativa; por isso usamos apenas pseudônimos "
  "fictícios como <i>aluno-017</i>.")

H("9. Qual problema acadêmico realmente exige blockchain?")
P("Para emitir e verificar certificados, <b>um banco de dados assinado digitalmente</b> costuma ser "
  "mais simples e suficiente: a instituição assina cada registro (ex.: Ed25519), qualquer pessoa "
  "verifica com a chave pública, e o banco pode ter cópias de segurança e logs. Blockchain só se "
  "justificaria se várias instituições que <i>não confiam entre si</i> precisassem manter em conjunto "
  "um histórico compartilhado sem uma autoridade central, aceitando custo, complexidade e "
  "privacidade reduzida. No cenário de uma única universidade emissora, a confiança já é "
  "centralizada, então assinatura + cópias externas resolvem melhor.")

H("Conclusão")
P("Serialização canônica, hash, nonce, encadeamento e validação cooperam para que qualquer alteração "
  "isolada seja <b>detectável</b>. Porém, sem cópias independentes e sem consenso, o dono da cadeia "
  "pode refazê-la inteira: temos evidência de adulteração, não imutabilidade. "
  "Foram implementados 30 testes automatizados, todos aprovados.")

SimpleDocTemplate("relatorio.pdf", pagesize=A4, leftMargin=2.2*cm, rightMargin=2.2*cm,
                  topMargin=2*cm, bottomMargin=2*cm, title="Relatório – Blockchain didática").build(S)


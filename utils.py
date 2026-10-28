import pypdf
import docx 
import unicodedata
import re
import math

def extrair_texto(arquivo):
    """
    Extrai o texto de um arquivo PDF, DOCX ou TXT.
    """

    nome = arquivo.name

    if nome.lower().endswith(".pdf"):
        # Extrair texto de PDF - página por página
        pdf_reader = pypdf.PdfReader(arquivo)
        texto = ""
        for pagina in pdf_reader.pages:
            texto += (pagina.extract_text() or "") + "\n" 

    elif nome.lower().endswith(".docx"):
        # Extrair texto de DOCX - parágrafo por parágrafo
        doc = docx.Document(arquivo)

        texto = "\n".join(paragrafo.text for paragrafo in doc.paragraphs)

        for tabela in doc.tables:
            for linha in tabela.rows:
                celulas = [celula.text.strip() for celula in linha.cells]
                texto += "\n" + " | ".join(celulas)

    elif nome.lower().endswith(".txt"):
        # Extrair texto de TXT - simplesmente ler o conteúdo
        texto = arquivo.getvalue().decode("utf-8")

    else:
        raise ValueError("Formato de arquivo não suportado. Por favor, envie um arquivo PDF, DOCX ou TXT.")

    texto = limpar_texto(texto, juntar_linhas=nome.lower().endswith(".pdf"))

    if not texto.strip():
        return None

    return texto

# Funções de RAG

FIM_DE_FRASE = ".!?…"
FECHAMENTOS = "”\"')]"

def ponto_de_corte(texto, fim, tolerancia):
    """Escolhe onde terminar o pedaço, olhando até a tolerancia de caracteres para trás a partir do fim."""

    limite = fim - tolerancia
    n = len(texto)

    # 1) preferência: terminar no fim de uma frase
    for c in range(fim, limite, -1):
        if c < n and texto[c].isspace():
            anterior = texto[c - 1]
            if anterior in FIM_DE_FRASE or (anterior in FECHAMENTOS and c >= 2 and texto[c - 2] in FIM_DE_FRASE):
                return c

    # 2) senão: terminar no fim de uma palavra
    for c in range(fim, limite, -1):
        if c < n and texto[c].isspace():
            return c

    # 3) sem espaços na janela: corte seco
    return fim

def dividir_chunks(texto, tamanho=1000, sobreposicao=200, tolerancia=150):
    """
    Divide o texto em chunks de tamanho especificado com sobreposicao.
    """

    if tamanho <= 0:
        raise ValueError("O tamanho do chunk deve ser maior que zero.")

    if sobreposicao >= tamanho:
        raise ValueError("A sobreposição deve ser menor que o tamanho do chunk.")
    
    chunks = []
    n = len(texto)
    inicio = 0

    while inicio < n:
        if inicio > 0:
            limite = min(inicio + tolerancia, n)
            c = inicio

            while c < limite and not texto[c - 1].isspace():
                c += 1
            if c < limite or (c == limite and texto[c-1].isspace()):
                inicio = c

        fim = min(inicio + tamanho, n)

        if fim < n:
            fim = ponto_de_corte(texto, fim, tolerancia)

        pedaco = texto[inicio:fim]
        
        if pedaco.strip():
            chunks.append(pedaco)

        if fim >= n:
            break

        inicio = max(fim - sobreposicao, inicio + 1)

    return chunks

STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
    "por", "para", "com", "sem", "sobre", "entre", "ate",
    "e", "ou", "mas", "que", "se", "como", "quando",
    "qual", "quais", "quem", "onde", "quanto", "quantos", "quantas",
    "foi", "foram", "ser", "sao", "era", "esta", "estao",
    "ao", "aos", "pelo", "pela", "isso", "esse", "essa",
    "este", "ha", "livro", "fazer", "autor", "texto", "documento",
    "menciona", "primeiro", "primeira", "segundo", "segunda", "terceiro",
    "terceira", "quarto", "quarta", "quinto", "quinta","explique",
    "melhor", "detalhe", "detalhes", "continue",
}

def normalizar(texto):
    texto = remover_acentos(texto)
    palavras = re.findall(r"\w+", texto)
    return [p for p in palavras if p not in STOPWORDS]


def buscar_trechos(pergunta, chunks_por_doc, nomes_ativos, k=6):
    palavras_pergunta = set(normalizar(pergunta))

    # 1) lista de candidatos: (nome, pedaço, palavras do pedaço)
    candidatos = []
    for nome in nomes_ativos:
        for pedaco in chunks_por_doc.get(nome, []):
            candidatos.append((nome, pedaco, set(normalizar(pedaco))))

    N = len(candidatos)

    # 2) df: em quantos pedaços cada palavra da pergunta aparece
    df = {p: sum(1 for _, _, palavras in candidatos if p in palavras)
          for p in palavras_pergunta}

    # 3) nota = soma dos pesos das palavras que casaram
    resultados = []
    for nome, pedaco, palavras in candidatos:
        em_comum = palavras_pergunta & palavras
        nota = sum(math.log(1 + N / df[p]) for p in em_comum)   # lacuna 1: soma de math.log(N / df[p]) para cada p em comum
        if nota > 0:
            resultados.append((nota, nome, pedaco))

    resultados = sorted(resultados, reverse=True, key=lambda r: r[0])   # lacuna 2: a mesma ordenação de antes
    return resultados[:k]

GATILHOS_GENERICOS = [
    "resum", "sintetiz", "visao geral", "sobre o que", "do que se trata",
    "principais pontos", "ideias principais", "tema central", "pontos chave",
    "quiz", "flashcard", "questoes", "multipla escolha", "me teste",
    "teste meu conhecimento", "explique o documento", "explique o texto",
    "explique o artigo",
]

def remover_acentos(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))

def pedido_generico(pergunta):
    pergunta_limpa = remover_acentos(pergunta)
    return any(g in pergunta_limpa for g in GATILHOS_GENERICOS)


def amostrar_trechos(chunks_por_doc, nomes_ativos, total=6):
    if not nomes_ativos:
        return []

    por_doc = max(1, total // len(nomes_ativos))
    resultados = []

    for nome in nomes_ativos:
        pedacos = chunks_por_doc.get(nome, [])
        tamanho = len(pedacos)

        if tamanho <= por_doc:
            indices = range(tamanho)
        elif por_doc == 1:
            indices = [0]
        else:
            indices = [int(i * (tamanho - 1) / (por_doc - 1)) for i in range(por_doc)]

        for i in indices:
            resultados.append((0, nome, pedacos[i]))

    return resultados

REFERENCIAS = {
    "primeiro", "primeira", "segundo", "segunda", "terceiro", "terceira",
    "quarto", "quarta", "quinto", "quinta", "anterior", "isso", "essa", "esse", "continue",
}
FRASES_ACOMPANHAMENTO = ["explique melhor", "mais detalhes", "detalhe melhor", "pode explicar"]

def pergunta_de_acompanhamento(pergunta, max_palavras=5):
    limpa = remover_acentos(pergunta)
    palavras = re.findall(r"\w+", limpa)

    if len(palavras) > max_palavras:
        return False

    return any(p in REFERENCIAS for p in palavras) or any(f in limpa for f in FRASES_ACOMPANHAMENTO)


def montar_consulta(pergunta, mensagens):
    """Para acompanhamentos, junta a última pergunta com assunto à consulta da busca."""
    if not pergunta_de_acompanhamento(pergunta):
        return pergunta

    for msg in reversed(mensagens):
        if (msg["role"] == "user"
                and not pergunta_de_acompanhamento(msg["content"])
                and normalizar(msg["content"])):
            return msg["content"] + " " + pergunta

    return pergunta

def limpar_texto(texto, juntar_linhas=False):
    """
    Limpa ruídos de formatação.
    - juntar_linhas=False (txt, docx): mantém as quebras de linha, só tira excessos.
    - juntar_linhas=True (pdf): junta tudo em um fluxo contínuo de texto.
    """
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")

    if juntar_linhas:
        texto = re.sub(r"(\w)-\n(\w)", r"\1\2", texto)   # palavra quebrada por hífen no fim da linha
        texto = re.sub(r"\s+", " ", texto)               # qualquer sequência de espaços/quebras vira um espaço
    else:
        texto = re.sub(r"[ \t]+", " ", texto)            # espaços repetidos
        texto = re.sub(r"\n{3,}", "\n\n", texto)         # 3+ quebras viram 2

    return texto.strip()

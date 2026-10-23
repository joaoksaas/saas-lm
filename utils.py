import pypdf
import docx 
import unicodedata
import re

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

    if not texto.strip():
        return None

    return texto

# Funções de RAG

def dividir_chunks(texto, tamanho=1000, sobreposicao=200):
    """
    Divide o texto em chunks de tamanho especificado com sobreposicao.
    """

    if tamanho <= 0:
        raise ValueError("O tamanho do chunk deve ser maior que zero.")

    if sobreposicao >= tamanho:
        raise ValueError("A sobreposição deve ser menor que o tamanho do chunk.")
    
    passo = tamanho - sobreposicao

    chunks = []

    for inicio in range(0, len(texto), passo):
        pedaco = texto[inicio:inicio + tamanho]

        if pedaco.strip():
            chunks.append(pedaco)

        if inicio + tamanho >= len(texto):
            break

    return chunks

STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
    "por", "para", "com", "sem", "sobre", "entre", "ate",
    "e", "ou", "mas", "que", "se", "como", "quando",
    "qual", "quais", "quem", "onde", "quanto", "quantos", "quantas",
    "foi", "foram", "ser", "sao", "era", "esta", "estao",
    "ao", "aos", "pelo", "pela", "isso", "esse", "essa", "este", "ha",
}

def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    palavras = re.findall(r"\w+", texto)

    return [p for p in palavras if p not in STOPWORDS]
    
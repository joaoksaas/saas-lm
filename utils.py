import pypdf
import docx 

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
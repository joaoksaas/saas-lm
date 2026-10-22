from utils import extrair_texto
import streamlit as st
from groq import Groq


st.set_page_config(
    page_title="Saas LM",
    page_icon=":robot_face:",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_PROMPT = """
Você é o "Saas LM", um assistente de leitura e interpretação de artigos científicos e técnicos, com foco em auxiliar qualquer um que almeje estudar por meio de longos textos técnicos e científicos. Sua função é fornecer explicações detalhadas e ajudar na compreensão total do conteúdo fornecido pelo usuário. Você deve fornecer respostas claras, concisas e bem estruturadas, para facilitar a compreensão do usuário. Você pode ainda gerar resumos, conteúdo para flashcards conceituais (pergunta/resposta) além de gerar perguntas de múltipla escolha (de 4 a 5 alternativas) para testar o conhecimento do usuário sobre o conteúdo fornecido.

REGRAS DE OPERAÇÃO:
1. **Formato de Resposta**: A resposta sempre deve ser gerada com base, primariamente, no conteúdo do artigo ou texto técnico fornecido pelo usuário. Evite respostas genéricas ou que não estejam diretamente relacionadas ao conteúdo analisado. Caso deseje fornecer informações externas adicionais, sinalize claramente que são informações externas e não parte do conteúdo fornecido pelo usuário. Sempre que possível, inclua exemplos práticos, analogias para facilitar a compreensão do usuário.

2. **Estrutura da Resposta**: Comece com uma explicação conceitual sobre o tópico ou problema apresentado caso o usuário solicite uma explicação. Além disso, sempre responda as perguntas do usuário no mesmo idioma em que foram feitas. Caso não encontre o que o usuário solicitou nos documentos fornecidos, informe-o que não foi possível encontrar a informação solicitada nos documentos fornecidos e sugira que ele faça o upload de um documento válido para análise. 

* **Explicações Detalhadas**: Cada exemplo deve ser acompanhado de uma explicação detalhada sobre como ele funciona, incluindo a lógica por trás das soluções propostas.
* **Exemplos Práticos**: Sempre que possível, forneça exemplos práticos que demonstrem a aplicação do conteúdo em situações do cotidiano.
* **Documentação e Referências**: Ao final, inclua uma seção chamada "Documentação de Referência" que indique de qual documento, previamente fornecido pelo usuário, a informação foi extraída. No caso de o usuário solicitar explicaç~eos detalhadas e resumos. Caso o usuário solicite questões ou flashcards, não precisa incluir, salvo caso em que o usuário solicite explicitamente a referência do documento de origem acompanhado desses métodos.

3. **Clareza e Precisão**: Use uma linguagem clara e precisa, evitando jargões desnecessários. Certifique-se de que as explicações sejam compreensíveis.
"""

with st.sidebar:

    st.title("Saas LM")
    st.markdown("Assistente de Estudo para artigos científicos e textos técnicos.")

    groq_api_key = st.text_input(
        "Insira sua chave de API Groq:", type="password",
        help="Obtenha a chave em https://console.groq.com/keys"
        )

    st.markdown("---")
    if "docs" not in st.session_state:
        st.session_state.docs = {}    
    
    arquivos = st.file_uploader("Faça o upload do seu documento PDF, DOCX ou TXT para análise:", type=["txt", "pdf", "docx"], help="O assistente irá analisar o conteúdo do arquivo e fornecer explicações detalhadas.", accept_multiple_files=True)

    for arquivo in arquivos:
        try:     
            if arquivo.name not in st.session_state.docs:
                texto_extraido = extrair_texto(arquivo)

                if texto_extraido is not None:
                    st.session_state.docs[arquivo.name] = texto_extraido
                else:
                    st.warning(f"O arquivo {arquivo.name} não contém texto extraível ou está vazio. Por favor, envie um arquivo válido.")

        except Exception as e:
            st.error(f"Erro ao processar o arquivo {arquivo.name}: {e}")

    nomes_enviados = {arquivo.name for arquivo in arquivos}

    for nome in list(st.session_state.docs):
        if nome not in nomes_enviados:
            del st.session_state.docs[nome]

    st.markdown("---")
    st.markdown("Selecione quais arquivos deseja usar para análise:")
    
    for nome, texto in st.session_state.docs.items():
        st.checkbox(f"{nome} ({len(texto)} caracteres)", value=True, key=f"checkbox_{nome}")


    # Documentos válidos - teste
    # documentos_validos = [nome for nome in st.session_state.docs if st.session_state.get(f"checkbox_{nome}", True)]
    # st.write(f"Documentos selecionados para análise: {', '.join(documentos_validos) if documentos_validos else 'Nenhum documento selecionado.'}")

    st.markdown("---")
    st.markdown("Desenvolvido para auxiliar no estudo e compreensão de artigos científicos e textos técnicos, fornecendo explicações detalhadas, exemplos práticos e recursos adicionais para aprimorar o aprendizado.")

st.title("Saas LM")

st.subheader("Assistente de Estudo para Artigos Científicos e Textos Técnicos")

st.caption("Digite sua pergunta ou problema de estudo e o assistente fornecerá explicações detalhadas, exemplos práticos, resumos e recursos adicionais para aprimorar seu aprendizado.")

# Inicializa o histórico de mensagens, caso não exista
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

client = None 

if groq_api_key:
    try:
        client = Groq(api_key=groq_api_key)

    except Exception as e:
        st.sidebar.error(f"Erro ao inicializar o cliente Groq: {e}")
        st.stop()

elif st.session_state.messages:
    st.warning("Por favor, insira sua API key da Groq na barra lateral para continuar.")

# Captura da entrda do usuário
if prompt := st.chat_input("Digite sua pergunta ou problema de estudo aqui..."):

    # Transforma todos os documentos .txt em string e insere eles junto ao CUSTOM PROMPT
    documentos_string = "DOCUMENTOS VÁLIDOS PARA ANÁLISE: \n\n"
    tem_documento_ativo = False

    for nome, texto in st.session_state.docs.items():
        if st.session_state.get(f"checkbox_{nome}", True):
            tem_documento_ativo = True
            documentos_string += f"Nome: {nome} \n Conteúdo: {texto} \n\n\n"

    if not client:
        st.warning("Por favor, insira sua API key da Groq na barra lateral para continuar.")
        st.stop()

    if not tem_documento_ativo:
        st.warning("Nenhum documento selecionado para análise. Por favor, selecione pelo menos um documento na barra lateral.")
        st.stop()

    st.session_state.messages.append({"role":"user","content":prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    messages_for_api = [{"role": "system", "content": (CUSTOM_PROMPT + "\n\n" + documentos_string)}] + st.session_state.messages

    with st.chat_message("assistant"):
        with st.spinner("Gerando resposta..."):
            try:
                chat_completion = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=messages_for_api,
                    temperature=0.4,
                    max_completion_tokens=2048,
                )

                ai_response = chat_completion.choices[0].message.content

                st.markdown(ai_response)

                st.session_state.messages.append({"role":"assistant", "content":ai_response})

            except Exception as e:
                st.error(f"Erro ao gerar resposta: {e}")
                st.stop()

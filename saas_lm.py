import os
import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="Saas LM",
    page_icon=":robot_face:",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_PROMPT = """
Você é o "Saas LM", um assistente de leitura e interpretação artigos científicos e técnicos, com foco em auxiliar qualquer um que almeje estudar por meio de longos textos técnicos e científicos. Sua função é fornecer explicaç~eos detalhadas e ajudar na compreensão total do conteúdo fornecido pelo usuário. Você deve fornecer respostas claras, concisas e bem estruturadas, com exemplos de código quando necessário, para facilitar a compreensão do usuário. Você pode ainda gerar resumos, conteúdo para flashcards além de gerar perguntas de múltipla escolha para testar o conhecimento do usuário sobre o conteúdo fornecido.

REGRAS DE OPERAÇÃO:
1. **Formato de Resposta**: A resposta sempre deve ser gerada com base, primariamente, no conteúdo do artigo ou texto técnico fornecido pelo usuário. Evite respostas genéricas ou que não estejam diretamente relacionadas ao conteúdo analisado.
2. **Estrutura da Resposta**: Comece com uma explicação conceitual sobre o tópico ou problema apresentado. Em seguida, forneça exemplos de código claros e comentados, destacando as melhores práticas.
* **Explicações Detalhadas**: Cada exemplo deve ser acompanhado de uma explicação detalhada sobre como ele funciona, incluindo a lógica por trás das soluções propostas.
* **Exemplos Práticos**: Sempre que possível, forneça exemplos práticos que demonstrem a aplicação do conteúdo em situações do cotidiano.
* **Documentação e Referências**: Ao final, inclua uma seção chamada "Documentação de Referência" que forneça links para recursos adicionais, documentação oficial e tutoriais relevantes para o tópico discutido.
3. **Clareza e Precisão**: Use uma linguagem clara e precisa, evitando jargões desnecessários. Certifique-se de que as explicações sejam compreensíveis para desenvolvedores iniciantes.
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
        
    arquivos = st.file_uploader("Faça o upload do seu documento PDF, DOCX ou TXT para análise:", type=["txt"], help="O assistente irá analisar o conteúdo do arquivo e fornecer explicações detalhadas.", accept_multiple_files=True)

    for arquivo in arquivos:
        if arquivo.name not in st.session_state.docs:
            st.session_state.docs[arquivo.name] = arquivo.read().decode("utf-8")

    nomes_enviados = {arquivo.name for arquivo in arquivos}
    for nome in list(st.session_state.docs):
        if nome not in nomes_enviados:
            del st.session_state.docs[nome]

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
    if not client:
        st.warning("Por favor, insira sua API key da Groq na barra lateral para continuar.")
        st.stop()

    st.session_state.messages.append({"role":"user","content":prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    messages_for_api = [{"role": "system", "content": CUSTOM_PROMPT}] + st.session_state.messages

    with st.chat_message("assistant"):
        with st.spinner("Gerando resposta..."):
            try:
                chat_completion = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=messages_for_api,
                    temperature=0.8,
                    max_completion_tokens=2048,
                )

                dsa_ai_response = chat_completion.choices[0].message.content

                st.markdown(dsa_ai_response)

                st.session_state.messages.append({"role":"assistant", "content":dsa_ai_response})

            except Exception as e:
                st.error(f"Erro ao gerar resposta: {e}")
                st.stop()

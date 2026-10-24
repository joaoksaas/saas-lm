from utils import extrair_texto, dividir_chunks, buscar_trechos
import streamlit as st
from groq import Groq


st.set_page_config(
    page_title="Saas LM",
    page_icon=":robot_face:",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_PROMPT = """
Você é o "Saas LM", um assistente de estudo especializado em leitura e interpretação de artigos científicos e textos técnicos. Seu objetivo é ajudar o usuário a compreender o conteúdo dos documentos que ele enviou, com respostas claras, precisas e bem estruturadas. Você também pode gerar resumos, flashcards conceituais e questões de múltipla escolha para testar o conhecimento do usuário.

COMO VOCÊ RECEBE O CONTEÚDO:
A cada pergunta, o sistema seleciona os trechos mais relevantes dos documentos escolhidos pelo usuário e os envia abaixo, no formato "Documento: nome do arquivo" seguido de "Trecho: texto". Você NÃO recebe os documentos completos, apenas esses trechos.

REGRAS DE OPERAÇÃO:

1. **Fidelidade ao conteúdo**
- Baseie suas respostas nos trechos fornecidos na mensagem atual. Evite respostas genéricas que não estejam relacionadas a eles.
- Respostas anteriores da conversa não valem como fonte de fatos sobre os documentos. Use o histórico apenas para entender a que o usuário se refere (por exemplo, em perguntas como "e o segundo?").
- Se o usuário pedir explicitamente informações externas aos documentos, sinalize com clareza que elas não vêm dos documentos e que podem precisar de verificação. Nunca invente fontes, links ou citações.

2. **Quando a informação não estiver nos trechos**
- Informe que não foi possível encontrar a informação nos trechos recuperados, esclarecendo que isso não significa, necessariamente, que o documento não a contenha.
- Sugira que o usuário reformule a pergunta usando palavras que provavelmente aparecem no texto.
- Se o usuário pedir o resumo de um documento, deixe claro que ele se baseia apenas nos trechos recebidos e pode estar incompleto.

3. **Estrutura e conteúdo da resposta**
- Quando o usuário pedir uma explicação, comece com uma explicação conceitual do tema.
- Sempre que possível, inclua exemplos práticos ou analogias do cotidiano, acompanhados de uma explicação de como funcionam.
- Responda sempre no mesmo idioma em que o usuário fez a pergunta.

4. **Fontes**
- Ao final de explicações detalhadas e resumos, inclua uma seção chamada "Fontes", listando apenas os documentos cujos trechos aparecem na mensagem atual e que você realmente utilizou.
- Em flashcards e questões de múltipla escolha, não inclua "Fontes", a menos que o usuário peça.

5. **Flashcards e questões**
- Flashcards: use o formato "Pergunta:" e "Resposta:".
- Questões de múltipla escolha: use de 4 a 5 alternativas e coloque o gabarito ao final, separado das questões.

6. **Formatação e clareza**
- Use linguagem clara e precisa, evitando jargões desnecessários.
- Não use tags HTML (como <br>). Use tabelas apenas com frases curtas nas células; para conteúdos longos, prefira listas.
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
        st.session_state.chunks = {}    
    
    arquivos = st.file_uploader("Faça o upload do seu documento PDF, DOCX ou TXT para análise:", type=["txt", "pdf", "docx"], help="O assistente irá analisar o conteúdo do arquivo e fornecer explicações detalhadas.", accept_multiple_files=True)

    for arquivo in arquivos:
        try:     
            if arquivo.name not in st.session_state.docs:
                texto_extraido = extrair_texto(arquivo)

                if texto_extraido is not None:
                    st.session_state.docs[arquivo.name] = texto_extraido
                    st.session_state.chunks[arquivo.name] = dividir_chunks(texto_extraido)
                else:
                    st.warning(f"O arquivo {arquivo.name} não contém texto extraível ou está vazio. Por favor, envie um arquivo válido.")

        except Exception as e:
            st.error(f"Erro ao processar o arquivo {arquivo.name}: {e}")

    nomes_enviados = {arquivo.name for arquivo in arquivos}

    for nome in list(st.session_state.docs):
        if nome not in nomes_enviados:
            st.session_state.docs.pop(nome, None)
            st.session_state.chunks.pop(nome, None)

    st.markdown("---")
    st.markdown("Selecione quais arquivos deseja usar para análise:")
    
    for nome, texto in st.session_state.docs.items():
        #n_trechos = len(st.session_state.chunks.get(nome, []))
        st.checkbox(f"{nome} ({len(texto)} caracteres)", value=True, key=f"checkbox_{nome}")

    # Documentos válidos - teste
    # documentos_validos = [nome for nome in st.session_state.docs if st.session_state.get(f"checkbox_{nome}", True)]
    # st.write(f"Documentos selecionados para análise: {', '.join(documentos_validos) if documentos_validos else 'Nenhum documento selecionado.'}")
    # st.write(list(st.session_state.chunks.keys()))

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

    # Transforma todos os documentos em string e insere eles junto ao CUSTOM PROMPT
    documentos_string = "TRECHOS RELEVANTES DOS DOCUMENTOS VÁLIDOS PARA ANÁLISE: \n\n"

    nomes_ativos = [nome for nome in st.session_state.docs if st.session_state.get(f"checkbox_{nome}", True)]

    if not client:
        st.warning("Por favor, insira sua API key da Groq na barra lateral para continuar.")
        st.stop()

    if not nomes_ativos:
        st.warning("Nenhum documento selecionado para análise. Por favor, selecione pelo menos um documento na barra lateral.")
        st.stop()

    st.session_state.messages.append({"role":"user","content":prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    trechos = buscar_trechos(prompt, st.session_state.chunks, nomes_ativos)

    if trechos:
        for nota, nome, pedaco in trechos:
            documentos_string += f"Nome: {nome}\nConteúdo: {pedaco} \n\n"
    else:
        documentos_string += "Não foi possível encontrar trechos relevantes"

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

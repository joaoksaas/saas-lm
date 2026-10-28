from utils import extrair_texto, dividir_chunks, buscar_trechos, pedido_generico, amostrar_trechos, montar_consulta, normalizar
import streamlit as st
from groq import Groq, RateLimitError, AuthenticationError, APIConnectionError, APIStatusError


st.set_page_config(
    page_title="Saas LM",
    page_icon=":robot_face:",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_PROMPT = """
Você é o "Saas LM", um assistente de estudo especializado em leitura e interpretação de artigos científicos e textos técnicos. Seu objetivo é ajudar o usuário a compreender o conteúdo dos documentos que ele carregou, com respostas claras, precisas e bem estruturadas. Você também pode gerar resumos, flashcards conceituais e questões de múltipla escolha para testar o conhecimento do usuário.

COMO VOCÊ RECEBE O CONTEÚDO:
A cada pergunta, o sistema seleciona automaticamente trechos dos documentos escolhidos pelo usuário e os apresenta ao final desta mensagem, no formato "Documento: nome do arquivo" seguido de "Trecho: texto". Esses são os "trechos recuperados". Você NÃO recebe os documentos completos. O usuário carrega os documentos, mas não escolhe os trechos: nunca diga que ele os enviou.
O cabeçalho que precede os trechos indica como eles foram obtidos:
- "mais relevantes para a pergunta": escolhidos pelas palavras da pergunta;
- "amostrados": espalhados ao longo de cada documento, sem relação com a pergunta (usado em pedidos de resumo, visão geral e quiz).

REGRAS DE OPERAÇÃO:

1. **Fidelidade aos documentos**
- Responda exclusivamente com base nos trechos recuperados na mensagem atual. Não use conhecimento externo, mesmo que o usuário peça, e não ofereça informações de fora dos documentos por iniciativa própria. Se o usuário pedir algo que exija conhecimento externo, explique que este assistente responde apenas com base nos documentos selecionados e que essa informação deve ser buscada em outra fonte.
- Respostas anteriores da conversa não valem como fonte de fatos. Use o histórico apenas para entender a que o usuário se refere (por exemplo, em "e o segundo?").
- Nunca invente fontes, links, citações ou nomes.

2. **Quando a informação não estiver nos trechos**
- Diga que não foi possível encontrar a informação nos trechos recuperados. Nunca afirme que o documento "não menciona", "não contém" ou "não trata" de algo, porque você viu apenas parte dele.
- Sugira que o usuário reformule a pergunta usando palavras que provavelmente aparecem no texto.
- Em resumos e visões gerais, avise que o resultado se baseia apenas nos trechos recuperados e pode estar incompleto.

3. **Estrutura e conteúdo da resposta**
- Responda no mesmo idioma da pergunta.
- Quando o usuário pedir uma explicação, comece pelo conceito e, sempre que possível, ilustre com exemplos ou analogias do cotidiano, explicando como funcionam.
- Use linguagem clara e precisa, evitando jargões desnecessários.

4. **Fontes**
- Ao final de explicações detalhadas e resumos, inclua uma seção "Fontes" com o nome dos documentos cujos trechos você realmente utilizou.
- Em flashcards e questões de múltipla escolha, não inclua "Fontes", a menos que o usuário peça.

5. **Flashcards e questões**
- Flashcards: use o formato "Pergunta:" e "Resposta:".
- Questões de múltipla escolha: 4 a 5 alternativas, com o gabarito ao final, separado das questões.

6. **Formatação (importante)**
- A interface exibe apenas Markdown puro. Qualquer tag HTML (como as de quebra de linha) aparece como texto literal e estraga a leitura. Nunca use tags HTML.
- Para organizar informação, prefira parágrafos curtos e listas em Markdown (com "-" ou numeração).
- Use tabelas somente para comparar itens, com frases curtas e uma única linha de texto por célula. Se precisar listar vários pontos sobre um item, faça uma lista fora da tabela.
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

    with st.expander("Avançado"):
       modo_debug = st.checkbox(
           "Modo debug (mostra notas e palavras da busca)",
           value=False,
           key="modo_debug",
       )

st.title("Saas LM")

st.subheader("Assistente de Estudo para Artigos Científicos e Textos Técnicos")

st.caption("Digite sua pergunta ou problema de estudo e o assistente fornecerá explicações detalhadas, exemplos práticos, resumos e recursos adicionais para aprimorar seu aprendizado.")

def mostrar_trechos(trechos, amostrados=False):
        with st.expander(f"Ver trechos consultados pela IA ({len(trechos)})"):
            if amostrados:
                st.caption("Trechos amostrados dos documentos (não escolhidos pela pergunta).")
            for i, (nome, pedaco) in enumerate(trechos, start=1):
                st.caption(f"{i}. {nome}")
                st.text(" ".join(pedaco.split()))

# Inicializa o histórico de mensagens, caso não exista
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("trechos"):
            mostrar_trechos(message["trechos"], message.get("amostrados", False))

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

    nomes_ativos = [nome for nome in st.session_state.docs if st.session_state.get(f"checkbox_{nome}", True)]

    if not client:
        st.warning("Por favor, insira sua API key da Groq na barra lateral para continuar.")
        st.stop()

    if not nomes_ativos:
        st.warning("Nenhum documento selecionado para análise. Por favor, selecione pelo menos um documento na barra lateral.")
        st.stop()

    consulta = montar_consulta(prompt, st.session_state.messages)

    usou_amostra = pedido_generico(prompt) or not normalizar(consulta)        

    if usou_amostra:
        trechos = amostrar_trechos(st.session_state.chunks, nomes_ativos)
        documentos_string = (
            "TRECHOS AMOSTRADOS DOS DOCUMENTOS SELECIONADOS"
            "(espalhados ao longo de cada documento, não escolhidos pela pergunta):\n\n"
        )
        
    else:
        trechos = buscar_trechos(consulta, st.session_state.chunks, nomes_ativos)  
        documentos_string = "TRECHOS DOS DOCUMENTOS SELECIONADOS MAIS RELEVANTES PARA A PERGUNTA:\n\n"

    trechos_usados = [(nome, pedaco) for _, nome, pedaco in trechos]

    with st.chat_message("user"):
        st.markdown(prompt)

    if modo_debug:
        palavras_pergunta = set(normalizar(consulta))
        with st.expander("Trechos enviados à IA (debug)"):
            for nota, nome, pedaco in trechos:
                casadas = palavras_pergunta & set(normalizar(pedaco))
                st.caption(f"nota {nota} | casaram: {', '.join(sorted(casadas))}")
                st.text(pedaco)


    if trechos:
        for _, nome, pedaco in trechos:
            documentos_string += f"Nome: {nome}\nConteúdo: {pedaco} \n\n"
    else:
        documentos_string += "Não foi possível encontrar trechos relevantes"


    st.session_state.messages.append({"role":"user","content":prompt})

    historico = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-7:]] # Últimas 4 (incluindo a atual) perguntas e 3 respostas

    messages_for_api = [{"role": "system", "content": (CUSTOM_PROMPT + "\n\n" + documentos_string)}] + historico

    with st.chat_message("assistant"):
        mensagem_erro = None

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

                if trechos_usados:
                    mostrar_trechos(trechos_usados, usou_amostra)

                st.session_state.messages.append({
                    "role":"assistant",
                    "content":ai_response,
                    "trechos": trechos_usados,
                    "amostrados": usou_amostra
                })


            except RateLimitError:
                mensagem_erro = "Limite de uso da Groq atingido (requisições ou tokens por minuto). Aguarde cerca de um minuto e tente novamente."
            except AuthenticationError:
                mensagem_erro = "Chave de API inválida. Confira a chave inserida na barra lateral."
            except APIConnectionError:
                mensagem_erro = "Não foi possível conectar ao serviço da Groq. Verifique sua conexão e tente novamente."
            except APIStatusError as e:
                if e.status_code == 413:
                    mensagem_erro = "A requisição ficou grande demais para o limite do modelo. Tente uma pergunta mais curta ou desmarque alguns documentos."
                else:
                    mensagem_erro = f"Erro da API da Groq (código {e.status_code}). Tente novamente em instantes."
            except Exception as e:
                mensagem_erro = f"Erro ao gerar resposta: {e}"

        if mensagem_erro:
            st.session_state.messages.pop()
            st.error(mensagem_erro)
            st.stop()

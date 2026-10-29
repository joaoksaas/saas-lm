# Saas LM

Assistente de estudo para conversar com seus próprios textos e artigos, no estilo NotebookLM. Você carrega documentos (PDF, DOCX ou TXT), escolhe quais usar e faz perguntas, pede resumos, flashcards e questões de múltipla escolha. As respostas se baseiam **apenas** nos documentos selecionados.

Projeto de estudo, desenvolvido a partir de um exercício do curso Fundamentos de Linguagem Python da Data Science Academy (DSA).

🔗 **Demo:** [Saas LM](https://saas-lm.streamlit.app/)

## Funcionalidades

- Upload de vários arquivos PDF, DOCX e TXT
- Seleção de quais arquivos entram na conversa (checkboxes na barra lateral)
- Chat com respostas baseadas nos documentos (modo estrito: sem conhecimento externo)
- Resumos, flashcards (pergunta/resposta) e questões de múltipla escolha com gabarito
- Perguntas de acompanhamento ("explique melhor o segundo")
- Botão **Ver trechos consultados pela IA** em cada resposta, para conferir a base da resposta
- Tratamento de erros da API (chave inválida, limite de uso, falha de conexão)
- Modo debug opcional, que mostra as notas e as palavras que casaram na busca

## Como funciona

O app usa uma versão simples de **RAG** (geração aumentada por recuperação), sem bibliotecas de IA além do cliente da Groq:

1. **Extração e limpeza:** o texto é extraído de cada arquivo (`pypdf`, `python-docx`) e limpo de ruídos de formatação. Tabelas do DOCX são lidas linha a linha.
2. **Divisão em trechos:** o texto é dividido em trechos de ~1.000 caracteres, com sobreposição de 200, cortados em limite de frase ou de palavra.
3. **Busca:** a pergunta e os trechos são normalizados (minúsculas, sem acentos, sem *stopwords*), e cada trecho recebe uma nota pela soma do peso das palavras em comum. Palavras raras pesam mais que palavras comuns (ideia do TF-IDF).
4. **Pedidos genéricos** ("resuma", "faça um quiz") não têm palavras para buscar. Nesses casos, o app envia uma amostra de trechos espalhados pelos documentos.
5. **Acompanhamentos:** perguntas como "e o terceiro?" reaproveitam a última pergunta com assunto para a busca.
6. **Geração:** os trechos escolhidos e as últimas mensagens da conversa são enviados ao modelo via API da Groq.

## Tecnologias

- Python
- [Streamlit](https://streamlit.io/)
- [Groq API](https://console.groq.com/) (modelo `openai/gpt-oss-20b`)
- `pypdf` e `python-docx`

## Como executar

1. Clone o repositório:

   ```bash
   git clone https://github.com/joaoksaas/saas-lm.git
   cd saas-lm
   ```

2. (Recomendado) Crie um ambiente virtual e instale as dependências:

   ```bash
   python -m venv venv
   # Windows: venv\Scripts\activate    |    Linux/macOS: source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Rode o app:

   ```bash
   streamlit run saas_lm.py
   ```

4. Cole sua chave de API da Groq na barra lateral (gere uma em https://console.groq.com/keys).

> A chave é digitada na interface e não fica salva no código nem no repositório.

## Estrutura

```
saas_lm.py        # interface (Streamlit) e fluxo do chat
utils.py          # extração, limpeza, divisão em trechos e busca
requirements.txt
```

## Limitações conhecidas

- **Resumos de documentos longos são parciais.** O resumo usa uma amostra de poucos trechos (num livro de centenas de páginas, algo como 1% do texto). A IA avisa quando o resumo é parcial, e o usuário pode aprofundar por partes, com perguntas.
- **Perguntas de enumeração** ("liste todos os exemplos do livro") funcionam mal, porque a busca traz poucos trechos.
- **A busca é por palavras, não por significado.** Sinônimos ("remuneração" e "salário") e variações ("colmeia" e "colmeias") podem não casar.
- **Acompanhamentos voltam ao assunto, não ao item.** Em "explique o segundo", a busca recupera o tema da pergunta anterior, e o modelo usa o histórico para entender a referência.
- **PDFs escaneados** (imagem, sem texto) não são lidos, porque o app não faz OCR. Tabelas em PDF podem sair desorganizadas.
- **Limites do plano gratuito da Groq** (requisições e tokens por minuto e por dia) podem causar erros em uso intenso. Confira os limites atuais no console da Groq.
- Os documentos ficam só na sessão do navegador e se perdem ao recarregar a página.

## Privacidade

O conteúdo dos documentos selecionados é enviado à API da Groq a cada pergunta. Não envie documentos sensíveis.

## Roadmap

- [x] Upload de PDF, DOCX e TXT
- [x] Seleção dos arquivos ativos
- [x] Busca por trechos (RAG) com peso por raridade das palavras
- [x] Resumos, flashcards e questões
- [x] Trechos consultados visíveis na interface

## Próximos Passos

- [ ] Stemming (reduzir palavras ao radical) para plural e conjugação
- [ ] Busca semântica com embeddings (sinônimos)
- [ ] Resumo de documentos longos por partes
- [ ] OCR para PDFs escaneados
- [ ] Resumo automático ao carregar um arquivo

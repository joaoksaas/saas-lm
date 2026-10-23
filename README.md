# Saas LM

Assistente de IA para conversar com seus próprios textos e artigos, inspirado no NotebookLM. Você envia os documentos, escolhe quais usar e faz perguntas sobre o conteúdo deles. Feito com Streamlit e a API da Groq.

> 🚧 Projeto em estágio inicial, em desenvolvimento.

## O que ele faz

- Upload de textos e artigos
- Lista de arquivos na barra lateral, com seleção de quais entram na conversa
- Chat com a IA baseado no conteúdo dos arquivos selecionados
- Histórico da conversa mantido durante a sessão

## Tecnologias

- Python
- [Streamlit](https://streamlit.io/)
- [Groq API](https://console.groq.com/)

## Como executar

1. Clone o repositório e entre na pasta:

```bash
   git clone https://github.com/joaoksaas/saas-lm.git
   cd saas-lm
```

2. Instale as dependências:

```bash
   pip install -r requirements.txt
```

3. Rode o app:

```bash
   streamlit run saas_lm.py
```

4. Cole sua chave de API da Groq na barra lateral (gere uma em https://console.groq.com/keys).

> A chave é digitada no próprio app e não fica salva no código.

## Roadmap

- [x] Chat com a IA
- [x] Upload de arquivos .txt
- [x] Seleção dos arquivos ativos na conversa
- [x] Respostas baseadas no conteúdo dos arquivos
- [x] Suporte a PDF e DOCX
- [ ] Busca por trechos relevantes (RAG) para arquivos grandes
- [ ] Citação da fonte em cada resposta
- [ ] Resumo automático ao enviar um arquivo
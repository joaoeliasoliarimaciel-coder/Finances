# Nossas Finanças

App pessoal de controle financeiro do casal, feito em Streamlit.

## Arquivos deste pacote

- `app.py` — o aplicativo em si (é o único arquivo obrigatório para o Streamlit rodar).
- `requirements.txt` — lista as bibliotecas que o Streamlit Cloud precisa instalar. **Obrigatório.**
- `secrets.toml` — exemplo de usuário/senha do login. **Não é para subir no GitHub** (veja abaixo).
- `.gitignore` — evita subir seus dados financeiros e o arquivo de senha por engano.

## Como colocar no GitHub

1. No seu repositório no GitHub, envie (upload) os arquivos: `app.py`, `requirements.txt` e `.gitignore`.
   - **Não envie o `secrets.toml`** — ele é só um exemplo para você configurar direto no Streamlit Cloud (passo 3).
2. Confirme que os nomes dos arquivos estão exatamente assim (minúsculo, sem espaços).

## Como publicar no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io) e clique em "New app".
2. Escolha o repositório, a branch e em **"Main file path" digite exatamente `app.py`**.
3. Antes de clicar em "Deploy", vá em **"Advanced settings" → "Secrets"** e cole o conteúdo do arquivo `secrets.toml` (trocando a senha de exemplo pela sua senha de verdade). É assim que você define o usuário e a senha do login do app.
4. Clique em "Deploy".

## Login padrão (se você não configurar o Secrets)

Se você pular o passo 3, o app libera acesso com usuário `casal` e senha `financas2026`. Recomendo configurar sua própria senha para não deixar esse padrão exposto.

## Se der erro ao publicar

- Confira se `requirements.txt` está mesmo na raiz do repositório.
- Confira se "Main file path" está escrito exatamente `app.py`.
- No painel do app, clique em "Manage app" (canto inferior direito) para ver os logs reais do erro.

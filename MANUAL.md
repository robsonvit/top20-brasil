# 🎵 Top 20 Brasil – Automação Completa
### Manual de Instalação, Configuração e Operação

---

## 📋 Resumo da Lógica

```
Toda segunda-feira às 8h (Brasília)
          │
          ▼
  Google Apps Script
  dispara o workflow
  via GitHub API REST
          │
          ▼
  GitHub Actions (Ubuntu)
  ┌────────────────────────────────────────────────┐
  │  Script 01 – Busca o Top 20                    │
  │    → Kworb Spotify BR (scraping público)       │
  │    → Kworb YouTube BR (scraping público)       │
  │    → Google Trends via SerpAPI (opcional)      │
  │    → Salva output/top20.json                   │
  │                                                │
  │  Script 02 – Baixa áudios                     │
  │    → yt-dlp busca no YouTube por cada música  │
  │    → Baixa somente o áudio MP3                 │
  │    → Corta para 30 segundos cada              │
  │    → Salva em output/audios/                   │
  │                                                │
  │  Script 03 – Cria vídeo visual                 │
  │    → Pillow gera frames PNG (1920×1080)        │
  │    → Efeitos: partículas, gradiente animado,   │
  │      pulsação de texto, barra de progresso     │
  │    → FFmpeg compila frames em MP4              │
  │                                                │
  │  Script 04 – Mixa áudio + vídeo               │
  │    → Concatena os 20 MP3s                      │
  │    → FFmpeg combina com o vídeo visual         │
  │    → Gera video_final.mp4                      │
  │                                                │
  │  Script 05 – Posta no YouTube                  │
  │    → OAuth2 com refresh_token (Secrets)        │
  │    → Upload resumível via YouTube Data API v3  │
  │    → Define licença Creative Commons (CC BY)  │
  │    → Configura thumbnail personalizada         │
  └────────────────────────────────────────────────┘
          │
          ▼
  YouTube publica vídeo público
  com licença CC BY (Creative Commons)
  "Top 20 Brasil – Maio 2026" 🎵
```

---

## 🏗️ Estrutura do Repositório

```
top20-brasil/
├── .github/
│   └── workflows/
│       └── top20-semanal.yml       ← Workflow principal
├── scripts/
│   ├── 01_buscar_top20.py          ← Busca ranking
│   ├── 02_baixar_audios.py         ← Download MP3
│   ├── 03_criar_video.py           ← Vídeo animado
│   ├── 04_mixar_audio_video.py     ← Mix final
│   ├── 05_postar_youtube.py        ← Upload YouTube
│   ├── google_apps_script.js       ← Trigger semanal (Google)
│   └── obter_refresh_token_youtube.py ← Setup OAuth (local)
├── .gitignore
├── requirements.txt
└── MANUAL.md                       ← Este arquivo
```

---

## 🚀 Passo a Passo: Criar o Repositório no GitHub com Segurança

### Passo 1 – Criar o repositório público

1. Acesse **github.com** → clique em **"New repository"**
2. Nome: `top20-brasil`
3. Visibilidade: **Public** (necessário para GitHub Actions gratuito no plano Free)
4. Marque: **"Add a README file"**
5. Clique **"Create repository"**

> ⚠️ **SEGURANÇA**: Mesmo sendo público, as **Secrets** nunca ficam visíveis.
> Nenhum arquivo com tokens/senhas deve ir para o repositório.

---

### Passo 2 – Subir os arquivos do projeto

```bash
# Clone o repositório recém-criado
git clone https://github.com/SEU_USUARIO/top20-brasil.git
cd top20-brasil

# Copie todos os arquivos deste projeto para dentro da pasta
# (certifique-se que o .gitignore está presente antes do primeiro commit)

# Adicionar e commitar
git add .
git commit -m "feat: automação Top 20 Brasil inicial"
git push origin main
```

---

### Passo 3 – Configurar Google Cloud (YouTube API)

1. Acesse **console.cloud.google.com**
2. Crie um projeto: ex. `top20-brasil-bot`
3. Menu lateral → **APIs e Serviços** → **Biblioteca**
4. Busque e ative: **YouTube Data API v3**
5. Menu lateral → **Credenciais** → **Criar credenciais** → **ID do cliente OAuth 2.0**
   - Tipo de aplicativo: **Aplicativo para computador**
   - Nome: `top20-uploader`
6. Clique em **Baixar JSON** → salve como `client_secret.json`

#### Obter o Refresh Token (execute localmente UMA VEZ):

```bash
# Na sua máquina local (não no GitHub)
cd scripts/
pip install google-auth-oauthlib google-api-python-client
python obter_refresh_token_youtube.py
```

- Uma janela do navegador abrirá → faça login com a conta YouTube desejada
- Autorize as permissões
- O script imprimirá os 3 valores que você precisa salvar

---

### Passo 4 – Configurar GitHub Secrets

No repositório: **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Como obter | Obrigatório |
|---|---|---|
| `YOUTUBE_CLIENT_ID` | Saída do script de setup | ✅ Sim |
| `YOUTUBE_CLIENT_SECRET` | Saída do script de setup | ✅ Sim |
| `YOUTUBE_REFRESH_TOKEN` | Saída do script de setup | ✅ Sim |
| `SERPAPI_KEY` | serpapi.com (plano free: 100 buscas/mês) | ⬜ Opcional |

> 🔐 **Os Secrets são criptografados e jamais aparecem nos logs do workflow.**

---

### Passo 5 – Configurar GitHub Actions Permissions

No repositório: **Settings → Actions → General**

- Em **Workflow permissions**: marque **"Read and write permissions"**
- Clique em **Save**

---

### Passo 6 – Configurar Google Apps Script (trigger semanal)

1. Acesse **script.google.com** → **Novo projeto**
2. Cole o conteúdo de `scripts/google_apps_script.js`
3. Altere `GITHUB_USER` para seu usuário do GitHub
4. No menu lateral, clique em **Projeto** → **Propriedades do script**
5. Salve o GitHub Token de forma segura:

```javascript
// Execute esta função UMA VEZ no editor do Apps Script:
// Menu: Executar → salvarTokenGitHub
// Passe seu token como argumento na linha abaixo:
salvarTokenGitHub("ghp_SEU_TOKEN_AQUI");
```

**Como criar o GitHub Token:**
- github.com → Profile → Settings → Developer Settings
- Personal access tokens → Tokens (classic) → Generate new token
- Escopos necessários: `repo` + `workflow`
- Copie o token (só aparece uma vez!)

6. No editor do Apps Script, execute: `configurarAcionador()`
   - Autorize as permissões quando solicitado
   - ✅ O trigger semanal está criado!

---

### Passo 7 – Testar manualmente

**Pelo GitHub:**
- Aba **Actions** → workflow `Top 20 Brasil - Semanal` → **Run workflow**

**Pelo Apps Script:**
- Execute a função `dispararWorkflow()` manualmente no editor

---

## ⚙️ Sobre o Vídeo Gerado

| Propriedade | Valor |
|---|---|
| Resolução | 1920 × 1080 (Full HD, 16:9) |
| FPS | 24 |
| Duração | ~10 minutos (20 músicas × 30s) |
| Codec vídeo | H.264 (libx264) |
| Codec áudio | AAC 128kbps |
| Licença | Creative Commons CC BY |
| Privacidade | Público |

**Efeitos visuais (sem loop repetitivo):**
- Partículas flutuantes com movimento aperiódico
- Gradiente de fundo que muda lentamente ao longo de todo o vídeo
- Número da posição com pulsação (frequência única por música)
- Nome da música com cor variável baseada em seno
- Barra de progresso da faixa atual
- Lista lateral com destaque da música em reprodução
- Ondas decorativas com fase temporal progressiva

---

## 🔍 Fontes do Ranking

| Fonte | Tipo | Custo |
|---|---|---|
| Kworb Spotify BR | Scraping público | Gratuito |
| Kworb YouTube BR | Scraping público | Gratuito |
| SerpAPI Google Trends | API | Gratuito (100/mês) ou pago |

As fontes são consultadas em ordem de prioridade. Se nenhuma retornar dados suficientes, um fallback com músicas populares conhecidas é usado automaticamente.

---

## 📅 Agendamento

| Componente | Função | Quando |
|---|---|---|
| Google Apps Script | Disparar o workflow | Toda segunda-feira às 8h BRT |
| GitHub Actions | Executar todos os scripts | Toda segunda-feira às 11h UTC (= 8h BRT) |

O workflow também roda automaticamente via `cron` no GitHub (backup do trigger manual).

---

## 🛠️ Manutenção

### Atualizar o fallback de músicas
Edite a lista `FALLBACK` em `scripts/01_buscar_top20.py`.

### Alterar duração de cada faixa
Em `scripts/02_baixar_audios.py` e `scripts/03_criar_video.py`:
```python
DURACAO_POR_MUSICA = 30  # altere aqui (em segundos)
```

### Alterar cores/visual
Em `scripts/03_criar_video.py`, seção `# Paleta de cores`.

### Refresh token expirou
Execute novamente `scripts/obter_refresh_token_youtube.py` e atualize o Secret.

### Verificar logs
- GitHub: aba **Actions** → clique no run → expanda cada step
- Apps Script: **Execuções** no menu lateral

---

## ❓ Perguntas Frequentes

**P: O repositório público expõe minhas credenciais?**
R: Não. As credenciais ficam nos **GitHub Secrets**, que são criptografados e nunca expostos nos logs ou no código.

**P: O YouTube pode restringir o vídeo por copyright das músicas?**
R: Possível. O uso de trechos de 30s é uma zona cinzenta do "fair use". Configuramos a licença como Creative Commons e a descrição como "educativo/informativo". Se houver ContentID claim, o vídeo pode ter anúncios inseridos pelo detentor dos direitos, mas raramente é removido.

**P: O GitHub Actions gratuito tem limite?**
R: Sim: 2.000 minutos/mês em repositórios públicos (gratuito). Cada run leva ~30-40 min. 4 runs/mês = ~160 min – bem dentro do limite.

**P: O yt-dlp pode falhar?**
R: Se o YouTube bloquear o IP do GitHub Actions, yt-dlp pode falhar para algumas músicas. Nesses casos, o script usa silêncio como fallback e o vídeo visual ainda é gerado normalmente.

**P: Posso adicionar mais de 20 músicas?**
R: Sim. Altere `TOTAL_MUSICAS` em `03_criar_video.py` e ajuste a lógica de geração de frames.

---

## 📞 Checklist de Funcionamento

- [ ] Repositório criado no GitHub (público)
- [ ] Todos os arquivos commitados com .gitignore correto
- [ ] YouTube Data API v3 ativada no Google Cloud
- [ ] `obter_refresh_token_youtube.py` executado localmente
- [ ] 3 GitHub Secrets configurados (CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
- [ ] GitHub Actions Permissions configurado para "Read and write"
- [ ] Google Apps Script criado com o código correto
- [ ] `GITHUB_USER` alterado no Apps Script
- [ ] Token GitHub salvo nas propriedades do Apps Script
- [ ] `configurarAcionador()` executado no Apps Script
- [ ] Teste manual feito via "Run workflow" no GitHub Actions
- [ ] Primeiro vídeo publicado no YouTube com sucesso ✅

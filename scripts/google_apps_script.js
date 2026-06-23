/**
 * ============================================================
 * TOP 20 BRASIL – Google Apps Script
 * ============================================================
 * Executa semanalmente via acionador de tempo (trigger).
 * Dispara o workflow do GitHub Actions via API REST.
 * Também envia e-mail de relatório após execução.
 *
 * COMO USAR:
 * 1. Abra script.google.com → Novo projeto
 * 2. Cole este código
 * 3. Preencha as constantes abaixo
 * 4. Rode configurarAcionador() UMA VEZ para criar o trigger semanal
 * 5. Autorize as permissões quando solicitado
 * ============================================================
 */

// ── CONFIGURAÇÕES – preencha antes de publicar ──────────────
const CONFIG = {
  // Token GitHub com permissão "Actions: write" (repo → Settings → Actions → Workflow permissions)
  GITHUB_TOKEN: PropertiesService.getScriptProperties().getProperty("GITHUB_TOKEN"),

  // Usuário e repositório GitHub
  GITHUB_USER: "SEU_USUARIO_GITHUB",
  GITHUB_REPO: "top20-brasil",

  // E-mail para receber relatório (pode ser o seu Gmail)
  EMAIL_RELATORIO: Session.getActiveUser().getEmail(),

  // Dia da semana para execução: 1=Dom, 2=Seg, 3=Ter, 4=Qua, 5=Qui, 6=Sex, 7=Sáb
  DIA_SEMANA: ScriptApp.WeekDay.MONDAY,

  // Hora de execução (0-23, horário de Brasília UTC-3)
  HORA_EXECUCAO: 8,
};
// ────────────────────────────────────────────────────────────


/**
 * Função principal – disparada pelo acionador semanal.
 * Aciona o workflow no GitHub via API REST (workflow_dispatch).
 */
function dispararWorkflow() {
  const url = `https://api.github.com/repos/${CONFIG.GITHUB_USER}/${CONFIG.GITHUB_REPO}/actions/workflows/top20-semanal.yml/dispatches`;

  const agora = new Date();
  const meses = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                 "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"];
  const mesAno = `${meses[agora.getMonth()]} ${agora.getFullYear()}`;

  const payload = JSON.stringify({
    ref: "main",
    inputs: {
      mes_ano: mesAno,
    },
  });

  const opcoes = {
    method: "POST",
    headers: {
      Authorization: `Bearer ${CONFIG.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "Content-Type": "application/json",
    },
    payload: payload,
    muteHttpExceptions: true,
  };

  Logger.log(`Disparando workflow para: Top 20 – ${mesAno}`);
  const resposta = UrlFetchApp.fetch(url, opcoes);
  const codigo = resposta.getResponseCode();

  if (codigo === 204) {
    Logger.log("✅ Workflow disparado com sucesso!");
    enviarEmailSucesso(mesAno);
    registrarLog("SUCESSO", mesAno, codigo);
  } else {
    const corpo = resposta.getContentText();
    Logger.log(`❌ Erro ao disparar workflow: ${codigo} – ${corpo}`);
    enviarEmailErro(mesAno, codigo, corpo);
    registrarLog("ERRO", mesAno, codigo, corpo);
  }
}


/**
 * Consulta o status do último workflow run.
 */
function consultarStatusUltimoRun() {
  const url = `https://api.github.com/repos/${CONFIG.GITHUB_USER}/${CONFIG.GITHUB_REPO}/actions/runs?per_page=1`;
  const opcoes = {
    method: "GET",
    headers: {
      Authorization: `Bearer ${CONFIG.GITHUB_TOKEN}`,
      Accept: "application/vnd.github+json",
    },
    muteHttpExceptions: true,
  };

  const resposta = UrlFetchApp.fetch(url, opcoes);
  const dados = JSON.parse(resposta.getContentText());
  const runs = dados.workflow_runs || [];

  if (runs.length > 0) {
    const run = runs[0];
    Logger.log(`Último run: #${run.run_number} | Status: ${run.status} | Conclusão: ${run.conclusion}`);
    Logger.log(`URL: ${run.html_url}`);
    return run;
  }
  return null;
}


/**
 * Verifica status 30 min após disparo e envia relatório detalhado.
 * Configure um segundo trigger com 30 min de delay se quiser.
 */
function verificarERelatarStatus() {
  const run = consultarStatusUltimoRun();
  if (!run) return;

  const corpo = `
<h2>📊 Relatório Top 20 Brasil – GitHub Actions</h2>
<table border="1" cellpadding="6" style="border-collapse:collapse">
  <tr><td><b>Run #</b></td><td>${run.run_number}</td></tr>
  <tr><td><b>Status</b></td><td>${run.status}</td></tr>
  <tr><td><b>Conclusão</b></td><td>${run.conclusion || "Em andamento"}</td></tr>
  <tr><td><b>Início</b></td><td>${run.created_at}</td></tr>
  <tr><td><b>URL</b></td><td><a href="${run.html_url}">${run.html_url}</a></td></tr>
</table>
<p>Acesse o YouTube para conferir o vídeo publicado.</p>
  `;

  MailApp.sendEmail({
    to: CONFIG.EMAIL_RELATORIO,
    subject: `[Top20 Brasil] Status: ${run.conclusion || run.status}`,
    htmlBody: corpo,
  });
}


// ── Funções auxiliares ───────────────────────────────────────

function enviarEmailSucesso(mesAno) {
  MailApp.sendEmail({
    to: CONFIG.EMAIL_RELATORIO,
    subject: `✅ [Top20 Brasil] Workflow disparado – ${mesAno}`,
    htmlBody: `
      <h2>✅ Workflow GitHub Actions iniciado com sucesso!</h2>
      <p>O processo de geração e postagem do <b>Top 20 Brasil – ${mesAno}</b> foi iniciado.</p>
      <p>Acesse <a href="https://github.com/${CONFIG.GITHUB_USER}/${CONFIG.GITHUB_REPO}/actions">
        github.com/${CONFIG.GITHUB_USER}/${CONFIG.GITHUB_REPO}/actions
      </a> para acompanhar.</p>
      <p>O vídeo será postado no YouTube em aproximadamente 30-60 minutos.</p>
    `,
  });
}

function enviarEmailErro(mesAno, codigo, corpo) {
  MailApp.sendEmail({
    to: CONFIG.EMAIL_RELATORIO,
    subject: `❌ [Top20 Brasil] Erro ao disparar workflow – ${mesAno}`,
    htmlBody: `
      <h2>❌ Erro ao disparar o workflow GitHub Actions</h2>
      <p>Mês/Ano: <b>${mesAno}</b></p>
      <p>Código HTTP: <b>${codigo}</b></p>
      <pre>${corpo}</pre>
      <p>Verifique o token GitHub e as configurações do repositório.</p>
    `,
  });
}

function registrarLog(status, mesAno, codigo, erro) {
  const planilhaId = PropertiesService.getScriptProperties().getProperty("PLANILHA_LOG_ID");
  if (!planilhaId) return; // Log em planilha é opcional

  try {
    const ss = SpreadsheetApp.openById(planilhaId);
    const aba = ss.getSheetByName("Log") || ss.insertSheet("Log");
    aba.appendRow([
      new Date().toISOString(),
      status,
      mesAno,
      codigo,
      erro || "",
    ]);
  } catch (e) {
    Logger.log("Erro ao registrar log: " + e);
  }
}


// ── Gerenciamento de acionadores (triggers) ─────────────────

/**
 * Crie o acionador semanal rodando esta função UMA VEZ manualmente.
 */
function configurarAcionador() {
  // Remover triggers existentes desta função para não duplicar
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === "dispararWorkflow") {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  // Criar novo trigger semanal
  ScriptApp.newTrigger("dispararWorkflow")
    .timeBased()
    .onWeekDay(CONFIG.DIA_SEMANA)
    .atHour(CONFIG.HORA_EXECUCAO + 3) // UTC = Brasília + 3h
    .create();

  Logger.log(`✅ Acionador semanal criado: toda ${nomeDia(CONFIG.DIA_SEMANA)} às ${CONFIG.HORA_EXECUCAO}h (Brasília)`);
}

/**
 * Remove todos os acionadores do script.
 */
function removerTodosAcionadores() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  Logger.log("Todos os acionadores removidos.");
}

/**
 * Listar acionadores ativos.
 */
function listarAcionadores() {
  ScriptApp.getProjectTriggers().forEach(t => {
    Logger.log(`Função: ${t.getHandlerFunction()} | Tipo: ${t.getEventType()}`);
  });
}

function nomeDia(dia) {
  const nomes = {
    [ScriptApp.WeekDay.SUNDAY]: "Domingo",
    [ScriptApp.WeekDay.MONDAY]: "Segunda",
    [ScriptApp.WeekDay.TUESDAY]: "Terça",
    [ScriptApp.WeekDay.WEDNESDAY]: "Quarta",
    [ScriptApp.WeekDay.THURSDAY]: "Quinta",
    [ScriptApp.WeekDay.FRIDAY]: "Sexta",
    [ScriptApp.WeekDay.SATURDAY]: "Sábado",
  };
  return nomes[dia] || "?";
}


/**
 * Salvar token GitHub nas propriedades do script (mais seguro que hardcoded).
 * Rode esta função uma vez passando seu token.
 */
function salvarTokenGitHub(token) {
  PropertiesService.getScriptProperties().setProperty("GITHUB_TOKEN", token);
  Logger.log("Token salvo nas propriedades do script.");
}

/**
 * Salvar ID da planilha de log (opcional).
 */
function salvarIdPlanilha(id) {
  PropertiesService.getScriptProperties().setProperty("PLANILHA_LOG_ID", id);
  Logger.log("ID da planilha salvo.");
}

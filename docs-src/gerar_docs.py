"""Gera os PDFs de apresentação (falas v2, roteiro v2 e banco de perguntas) no visual dos documentos originais.

Uso: python docs-src/gerar_docs.py
Requer Google Chrome instalado (usa o modo headless para imprimir em PDF).

Marcação dos textos de fala:
  [texto]    -> indicação de cena (laranja, não se fala)
  **texto**  -> frase de impacto (destaque azul)
  outras     -> fala normal
"""
import html
import os
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EQUIPE = "Athos, Jhonatan, Gabriel, Lucas, Rafael"
CHROME = next((p for p in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                           r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                           os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")] if os.path.exists(p)), None)

CSS = """
@page { size: A4; margin: 20mm 18mm 18mm 18mm;
  @top-left-corner { content: ""; background: #14294A; border-bottom: 3px solid #F28C00; }
  @top-left { content: "STARTUP XYZ  |  FAIXA"; background: #14294A; color: #fff; font: bold 9.5pt Arial, sans-serif; border-bottom: 3px solid #F28C00; vertical-align: middle; }
  @top-center { content: ""; background: #14294A; border-bottom: 3px solid #F28C00; }
  @top-right { content: "Gestão de Documentos para IA"; background: #14294A; color: #C9D3E0; font: 8.5pt Arial, sans-serif; border-bottom: 3px solid #F28C00; vertical-align: middle; }
  @top-right-corner { content: ""; background: #14294A; border-bottom: 3px solid #F28C00; }
  @bottom-left { content: "Equipe: EQUIPE"; font: 8.5pt Arial, sans-serif; color: #7A8797; }
  @bottom-right { content: "Página " counter(page); font: 8.5pt Arial, sans-serif; color: #7A8797; } }
body { padding-top: 4mm; }
* { box-sizing: border-box; }
body { font-family: Arial, 'Segoe UI', sans-serif; color: #16202C; font-size: 10.6pt; line-height: 1.55; margin: 0; }
.faixa { position: fixed; top: -26mm; left: -18mm; right: -18mm; height: 17mm; background: #14294A; border-bottom: 3px solid #F28C00;
  color: #fff; display: flex; align-items: center; justify-content: space-between; padding: 0 18mm; font-size: 9.5pt; }
.faixa b { letter-spacing: .03em; }
.faixa span { color: #C9D3E0; font-size: 8.5pt; }
h1 { font-size: 22pt; color: #14294A; margin: 0 0 4px; }
.subtitulo { color: #6B7888; font-size: 11.5pt; margin: 0 0 6px; }
.equipe { color: #14294A; font-weight: bold; font-size: 9.5pt; margin-bottom: 10px; }
hr.lar { border: 0; border-top: 1.5px solid #F28C00; margin: 12px 0 14px; }
p { margin: 0 0 8px; text-align: justify; }
.caixa { background: #F4F6F9; border: 1px solid #DCE2EA; border-radius: 4px; padding: 10px 14px; margin: 10px 0 14px; }
.caixa.verde { background: #E9F3EC; border-color: #7FB08D; }
.caixa.laranja { background: #FFF4E2; border-color: #F2C27A; }
.caixa b.t { display: block; color: #14294A; margin-bottom: 2px; }
h2.bloco { background: #14294A; color: #fff; font-size: 13pt; padding: 8px 12px; margin: 18px 0 8px; border-left: 5px solid #F28C00; break-after: avoid; }
.orador { display: flex; justify-content: space-between; background: #1D3A63; color: #fff; font-weight: bold; padding: 6px 12px; margin: 6px 0 4px; break-after: avoid; }
.slides { font-size: 9pt; color: #4C5A6B; margin-bottom: 8px; }
.cena { color: #E07B00; font-style: italic; font-size: 9pt; margin: 8px 0 3px; break-after: avoid; }
.fala { margin-left: 8px; }
.impacto { margin-left: 8px; color: #14294A; font-weight: bold; font-style: italic; }
table { width: 100%; border-collapse: collapse; font-size: 9.4pt; margin: 6px 0 12px; }
th { background: #14294A; color: #fff; text-align: left; padding: 6px 8px; }
td { border: 1px solid #DCE2EA; padding: 6px 8px; vertical-align: top; }
tr:nth-child(even) td { background: #F7F9FB; }
tr { break-inside: avoid; }
ul { margin: 4px 0 10px 18px; padding: 0; } li { margin-bottom: 4px; }
.q { break-inside: avoid; border-bottom: 1px solid #E3E8EE; padding: 7px 0; }
.q .perg { font-weight: bold; color: #14294A; }
.q .quem { font-size: 8.5pt; color: #E07B00; font-weight: bold; margin-left: 6px; }
.q .resp { margin: 3px 0 0; }
.tema { color: #14294A; font-size: 12pt; margin: 16px 0 2px; border-bottom: 2px solid #F28C00; padding-bottom: 2px; break-after: avoid; }
.pal { font-size: 8.5pt; color: #7A8797; font-weight: normal; }
"""


def pagina(titulo_faixa, corpo):
    css = CSS.replace("EQUIPE", EQUIPE).replace("FAIXA", titulo_faixa)
    return (f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>{css}</style></head><body>'
            f'{corpo}</body></html>')


def md(t):
    """Negrito inline com **...** e escape do resto."""
    partes = t.split("**")
    return "".join(f"<b>{html.escape(p)}</b>" if i % 2 else html.escape(p) for i, p in enumerate(partes))


def fala_html(texto):
    out, palavras = [], 0
    for linha in [l.strip() for l in texto.strip().splitlines() if l.strip()]:
        if linha.startswith("[") and linha.endswith("]"):
            out.append(f'<div class="cena">{html.escape(linha)}</div>')
        elif linha.startswith("**") and linha.endswith("**"):
            out.append(f'<p class="impacto">{html.escape(linha[2:-2])}</p>')
            palavras += len(linha.split())
        else:
            out.append(f'<p class="fala">{md(linha)}</p>')
            palavras += len(linha.split())
    return "\n".join(out), palavras


def imprimir(nome_html, conteudo, nome_pdf):
    tmp = RAIZ / "docs-src" / nome_html
    tmp.write_text(conteudo, encoding="utf-8")
    if not CHROME:
        print("Chrome não encontrado; HTML salvo em", tmp)
        return
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={RAIZ / nome_pdf}", tmp.as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("gerado:", nome_pdf)


# ----------------------------------------------------------------------------- FALAS
BLOCOS = [
    ("Bloco 1 — Abertura, Problema e Requisitos", "Athos", "3 minutos",
     "Slides 1 a 4 — Capa, Entendimento do Problema, Levantamento de Requisitos e Visão Geral da Solução.", """
[olhar para a banca, não para o slide, ao dizer o número]
Bom dia. Nós somos Athos, Gabriel, Jhonatan, Lucas e Rafael. Antes de mostrar qualquer diagrama, quero deixar um número com vocês: cinquenta mil. É a quantidade de documentos que a Startup XYZ recebe por mês, de clientes que confiam a ela arquivos que não podem ser perdidos nem vistos por outra empresa.
**O problema aqui não é só guardar arquivo. É guardar o ativo que essa empresa vai usar para treinar a próxima geração da própria inteligência artificial.**
A XYZ é um SaaS que extrai dados de PDFs e imagens com IA. Quando ela cresce, aparecem três problemas ao mesmo tempo. Se todo upload passar pelo servidor, o servidor vira gargalo. Com milhares de clientes, o cliente A nunca pode ver o documento do cliente B. E apagar o histórico não é opção, mas guardar tudo em armazenamento rápido faz o custo subir todo mês.
[transição de slide: Levantamento de Requisitos]
Separamos os requisitos em dois grupos. Funcionais: autenticar o usuário, receber PDF e imagem sem gargalo, isolar os documentos por cliente, permitir download seguro e preservar o histórico por anos. Não funcionais: escalar com cinquenta mil arquivos por mês, segurança e privacidade pensando na LGPD, custo proporcional ao uso, alta disponibilidade sem administrar servidores e rastreabilidade de quem acessou o quê.
**Não construímos um repositório de arquivos. Construímos uma estratégia de valor ao longo do tempo.**
[transição de slide: Visão Geral da Solução]
Em linguagem simples, a solução tem quatro passos. O usuário faz login e recebe um token que diz quem ele é. A API confere esse token e decide o que ele pode acessar. O sistema devolve uma chave temporária que abre só aquele arquivo, por poucos minutos. E o arquivo vai direto para o armazenamento, que depois de um ano o move sozinho para uma camada muito mais barata, sem apagar nada. O Jhonatan agora mostra como cada peça faz isso.
"""),
    ("Bloco 2 — Arquitetura, Serviços e Justificativa", "Jhonatan", "3 minutos",
     "Slides 5 a 8 — Diagrama de Arquitetura, Explicação dos Serviços, Justificativa da Escolha e Mapeamento de Requisitos.", """
[apontar o diagrama da esquerda para a direita, seguindo os números das setas]
Obrigado, Athos. A forma mais simples de resolver isso seria um servidor ligado o tempo todo esperando os uploads. Foi exatamente o que decidimos não fazer. Cinquenta mil arquivos por mês dão pouco mais de um por minuto: um servidor ligado vinte e quatro horas ficaria ocioso quase o tempo todo e ainda seria o gargalo nos picos.
[seta 1: Cliente → Cognito]
O fluxo começa no Amazon Cognito. É ele que autentica o usuário e emite um token JWT. Usamos o Cognito para não construir login do zero.
[seta 2: Cliente → API Gateway]
Com esse token, o app chama o Amazon API Gateway. O Gateway não autentica ninguém: ele valida o token do Cognito e limita o número de requisições. Sem token válido a chamada morre ali, e a Lambda nem executa.
[setas 3 e 4: Lambda e STS]
Depois vem a AWS Lambda, e aqui está o que diferencia a nossa solução. A Lambda não recebe o arquivo. Ela lê quem é o usuário no próprio token, pede ao AWS STS uma credencial temporária que só enxerga a pasta desse usuário e usa essa credencial para assinar uma URL válida por quinze minutos.
**O arquivo vai direto do cliente para o Amazon S3. A Lambda nunca toca no binário, então não há limite de payload nem gargalo no backend.**
[apontar para o bucket S3]
O S3 é o coração da solução. Escolhemos S3 e não EFS porque os documentos são gravados uma vez e não são editados: precisamos de durabilidade, não de sistema de arquivos. Os objetos são cifrados com uma chave nossa no AWS KMS, cada upload novo é escaneado pelo GuardDuty, e CloudWatch e CloudTrail registram o que acontece.
Uma pergunta comum: por que um bucket só, com uma pasta por cliente, e não um bucket por cliente? A AWS até permite milhares de buckets por conta, mas cada bucket seria mais uma política, mais uma regra de ciclo de vida e mais uma configuração de chave para manter. Com um bucket e uma credencial restrita à pasta, temos o mesmo isolamento com uma configuração só, e o histórico fica reunido para treinar a IA.
[transição de slide: Atendimento aos Requisitos]
**Cada requisito que o Athos apresentou tem um componente concreto respondendo por ele. A tabela mostra isso linha por linha.**
Agora o Gabriel mostra como essa arquitetura se comporta quando cresce, quando algo falha e quanto ela custa.
"""),
    ("Bloco 3 — Escalabilidade, Resiliência, Segurança, Custos e Recuperação", "Gabriel", "3 minutos",
     "Slides 9 a 13 — Escalabilidade, Resiliência a Falhas, Segurança, Custos e Estratégia de Recuperação.", """
[pausa de um segundo antes de começar, tom mais firme]
Vou responder três perguntas antes que vocês precisem fazer: o que acontece se o volume crescer dez vezes, o que acontece se algo falhar, e quanto isso custa.
Crescimento. Cinquenta mil documentos por mês são pouco mais de um por minuto; dez vezes mais são doze por minuto. Nossa API aceita dez requisições por segundo por rota, e a conta aceita dez mil. Não existe servidor para redimensionar, e os limites que existem são cotas de conta, ajustáveis com um pedido à AWS. Na demo, cada autorização levou cerca de duzentos e cinquenta milissegundos.
**Crescer dez vezes não exige redesenhar a solução. Exige, no máximo, um pedido de aumento de cota.**
[transição de slide: Resiliência]
Falhas. Não há instância para cair: Lambda, API Gateway e Cognito rodam em várias zonas. O S3 grava cada objeto em pelo menos três zonas antes de confirmar o upload, por isso o RPO é praticamente zero. Se a região inteira cair, os dados continuam lá e a infraestrutura é recriada em cerca de dois minutos pelo CloudFormation. Não replicamos para outra região porque o Brasil tem uma só, e copiar dados pessoais para fora do país é transferência internacional pela LGPD.
[transição de slide: Segurança]
Segurança em três camadas. Identidade: a Lambda lê o usuário do token do Cognito, nunca do que o cliente envia. Rede: não usamos VPC de propósito, porque nenhum componente precisa de rede privada; o controle está no bucket fechado ao público, na exigência de TLS e no limite de requisições. Dados: criptografia com KMS e registro no CloudTrail de cada credencial emitida.
[apontar para a tabela de custos]
Custo. Em São Paulo, no terceiro ano, com um ano de documentos no S3 Standard e dois no Deep Archive, a conta fica em torno de sessenta dólares por mês. Sem o ciclo de vida, só o armazenamento desse histórico custaria noventa e sete.
**O custo de armazenamento cai cerca de noventa e dois por cento no momento em que o documento deixa de ser operação e vira histórico.**
O segundo maior item é o GuardDuty, uns vinte dólares por mês. Ele se paga porque o arquivo vem de fora, é aberto automaticamente pelo parser de IA e fica guardado para sempre. Escanear na entrada custa quatro centésimos de centavo por documento.
[transição de slide: Backup e Recuperação]
Por fim, recuperação: o versionamento desfaz qualquer sobrescrita, e a política do bucket só deixa a conta root apagar uma versão de vez. O Lucas agora mostra tudo isso funcionando.
"""),
    ("Bloco 4 — Demonstração ao vivo", "Lucas", "3 minutos",
     "Slide 14 — Projeto em funcionamento, na conta AWS do grupo em São Paulo. Preparação no Roteiro v2.", """
[tela: página da demo na aba do cliente-a, já logado; console da Lambda aberto em outra aba]
Até aqui vocês viram o desenho. Agora vão ver a arquitetura rodando, na nossa conta AWS em São Paulo.
[clicar em "Chamar a API sem login"]
Primeiro, alguém de fora chama a nossa API sem login: resposta 401. Com um token forjado, 401 de novo. Isso para no API Gateway; a Lambda nem executa.
[escolher contrato-cliente-a.pdf e clicar em Enviar]
Agora o cliente A envia um contrato. A API devolveu a URL e o navegador gravou direto no S3: resposta 204. Reparem na chave: o arquivo caiu na pasta usuario- seguida do identificador desse usuário no Cognito, com um nome gerado pelo servidor.
[colar no campo 4 a chave do arquivo do cliente-b e clicar em Tentar baixar]
Agora o ataque. O cliente A descobriu o nome de um arquivo do cliente B e pede o download. A aplicação recusa: 403, chave fora do seu prefixo. Mas e se o nosso código tivesse um bug e esquecesse essa checagem?
[console: APP_CHECK = false, Salvar; voltar à página e clicar de novo em Tentar baixar]
**Desliguei a checagem da aplicação para simular o bug. A Lambda assinou a URL, e o S3 respondeu 403 AccessDenied. A credencial que assinou essa URL foi emitida pelo STS só para a pasta do cliente A. O isolamento não depende de o código lembrar de checar.**
[console: voltar APP_CHECK para true e salvar]
[na lista, clicar em Baixar no documento DEEP_ARCHIVE e depois em Restaurar]
Por último, o tempo. Este documento está em Deep Archive, como estaria depois de um ano. O download é recusado com a mensagem de arquivado, e o cliente pede a restauração: 202. Em até doze horas o arquivo volta. Ninguém apagou nada.
[se sobrar tempo: CloudTrail filtrado por AssumeRole]
E tudo ficou registrado: o CloudTrail mostra cada credencial emitida, com o usuário e a pasta a que ela dava acesso. Passo para o Rafael.
"""),
    ("Bloco 5 — Evolução e Encerramento", "Rafael", "1,5 minuto",
     "Slides 15 e 16 — Evolução e Visão de Futuro, Conclusão.", """
[tom mais reflexivo, ritmo um pouco mais lento]
Tudo o que vocês viram resolve o problema de hoje. Quero fechar com o que vem depois.
Se a empresa crescer dez vezes, o próximo passo não é redesenhar: é colocar uma fila SQS entre o upload e a extração de IA, para que um pico de envios não sobrecarregue o processamento. A infraestrutura já é código, recriada em dois minutos pelo CloudFormation; o próximo passo é um pipeline de deploy com revisão. E, para o histórico virar base de treino com segurança, o Macie encontra dados pessoais e o treino roda num ambiente separado, com dados anonimizados.
[transição para o encerramento, olhar para todos os avaliadores]
Para fechar, volto ao número do Athos: cinquenta mil documentos por mês que não podem ser perdidos nem vistos por outro cliente, com um custo que não pode explodir com o tempo.
**A resposta não é a arquitetura mais complexa. É a mais honesta com o problema: cada serviço faz o que faz de melhor, o armazenamento fica noventa e dois por cento mais barato quando o dado vira histórico, e o isolamento entre clientes foi provado ao vivo, não só no papel.**
Segurança desenhada na arquitetura, custo sob controle e nenhum documento perdido. Obrigado, e ficamos à disposição para as perguntas.
"""),
]


def gerar_falas():
    corpo = [f'<h1>Textos de Apresentação v2</h1><p class="subtitulo">Startup XYZ — Gestão de Documentos para IA | Discurso completo, alinhado à arquitetura implantada e à demo real</p>',
             f'<div class="equipe">Equipe: {EQUIPE}</div><hr class="lar">',
             '<p>Esta versão substitui a v1. Ela corrige os pontos técnicos que a banca poderia contestar e troca o walkthrough simulado pela demonstração real na AWS. O texto não precisa ser decorado palavra por palavra, mas ensaiado até sair natural, sem leitura de slide.</p>',
             '<div class="caixa"><b class="t">Como usar este material</b>As frases em <span style="color:#E07B00;font-style:italic">itálico laranja</span> são indicações de cena: o que fazer ou apontar, e não se falam. As frases em <b style="color:#14294A"><i>destaque azul</i></b> são os pontos de maior impacto: diga com pausa antes e depois.</div>']
    resumo = []
    for titulo, quem, tempo, slides, texto in BLOCOS:
        h, n = fala_html(texto)
        resumo.append((quem, tempo, n))
        corpo.append(f'<h2 class="bloco">{html.escape(titulo)}</h2><div class="orador"><span>{quem}</span><span>{tempo} <span class="pal">(~{n} palavras)</span></span></div>'
                     f'<div class="slides">{html.escape(slides)}</div>{h}')
    total = sum(n for *_, n in resumo)
    corpo.append(f'<div class="caixa verde"><b class="t">Tempo total</b>{total} palavras de fala, cerca de {total/140:.0f} minutos a 140 palavras por minuto, mais as ações da demo. Fica em torno de 13 minutos, dentro da janela de 10 a 15 do guia.</div>')
    corpo.append('<div class="caixa laranja"><b class="t">O que mudou em relação à v1</b><ul>'
                 '<li>Quem autentica é o Cognito; o API Gateway só valida o token.</li>'
                 '<li>O isolamento é feito por credencial temporária do STS restrita à pasta, não por "condition key de prefixo" (a condição s3:prefix só vale para listagem).</li>'
                 '<li>O argumento do bucket por cliente foi atualizado: a AWS permite até 1 milhão de buckets; o motivo é operacional.</li>'
                 '<li>Números em São Paulo: Deep Archive custa 8% do Standard (economia de ~92%, não 95%) e o total fica em ~US$ 60/mês no 3º ano.</li>'
                 '<li>GuardDuty faz parte da arquitetura atual, com justificativa de custo; não é mais "próximo passo".</li>'
                 '<li>RPO explicado como gravação em 3+ zonas (não "replicação"); falha de região e LGPD tratadas.</li>'
                 '<li>O bloco do Lucas virou demonstração real, com cenas que batem com a página da demo.</li></ul></div>')
    imprimir("falas_v2.html", pagina("TEXTOS DE APRESENTAÇÃO", "\n".join(corpo)), "Textos_de_Apresentacao_v2.pdf")
    return resumo


# ----------------------------------------------------------------------------- ROTEIRO
def gerar_roteiro(resumo):
    linhas = [("Apresentação do problema", "1, 2", "1,5 min", "Athos"), ("Requisitos e visão da solução", "3, 4", "1,5 min", "Athos"),
              ("Arquitetura, serviços, justificativa e requisitos", "5 a 8", "3 min", "Jhonatan"),
              ("Escalabilidade, resiliência, segurança, custos e recuperação", "9 a 13", "3 min", "Gabriel"),
              ("Demonstração ao vivo na AWS", "14", "3 min", "Lucas"), ("Evolução e encerramento", "15, 16", "1,5 min", "Rafael")]
    tab = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in linhas)
    corpo = f"""
<h1>Roteiro de Apresentação v2</h1><p class="subtitulo">Startup XYZ — Gestão de Documentos para IA | Tempo, divisão de falas, preparação da demo e perguntas da banca</p>
<div class="equipe">Equipe: {EQUIPE}</div><hr class="lar">
<p>Este roteiro organiza os 16 slides da estrutura oficial dentro da janela de 10 a 15 minutos do guia, com cada integrante dono de um bloco coeso. A mudança principal em relação à v1: o slide 14 agora é uma <b>demonstração real</b> na conta AWS do grupo, como o guia exige ("não basta dizer que funciona, mostre funcionando").</p>
<h2 class="bloco">1. Distribuição de tempo (total: ~13,5 minutos)</h2>
<table><tr><th>Etapa</th><th>Slides</th><th>Tempo</th><th>Responsável</th></tr>{tab}</table>
<p>Reserve de 2 a 4 minutos, fora desse total, para as perguntas da banca. O texto completo de cada bloco está em <b>Textos_de_Apresentacao_v2.pdf</b>.</p>

<h2 class="bloco">2. Preparação da demonstração (antes de entrar na sala)</h2>
<table><tr><th>Quando</th><th>O que fazer</th><th>Quem</th></tr>
<tr><td>Véspera</td><td>Rodar a demo inteira uma vez e <b>gravar em vídeo</b> (Win + Alt + R). É o plano B se a internet cair.</td><td>Lucas</td></tr>
<tr><td>Véspera</td><td>Conferir que a stack <code>xyz-docs</code> está em CREATE_COMPLETE e que <code>APP_CHECK</code> está <b>true</b>.</td><td>Gabriel</td></tr>
<tr><td>30 min antes</td><td>Abrir terminal em <code>demo-aws/app</code> e rodar <code>python -m http.server 8000 --bind 127.0.0.1</code>.</td><td>Lucas</td></tr>
<tr><td>15 min antes</td><td>Fazer login do <b>cliente-a</b> e do <b>cliente-b</b> em duas abas de <code>localhost:8000</code> (o token dura 60 min). Enviar um PDF pelo cliente-b e copiar a chave dele. No cliente-a, enviar <code>relatorio-2024-cliente-a.pdf</code> com "Simular documento com mais de 365 dias" marcado.</td><td>Lucas</td></tr>
<tr><td>15 min antes</td><td>Deixar abertas: a aba do cliente-a, o console da Lambda em Configuração → Variáveis de ambiente e o CloudTrail filtrado por AssumeRole.</td><td>Lucas</td></tr>
<tr><td>Depois da demo</td><td>Voltar <code>APP_CHECK</code> para <b>true</b>.</td><td>Lucas</td></tr></table>
<div class="caixa laranja"><b class="t">Se algo falhar ao vivo</b>Token expirado (401 no meio): clique em Sair e entre de novo. Sem internet: mostre o vídeo ou os prints 23 a 36 do Manual da Demo. Nunca tente consertar na frente da banca por mais de 20 segundos.</div>

<h2 class="bloco">3. Roteiro por integrante</h2>
<div class="orador"><span>Athos</span><span>3 minutos</span></div>
<ul><li>Abrir com o número (50 mil/mês) e com os três problemas: gargalo, isolamento entre clientes e custo que cresce com o histórico.</li>
<li>Requisitos funcionais e não funcionais sem nomear serviços ainda.</li>
<li>Fechar com a visão em quatro passos: identifica, autoriza, entrega uma chave temporária, guarda e arquiva.</li></ul>
<div class="orador"><span>Jhonatan</span><span>3 minutos</span></div>
<ul><li>Seguir o diagrama pelos números das setas: Cognito → API Gateway → Lambda ↔ STS → URL → S3.</li>
<li>Para cada serviço: o que faz, por que foi escolhido, como se conecta. Citar KMS, GuardDuty, CloudWatch e CloudTrail.</li>
<li>Nomear a alternativa descartada antes da escolhida (EC2, Function URL, EFS, bucket por cliente, SSE-S3, Glacier Instant).</li></ul>
<div class="orador"><span>Gabriel</span><span>3 minutos</span></div>
<ul><li>Escala com números: ~1,2 documento/min, 10 req/s por rota, 10 mil req/s na conta, ~250 ms por autorização.</li>
<li>Resiliência: multi-AZ, RPO ~0 por gravação em 3+ zonas, região fora = dados intactos + CloudFormation; por que não replicar (LGPD).</li>
<li>Segurança em três camadas e por que não há VPC. Custos em São Paulo (~US$ 60/mês, 92% de economia no histórico, GuardDuty justificado).</li></ul>
<div class="orador"><span>Lucas</span><span>3 minutos</span></div>
<ul><li>Demo em cinco momentos: sem login (401), upload (204), ataque bloqueado pela aplicação (403), ataque com bug simulado bloqueado pelo S3 (403 AccessDenied), Deep Archive (409 → 202).</li>
<li>O momento-chave é o quarto: dizer devagar que o isolamento não depende de o código lembrar de checar.</li></ul>
<div class="orador"><span>Rafael</span><span>1,5 minuto</span></div>
<ul><li>Evolução: fila SQS para a IA, pipeline de deploy sobre o CloudFormation, Object Lock, Macie e treino em ambiente separado.</li>
<li>Fechar pela estrutura do guia: problema, o que foi construído, benefícios, próximos passos.</li></ul>

<h2 class="bloco">4. Perguntas mais prováveis (resposta-síntese)</h2>
<p>Todos devem saber a resposta curta de cada tema, mesmo sem ter apresentado aquele slide. As respostas completas estão no <b>Banco_de_Perguntas_da_Banca.pdf</b>.</p>
<table><tr><th>Tema</th><th>Pergunta</th><th>Resposta-síntese</th></tr>
<tr><td>Arquitetura</td><td>Por que esse serviço? Qual a alternativa?</td><td>Citar a alternativa descartada e o motivo objetivo (EC2 ocioso, Function URL sem authorizer JWT, EFS sem classes de arquivo).</td></tr>
<tr><td>Segurança</td><td>Quem acessa o quê? E se a URL vazar?</td><td>Cada usuário só alcança a própria pasta, por credencial do STS. A URL vale 15 min (upload) ou 5 min (download), para um objeto; revogar as sessões da role invalida todas.</td></tr>
<tr><td>Custos</td><td>O que é mais caro? E com 10x?</td><td>O ano em S3 Standard, depois o GuardDuty. Com 10x o custo cresce proporcional (~US$ 580/mês), sem degrau de servidor.</td></tr>
<tr><td>Escala</td><td>Existe gargalo?</td><td>Só cotas de conta (Lambda, STS, KMS), ajustáveis. O arquivo não passa pelo backend.</td></tr>
<tr><td>Recuperação</td><td>Quanto tempo para restaurar?</td><td>Standard: imediato. Versão apagada: segundos. Deep Archive: até 12 h. Infraestrutura: ~2 min pelo CloudFormation.</td></tr>
<tr><td>LGPD</td><td>E o direito de exclusão?</td><td>"Nunca apagar" é regra de negócio, não trava técnica absoluta: a exclusão definitiva existe por um processo controlado (conta root), registrado no CloudTrail.</td></tr></table>

<h2 class="bloco">5. O que evitar</h2>
<ul><li><b>Ler os slides.</b> O slide é apoio; a banca quer ouvir a explicação.</li>
<li><b>Gastar metade do tempo no problema.</b> Três minutos no máximo até entrar na arquitetura.</li>
<li><b>Deixar a demo para o último minuto.</b> Os três minutos do Lucas são protegidos: se alguém atrasar, corta do próprio bloco.</li>
<li><b>Prometer o que não foi feito.</b> Alarme de billing e replicação entre regiões não estão ativos; o GuardDuty está no desenho mas não na demo (plano gratuito). Se perguntarem, diga exatamente isso.</li></ul>
<div class="caixa verde"><b class="t">Regra de Ouro (guia do TCC)</b>Ao final, a banca deve conseguir responder: qual problema o grupo resolveu, como a solução resolve e por que essa foi a melhor escolha considerando segurança, disponibilidade, escalabilidade e custos. Cada integrante encerra seu bloco reforçando uma dessas três respostas.</div>
"""
    imprimir("roteiro_v2.html", pagina("ROTEIRO DE APRESENTAÇÃO", corpo), "Roteiro_de_Apresentacao_v2.pdf")


# ----------------------------------------------------------------------------- BANCO DE PERGUNTAS
PERGUNTAS = {
    "Arquitetura": [
        ("Por que serverless e não EC2?", "Jhonatan",
         "O volume é ~1,2 documento por minuto e irregular. Uma EC2 ficaria ociosa quase o tempo todo e ainda exigiria escalar, aplicar patches e balancear. Com Lambda e API Gateway pagamos por requisição e não há servidor para cair ou dimensionar."),
        ("Por que API Gateway e não Lambda Function URL?", "Jhonatan",
         "A Function URL só autentica com IAM ou fica aberta. O API Gateway tem authorizer JWT nativo do Cognito, limite de requisições por rota, domínio próprio e log de acesso. Barrar token inválido antes da Lambda também economiza execução."),
        ("Por que HTTP API e não REST API?", "Jhonatan",
         "A HTTP API é mais barata (US$ 1,59 por milhão em São Paulo) e já tem authorizer JWT. A REST API só faria sentido se precisássemos de WAF direto no Gateway ou de planos de uso por cliente."),
        ("Por que S3 e não EFS, RDS ou DynamoDB para os arquivos?", "Jhonatan",
         "Os documentos são gravados uma vez e lidos poucas vezes. O S3 tem 11 noves de durabilidade, classes de custo para arquivamento e URL pré-assinada. EFS é sistema de arquivos compartilhado, mais caro e sem classe de arquivo profundo; banco de dados não é lugar de binário."),
        ("Por que não checar a permissão só no código?", "Lucas",
         "Porque código tem bug. Um erro de autorização (IDOR) deixaria o usuário A ler o B. Com a credencial do STS restrita à pasta, mesmo com bug a AWS nega. Mostramos isso ao vivo desligando a checagem."),
        ("Por que um bucket com uma pasta por cliente e não um bucket por cliente?", "Jhonatan",
         "A AWS permite até 1 milhão de buckets, então não é limite. É operação: cada bucket seria mais uma política, um ciclo de vida e uma configuração de chave. Com um bucket e credencial por pasta temos o mesmo isolamento, uma configuração só e o histórico reunido para a IA."),
        ("Como o usuário lista os documentos dele?", "Lucas",
         "A Lambda lista com a mesma credencial restrita, e a session policy só permite ListBucket com a condição s3:prefix igual à pasta dele. É exatamente aqui que essa condition key vale. Para busca por nome ou status, a evolução é uma tabela de metadados no DynamoDB."),
        ("Onde fica o nome original do arquivo?", "Jhonatan",
         "O servidor gera o nome como UUID, para evitar colisão e nomes maliciosos. O nome original pode ir como metadado do objeto ou numa tabela de metadados."),
    ],
    "Segurança": [
        ("E se a URL pré-assinada vazar?", "Gabriel",
         "Ela vale como um ingresso: quem tiver pode usar. Por isso vale 15 minutos para upload e 5 para download, para um único objeto, só por HTTPS. Se vazar, a aba Revogar sessões da role invalida na hora todas as URLs já assinadas. Tudo fica no CloudTrail."),
        ("Quem pode acessar os recursos?", "Gabriel",
         "O usuário só alcança a própria pasta. A Lambda não tem acesso ao bucket: ela só pode assumir a role de acesso, e reduz essa role a uma pasta por pedido. Só a conta root consegue apagar uma versão de vez. O bucket é fechado ao público."),
        ("Por que não há VPC, subnets e Security Groups?", "Gabriel",
         "Nenhum componente precisa de rede privada: não há banco nem servidor. Colocar a Lambda numa VPC adicionaria NAT Gateway (custo fixo) sem ganho. O controle está em IAM, na política do bucket, na exigência de TLS e no limite de requisições."),
        ("E ataque de negação de serviço?", "Gabriel",
         "O AWS Shield Standard é automático. O API Gateway limita cada rota a 10 req/s com pico de 20 e responde 429 acima disso. Se precisar de regras por IP, colocamos WAF (via REST API ou CloudFront)."),
        ("E se alguém enviar um arquivo malicioso?", "Gabriel",
         "A URL de upload só aceita PDF, PNG e JPEG até 20 MB. No desenho, o GuardDuty escaneia cada objeto novo e marca com uma tag; o parâmetro EnforceMalwareScan faz o app ler só arquivos marcados como limpos. Na demo ele não aparece porque o plano gratuito da AWS bloqueia o GuardDuty."),
        ("Criptografia é exigência da LGPD?", "Gabriel",
         "A LGPD pede medidas de segurança adequadas (art. 46), sem nomear tecnologia. Usamos KMS com chave própria porque dá controle da chave e registro de uso. Com Bucket Keys o KMS registra por bucket, então a auditoria por objeto vem do CloudTrail."),
        ("Vocês usaram a conta root?", "Gabriel",
         "Na demo, sim. Em produção: MFA no root, acesso pelo IAM Identity Center e root só para emergência, que é inclusive quem pode apagar versões."),
    ],
    "LGPD e negócio": [
        ("'Nunca apagar' não conflita com o direito de exclusão (art. 18)?", "Athos",
         "É regra de negócio, não trava técnica absoluta. Aplicação e administradores não conseguem apagar; a exclusão definitiva existe por um processo controlado com a conta root, registrado no CloudTrail. O contrato define o prazo de retenção."),
        ("Pode usar documento de cliente para treinar IA?", "Rafael",
         "Só com base legal no contrato ou consentimento. Na evolução: Macie para achar dados pessoais, anonimização e treino num ambiente separado, sem acesso ao bucket de produção."),
        ("Por que não replicar para outra região?", "Gabriel",
         "O Brasil tem uma região AWS. Replicar seria mandar dado pessoal para fora do país (transferência internacional, art. 33) e custaria ~US$ 7 por mês só de transferência (US$ 0,138/GB saindo de São Paulo), fora as gravações na outra região. Falha regional afeta acesso, não a durabilidade. Se um contrato exigir, é uma regra de replicação a mais."),
    ],
    "Custos": [
        ("Qual o recurso mais caro?", "Gabriel",
         "O ano de documentos em S3 Standard (~US$ 24/mês), depois o GuardDuty (~US$ 20). No 3º ano o total fica em ~US$ 60/mês em São Paulo."),
        ("O que acontece com 10 vezes a demanda?", "Gabriel",
         "O custo cresce proporcional, sem degrau: ~US$ 580/mês (6 TB em Standard, 18 TB em Deep Archive, GuardDuty para 500 mil uploads). Não entra servidor nem licença."),
        ("Como reduzir mais?", "Rafael",
         "Standard-IA ou Intelligent-Tiering depois de 30 a 90 dias, se o acesso cair antes de um ano; Lambda em ARM (cerca de 20% mais barata); escanear só os tipos de arquivo que o parser abre."),
        ("Por que Deep Archive e não Glacier Instant Retrieval?", "Gabriel",
         "Em São Paulo, Deep Archive custa US$ 0,0032/GB e Glacier Instant US$ 0,0083. Depois de um ano o acesso é raro. Se o treino de IA ler o histórico com frequência, trocamos a regra para Glacier Instant."),
        ("E objetos pequenos?", "Gabriel",
         "Objetos com menos de 128 KB não mudam de classe por padrão, porque a taxa de transição não compensaria. Ficam em Standard, com custo irrelevante."),
        ("Por que não mostraram a Pricing Calculator?", "Gabriel",
         "Calculamos com a AWS Price List oficial de São Paulo, item a item. Se a banca quiser, a mesma conta pode ser montada na calculadora."),
    ],
    "Escalabilidade e recuperação": [
        ("Existe gargalo?", "Gabriel",
         "Só cotas de conta: concorrência da Lambda (1.000 por padrão), taxa de chamadas ao STS e ao KMS (Bucket Keys reduzem), ajustáveis com pedido. O S3 aguenta 3.500 gravações por segundo por prefixo, e cada usuário tem o seu."),
        ("O que acontece num pico?", "Gabriel",
         "Acima de 10 req/s por rota a API responde 429 e o app tenta de novo com espera crescente. Como o arquivo vai direto ao S3, o pico não chega ao backend."),
        ("Quanto tempo para restaurar?", "Gabriel",
         "Documento em Standard: imediato. Versão sobrescrita ou apagada: segundos, pelo versionamento. Documento em Deep Archive: até 12 horas (ou 48 h no modo mais barato). Infraestrutura inteira: ~2 minutos pelo CloudFormation."),
        ("E se a Lambda falhar?", "Lucas",
         "O alarme de erros dispara, o app tenta de novo e nada se perde, porque o arquivo não passa pela Lambda. Se o erro for no código, a versão anterior é republicada pelo template."),
    ],
    "Demonstração": [
        ("Isso está rodando de verdade?", "Lucas",
         "Sim, na conta do grupo em São Paulo, stack xyz-docs. O CloudTrail mostra cada credencial emitida e os logs da API mostram cada chamada, inclusive o 403 do ataque."),
        ("Por que o GuardDuty não aparece na demo?", "Lucas",
         "O plano gratuito da AWS bloqueia o serviço. A arquitetura e o template já estão prontos para ele (parâmetro EnforceMalwareScan)."),
        ("Outra pessoa consegue recriar o projeto?", "Rafael",
         "Sim: o template CloudFormation cria os 26 recursos em ~2 minutos, e o README e o Manual da Demo explicam cada passo com prints."),
    ],
}


def gerar_perguntas():
    corpo = [f'<h1>Banco de Perguntas da Banca</h1><p class="subtitulo">Startup XYZ — Gestão de Documentos para IA | Respostas curtas, com quem responde</p>',
             f'<div class="equipe">Equipe: {EQUIPE}</div><hr class="lar">',
             '<p>A banca pode direcionar qualquer pergunta a qualquer integrante. O nome em laranja indica quem responde primeiro; os outros complementam só se faltar algo. Responda em duas ou três frases e pare: a banca pergunta de novo se quiser mais.</p>']
    total = 0
    for tema, qs in PERGUNTAS.items():
        corpo.append(f'<div class="tema">{html.escape(tema)}</div>')
        for p, quem, r in qs:
            total += 1
            corpo.append(f'<div class="q"><span class="perg">{html.escape(p)}</span><span class="quem">{quem}</span><p class="resp">{md(r)}</p></div>')
    imprimir("perguntas.html", pagina("BANCO DE PERGUNTAS", "\n".join(corpo)), "Banco_de_Perguntas_da_Banca.pdf")
    return total


if __name__ == "__main__":
    resumo = gerar_falas()
    gerar_roteiro(resumo)
    n = gerar_perguntas()
    for quem, tempo, palavras in resumo:
        print(f"  {quem:9s} {tempo:12s} {palavras} palavras")
    print(f"  total: {sum(p for *_, p in resumo)} palavras | {n} perguntas")

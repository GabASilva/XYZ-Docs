"""Gera Analise_Apresentacao_HA_FinOps.pdf no visual dos outros documentos do projeto.

Uso: python docs-src/gerar_analise.py
Usa o mesmo Chrome do gerar_docs.py. Em outro sistema, aponte a variável CHROME para o executável.

Preços: AWS Price List API (publicação de 28/09/2026), região sa-east-1 salvo indicação.
Premissas do modelo: 50 mil documentos/mês, 1 MB em média, ~4 chamadas de API por documento.
"""
import os

import gerar_docs as base

base.CHROME = os.environ.get("CHROME") or base.CHROME

CSS_EXTRA = """
<style>
h2.bloco { margin-top: 22px; }
.item { break-inside: avoid; border-left: 3px solid #DCE2EA; padding: 4px 0 4px 10px; margin: 8px 0; }
.item b.tit { color: #14294A; }
.item .lin { margin: 2px 0; text-align: left; }
.item .lin span { display: inline-block; min-width: 92px; color: #6B7888; font-size: 9pt; font-weight: bold; }
.grave { border-left-color: #B23A3A; }
td.num { text-align: right; white-space: nowrap; }
tr.dest td { background: #E9F3EC !important; font-weight: bold; }
.nota { font-size: 9pt; color: #4C5A6B; }
</style>
"""


def item(titulo, linhas, grave=False):
    corpo = "".join(f'<p class="lin"><span>{k}</span>{v}</p>' for k, v in linhas)
    return f'<div class="item{" grave" if grave else ""}"><b class="tit">{titulo}</b>{corpo}</div>'


def tabela(cab, linhas, destaque=()):
    th = "".join(f"<th>{c}</th>" for c in cab)
    trs = []
    for i, l in enumerate(linhas):
        tds = "".join(f'<td class="num">{c}</td>' if j and isinstance(c, str) and c[:1] in "US~+−-0123456789" and len(c) < 16 else f"<td>{c}</td>"
                      for j, c in enumerate(l))
        trs.append(f'<tr{" class=dest" if i in destaque else ""}>{tds}</tr>')
    return f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>"


# ----------------------------------------------------------------------------- 1. DIVERGÊNCIAS
DIVERGENCIAS = [
    ("A. Infraestrutura e código", [
        ("1. Região", [
            ("Apresentação", "us-east-1 (Virgínia), 9 vezes, inclusive nos preços."),
            ("Real", "tudo foi criado em <b>sa-east-1 (São Paulo)</b>: manual, prints e template."),
            ("Por quê", "a banca vê “sa-east-1” no console durante a demo. Os preços de São Paulo são bem maiores (S3 Standard: US$ 0,0405/GB contra 0,023)."),
            ("Ajuste", "trocar a região e usar os preços da seção 4.")], True),
        ("2. Ferramenta de IaC", [
            ("Apresentação", "“Toda a infraestrutura foi codificada em Terraform” (slide 13 e <code>main.tf</code> na aba Código)."),
            ("Real", "é <b>CloudFormation</b>: <code>demo-aws/infra/template.base.yaml</code>, gerado por <code>build_template.py</code>. Não existe Terraform no projeto."),
            ("Ajuste", "dizer CloudFormation: nativo, sem arquivo de estado, recria a pilha em ~2 minutos.")], True),
        ("3. Testes PyTest (slide 14)", [
            ("Apresentação", "“suíte que comprova matematicamente o isolamento”."),
            ("Real", "não há testes no repositório. O teste exibido nem usa a política que gera: só compara duas strings."),
            ("Ajuste", "remover. A prova real de isolamento é a demo com <code>APP_CHECK=false</code> (item 11).")], True),
        ("4. Código da Lambda (aba Código)", [
            ("Apresentação", "<code>presigner.py</code>."),
            ("Real", "é <code>demo-aws/lambda/app.py</code>. A versão exibida falharia na AWS: a session policy não tem <code>kms:GenerateDataKey</code>, então o upload num bucket SSE-KMS é negado. Também não valida tipo nem tamanho e grava tudo como <code>.pdf</code>."),
            ("Ajuste", "mostrar o <code>app.py</code> (valida PDF/PNG/JPG, limite de 20 MB, 4 rotas).")], True),
        ("5. API", [
            ("Apresentação", "uma rota, <code>POST /documents/presigned-url</code>, e um <code>openapi.json</code>."),
            ("Real", "4 rotas: <code>POST /upload-url</code>, <code>GET /files</code>, <code>GET /download-url</code> e <code>POST /restore</code>. Não existe OpenAPI.")]),
        ("6. Tamanho máximo", [
            ("Apresentação", "“arquivos de até 50 MB”."),
            ("Real", "<b>20 MB</b>, imposto pelo <code>content-length-range</code> da URL assinada.")]),
        ("7. Nome original nos metadados", [
            ("Real", "o código não grava o nome original. Remover a frase.")]),
        ("8. “Arquitetura Event-Driven”", [
            ("Real", "não há nenhum evento ou EventBridge implementado. Remover o termo.")]),
    ]),
    ("B. Erros técnicos de segurança", [
        ("9. “HMAC Tampering” no JWT", [
            ("Real", "o Cognito assina com <b>RS256</b> (assimétrico: chave privada e chave pública). HMAC usa chave compartilhada. O próprio token de exemplo da apresentação começa com <code>{\"alg\":\"RS256\"}</code>."),
            ("Ajuste", "“adulteração de assinatura RS256”: o API Gateway confere a assinatura com a chave pública do Cognito (JWKS).")], True),
        ("10. Path traversal “bloqueado pelo STS com 403”", [
            ("Real", "o motivo está errado. O S3 não interpreta <code>..</code>: <code>usuario-123/../usuario-456/x</code> é só um nome literal <b>dentro</b> da pasta do usuário 123, e a política até permitiria."),
            ("Ajuste", "“o ataque não funciona porque no S3 a chave é literal e nunca sai do prefixo do usuário”.")], True),
        ("11. “A claim sub elimina IDOR”", [
            ("Real", "o <code>sub</code> impede escolher a pasta no upload. No download a defesa tem duas camadas: a Lambda recusa a chave alheia e, mesmo com bug na Lambda (<code>APP_CHECK=false</code>), a credencial do STS não alcança outra pasta."),
            ("Ajuste", "essa demonstração é o ponto mais forte do projeto e não aparece na apresentação. Deve entrar.")], True),
        ("12. “TLS 1.2+ obrigatório” (pergunta 5 da banca)", [
            ("Real", "o bucket exige TLS (<code>aws:SecureTransport</code>), mas não fixa a versão."),
            ("Ajuste", "dizer “TLS obrigatório”.")]),
    ]),
    ("C. Antimalware: slide 11 e passo 7", [
        ("13. GuardDuty + EventBridge + Lambda de Resposta + Bucket de Ameaças", [
            ("Real", "nada disso existe. O template tem só o parâmetro opcional <code>EnforceMalwareScan</code>, desligado por padrão, que faz o app ler apenas arquivos marcados como limpos."),
            ("Contradição", "o passo 7 “destrói o arquivo em todas as versões”, mas a regra central do case é <b>nunca apagar</b>. A política do bucket nega <code>DeleteObjectVersion</code> para todos menos o root: a Lambda de Resposta seria bloqueada pelo próprio projeto."),
            ("Risco", "se o GuardDuty der falso positivo, o documento legítimo do cliente some para sempre."),
            ("Exageros", "“cada incidente deixa o sistema mais esperto”: o hash só reconhece o arquivo idêntico, e nada consulta esse banco. A simulação usa <code>.exe</code>, que a API real recusa."),
            ("Ajuste", "mover para “Evolução”, com <b>quarentena com prazo</b> em vez de destruição.")], True),
    ]),
    ("D. Custos (slides 12 e 15, calculadora FinOps)", [
        ("14. “95,8% de economia contra uma arquitetura legada de ~US$ 450/mês”", [
            ("Real", "o valor de US$ 450 foi inventado. A fórmula no código é <code>450 + docs/1000 × 0,50</code>, sem fonte."),
            ("Ajuste", "comparar com alternativas reais em São Paulo: 2 EC2 t4g.small + ALB ≈ <b>US$ 80/mês</b>; Fargate ≈ <b>US$ 72/mês</b>; camada serverless do projeto ≈ <b>US$ 2,50/mês</b>. Sem lifecycle, o armazenamento custaria US$ 73,69/mês no 3º ano, contra US$ 35,47 com lifecycle (−52%).")], True),
        ("15. “Custo total ~US$ 18,78/mês”", [
            ("Real", "em São Paulo, com a configuração atual: <b>~US$ 26/mês no 1º ano e ~US$ 35/mês no 3º</b>. O GuardDuty, que a apresentação diz estar ligado, soma <b>+US$ 20,66/mês</b> e seria o maior item da conta.")], True),
        ("16. “Deep Archive: −95%”", [
            ("Real", "em São Paulo vai de US$ 0,0405 para US$ 0,0032 por GB: <b>−92%</b>. Os 95% são de Virgínia.")]),
    ]),
    ("E. Estrutura exigida pelo guia oficial", [
        ("17. Slides que faltam", [
            ("Faltam", "tabela “requisito × como foi atendido” (slide 8 do guia), Resiliência (10), Backup e Recuperação (13), Demonstração (14, trocada por “Testes PyTest”), requisitos funcionais e não funcionais separados (3) e alternativas consideradas (7).")], True),
        ("18. Capa", [("Ajuste", "colocar os nomes da equipe; o guia exige.")]),
        ("19. Notas do orador", [("Ajuste", "estão para 4 alunos em 15 min. A equipe tem 5, e o roteiro v2 prevê ~13,5 min.")]),
        ("20. Slide final", [("Ajuste", "trocar “Projeto TCC Concluído com Sucesso!” por problema → solução → benefícios → próximos passos.")]),
    ]),
]


def secao1():
    out = ['<h2 class="bloco">1. O que não bate entre a apresentação e o projeto</h2>',
           '<p>Arquivo analisado: <code>Arquitetura_V3_Apresentacao_4.html</code>. Itens com barra vermelha são os que a banca '
           'consegue desmentir abrindo o console ou o repositório.</p>']
    for grupo, itens in DIVERGENCIAS:
        out.append(f'<div class="tema">{grupo}</div>')
        out += [item(t, l, g[0] if g else False) for t, l, *g in itens]
    return "\n".join(out)


# ----------------------------------------------------------------------------- 2. HA E ELASTICIDADE
def secao2():
    return f"""
<h2 class="bloco">2. Alta disponibilidade e elasticidade: o que mudar no projeto</h2>
<div class="caixa"><b class="t">O argumento base</b>Num projeto serverless não existe servidor para derrubar: Cognito, API Gateway, Lambda e S3
já rodam em várias zonas de disponibilidade. Pelos SLAs contratuais (Lambda 99,95%, API Gateway 99,95%, Cognito 99,9%, S3 99,9%),
a disponibilidade composta fica em torno de <b>99,7%</b> sem configuração extra. O que falta é <b>tornar isso visível</b>.</div>

<div class="tema">Elasticidade</div>
{tabela(["Mudança", "O que a banca vê", "Custo"], [
    ["<b>Script de teste de carga</b> (<code>demo-aws/carga/teste_carga.py</code>): login no Cognito e 1.000 pedidos de <code>/upload-url</code>, 50 em paralelo. Mostra latência p50/p95 e contagem de 200 e 429.",
     "No dashboard, a concorrência da Lambda sobe de 1 para dezenas e volta a 0, com latência estável e sem erros.", "~US$ 0,003 por rodada"],
    ["<b>Gráfico <code>ConcurrentExecutions</code></b> no dashboard (hoje não existe).", "A curva de escala em tempo real.", "Grátis"],
    ["<b>Throttling como parâmetro da pilha</b> (hoje fixo em 10 req/s, rajada de 20).",
     "Rodada 1, limite baixo: 429 barrados na borda, sem custo de Lambda (“freio de custo”). Rodada 2: sobe o limite (update de ~1 min) e a carga passa toda.", "Grátis"],
])}
<div class="caixa laranja"><b class="t">Antes da demo</b>Em Service Quotas, conferir o limite de “Concurrent executions” da Lambda.
Contas novas às vezes vêm com apenas 10, e com esse limite o teste de carga falha.</div>
<p>Números úteis para a banca: média de 50 mil por mês ≈ <b>1,2 documento por minuto</b>. Cada prefixo do S3 aguenta 3.500 PUT/s
e há um prefixo por usuário, então a capacidade cresce com o número de clientes. O gargalo real a monitorar é a cota de login do Cognito.</p>

<div class="tema">Alta disponibilidade e recuperação</div>
{tabela(["Mudança", "O que a banca vê", "Custo"], [
    ["<b>Variável <code>FAULT_RATE</code></b> na Lambda (mesmo padrão do <code>APP_CHECK</code>), que faz X% das chamadas falharem, mais <b>retry com backoff</b> no <code>index.html</code>.",
     "Com 50% de falha, o alarme dispara e o e-mail chega, mas o usuário completa o upload (“tentativa 1 falhou, 2 OK”).", "Grátis"],
    ["Versão profissional do mesmo teste: <b>AWS Fault Injection Service</b> com ação de erro na Lambda.", "O mesmo resultado, com ferramenta de caos de mercado.", "Centavos por teste"],
    ["<b>Replicação entre regiões (CRR)</b> para um bucket em us-east-1, gravando direto em Deep Archive.",
     "Upload em São Paulo e o arquivo aparece em Virgínia: DR regional funcionando.", "~US$ 9/mês (pesa a transferência SP→EUA, US$ 0,138/GB)"],
    ["<b>Restauração de versão</b> pelo console (“Mostrar versões”).", "Arquivo sobrescrito e a versão anterior volta: proteção contra erro humano e ransomware.", "Grátis"],
    ["<b><code>DeletionPolicy: Retain</code></b> no bucket e na chave KMS.", "Apaga a pilha, recria em ~2 min e os dados continuam lá: RTO medido ao vivo.", "Grátis"],
])}
<div class="caixa laranja"><b class="t">Achado real no template</b>Hoje o template <b>não tem</b> <code>DeletionPolicy</code>. Se alguém excluir a pilha,
a chave KMS entra em exclusão agendada e, quando for apagada, <b>todos os documentos ficam ilegíveis para sempre</b>, mesmo com o bucket preservado.
Para a demo, isso pode virar um parâmetro.</div>
<div class="caixa verde"><b class="t">Recomendação</b>Teste de carga com throttling parametrizado, <code>FAULT_RATE</code> com retry e <code>DeletionPolicy</code>:
é barato, roda ao vivo e responde direto ao comentário do professor. A replicação entre regiões fica como opcional, porque custa todo mês.</div>
"""


# ----------------------------------------------------------------------------- 3. ALTERNATIVAS
def secao3():
    return f"""
<h2 class="bloco">3. Serviços alternativos e por que não foram usados</h2>
<p class="nota">Preços de São Paulo (sa-east-1).</p>
{tabela(["Em uso", "Alternativa", "Por que não"], [
    ["<b>Cognito</b>", "Auth0/Okta, Keycloak em EC2, IAM Identity Center", "10 mil usuários ativos/mês grátis e integração nativa com o autorizador JWT. Auth0 cobra por usuário e guarda os dados fora da AWS. Keycloak exige servidor. Identity Center é para funcionários, não clientes."],
    ["<b>API Gateway HTTP API</b>", "REST API", "US$ 4,25 contra <b>US$ 1,59</b> por milhão. A REST traz WAF, cache e <i>usage plans</i>; vale como evolução, pois usage plans permitem cobrar planos por cliente."],
    ["", "Lambda Function URL", "Grátis, mas sem autorizador JWT e sem throttling por rota: a segurança teria que ser escrita no código."],
    ["", "ALB", "~US$ 25/mês fixos mesmo sem uso."],
    ["<b>Lambda</b>", "EC2 (2 instâncias + ALB)", "~<b>US$ 80/mês</b> contra ~US$ 0,30 da Lambda. Com 1,2 req/min o servidor fica ocioso mais de 99% do tempo, e ainda exige patch e escala."],
    ["", "ECS Fargate", "~<b>US$ 72/mês</b> com 2 tarefas para alta disponibilidade."],
    ["<b>STS + session policy</b>", "Cognito Identity Pool", "O navegador receberia credenciais AWS direto: superfície de ataque maior e sem como impor tipo e tamanho de arquivo."],
    ["", "S3 Access Grants", "Feito para esse caso, mas cobra US$ 0,03 por mil pedidos (~US$ 6/mês). O STS é grátis."],
    ["", "Access Point ou bucket por cliente", "Limite de quantidade e uma política por cliente para gerenciar. Um bucket com prefixos escala sem isso."],
    ["", "ABAC com <i>session tags</i>", "Equivalente e grátis. Resposta honesta para a banca: “seria uma alternativa válida”."],
    ["<b>S3 Standard</b>", "EFS, DynamoDB, RDS", "EFS exige VPC e é várias vezes mais caro; DynamoDB limita cada item a 400 KB; banco de dados não é lugar de arquivo."],
    ["<b>Deep Archive</b>", "Glacier Flexible", "US$ 0,00765/GB, 2,4 vezes o Deep Archive. A vantagem é restaurar em minutos ou horas."],
    ["", "Glacier Instant / Intelligent-Tiering", "Não substituem, complementam. Ver alavanca nº 1 na seção 4."],
    ["<b>KMS com chave própria</b>", "SSE-S3 (grátis)", "Com chave própria há auditoria no CloudTrail, controle e revogação pela política da chave. Custa US$ 1/mês, e o Bucket Key zera quase todas as chamadas."],
    ["<b>GuardDuty</b> (opcional)", "ClamAV numa Lambda", "Mais barato em volume, mas vocês mantêm as assinaturas de vírus e o código. O GuardDuty é gerenciado."],
    ["<b>CloudFormation</b>", "Terraform, CDK, SAM", "Nativo e grátis, sem arquivo de estado. Terraform faz sentido com várias nuvens; o SAM simplificaria a parte da Lambda."],
    ["<b>sa-east-1</b>", "us-east-1", "A pilha sairia ~45% mais barata, mas: dados de clientes brasileiros no Brasil (LGPD, transferência internacional), menor latência e “dados no Brasil” como argumento de venda."],
])}
"""


# ----------------------------------------------------------------------------- 4. FINOPS
def secao4():
    return f"""
<h2 class="bloco">4. FinOps: o argumento de venda</h2>
<div class="caixa"><b class="t">Premissas</b>Preços da AWS Price List API (publicação de 28/09/2026), região sa-east-1. 50 mil documentos por mês,
1 MB em média (~48,8 GB/mês), ~4 chamadas de API por documento, Lambda de 256 MB com ~300 ms. Valores em dólar, sem descontar a camada gratuita.</div>

<div class="tema">Quanto custa hoje (configuração atual)</div>
{tabela(["Item / mês", "1º ano (mês 12)", "3º ano (mês 36)"], [
    ["S3 Standard (últimos 12 meses, ~586 GB)", "US$ 23,73", "US$ 23,73"],
    ["Deep Archive (histórico) + custo fixo por objeto", "—", "US$ 4,24"],
    ["Transições do lifecycle (US$ 0,10 por mil)", "—", "US$ 5,00"],
    ["API Gateway + Lambda + PUTs + KMS + CloudWatch", "US$ 2,50", "US$ 2,50"],
    ["<b>Total</b>", "<b>~US$ 26</b>", "<b>~US$ 35</b>"],
    ["+ GuardDuty (opcional)", "+US$ 20,66", "+US$ 20,66"],
], destaque=(4,))}
<ul>
<li><b>O S3 Standard é 67% da conta.</b> Lambda e API somam centavos: o custo está no primeiro ano de armazenamento.</li>
<li><b>Em São Paulo, mover para o Deep Archive custa mais que guardar nele</b> (US$ 5,00 em transições contra US$ 3,75 de armazenamento).</li>
<li><b>O GuardDuty custaria mais que toda a infraestrutura.</b> Por isso deve ser vendido como adicional.</li>
</ul>

<div class="tema">Cenários de armazenamento (alavanca nº 1)</div>
{tabela(["Cenário (total/mês)", "Mês 12", "Mês 24", "Mês 36", "Acumulado 3 anos"], [
    ["A. Tudo em Standard (sem lifecycle)", "26,23", "49,96", "73,69", "US$ 1.407"],
    ["B. Atual: Standard por 365 dias → Deep Archive", "26,23", "33,35", "35,47", "US$ 987"],
    ["C. 30 dias Standard → Glacier Instant → Deep Archive aos 365", "9,94", "17,06", "19,18", "US$ 504"],
    ["D. Intelligent-Tiering, arquivando no Deep Archive", "11,79", "15,41", "19,02", "US$ 480"],
], destaque=(2,))}
<p><b>Mudar uma regra do lifecycle corta ~49% do custo em 3 anos.</b> O cliente lê o documento nos primeiros dias, quando a IA extrai
as informações; depois o acesso é raro, e manter o arquivo um ano inteiro em Standard é desperdício.
No cenário C, ler um arquivo no Glacier Instant custa US$ 0,03/GB, mas continua em milissegundos, sem restore.
O cenário D se ajusta sozinho e não cobra leitura, mas cobra US$ 0,0025 por mil objetos por mês de monitoramento.</p>

<div class="tema">Outras alavancas (mudanças no template)</div>
<ul>
<li><b>Filtro de tamanho no lifecycle</b> (<code>ObjectSizeGreaterThan</code>): um arquivo de 1 MB paga a transição para o Deep Archive em 2,8 meses;
um de 128 KB leva 24 meses; um de 64 KB, 4,5 anos. Arquivar só acima de ~256 KB.</li>
<li><b>Tags de custo</b> (<code>Projeto=xyz-docs</code>) em todos os recursos e <b>Cost Anomaly Detection</b> (grátis). O template já tem Budget, mas não tem tags.</li>
<li><b>Custo por cliente (showback)</b>: S3 Inventory + Athena somam os GB por prefixo de cliente por menos de US$ 0,01/mês e permitem faturar pelo uso real.</li>
<li><b>Plano do Cognito</b>: confirmar se o user pool está no <b>Lite</b> (US$ 0,0055 por usuário ativo depois dos 10 mil grátis) e não no <b>Essentials</b> (US$ 0,015).</li>
</ul>

<div class="tema">Armadilhas para antecipar à banca</div>
<ul>
<li><b>Transferência de saída de dados é o custo escondido</b>: US$ 0,15/GB para a internet em São Paulo, depois de 100 GB grátis por mês.
Treinar a IA em outra região sai caro: ler 3 anos de histórico (1,76 TB) de Virgínia custaria ~US$ 243 só em transferência. Regra: processar na mesma região.</li>
<li><b>Restaurar o histórico é barato</b> se não for urgente: modo Bulk (até 48 h) a US$ 0,008/GB. Um ano inteiro de documentos sai por menos de US$ 5.</li>
<li><b>Logs do CloudWatch</b> custam US$ 0,90/GB em São Paulo. A retenção de 30 dias já está configurada.</li>
</ul>

<div class="tema">Como vender: custo unitário e planos</div>
{tabela(["Indicador", "Valor"], [
    ["Custo de infraestrutura por mil documentos novos/mês (hoje)", "US$ 0,71"],
    ["Mesmo indicador no cenário C", "US$ 0,38"],
    ["Volume 10 vezes maior (500 mil/mês), cenário C, 3º ano", "US$ 178/mês"],
    ["Só a computação de uma arquitetura tradicional com alta disponibilidade", "US$ 72–80/mês"],
], destaque=(1,))}
<p>O custo cresce de forma linear, sem degraus de servidor, e o custo fixo sem uso é praticamente zero.
Os planos podem seguir os adicionais, cada um com custo unitário conhecido:</p>
<ul>
<li><b>Básico</b>: isolamento, criptografia e histórico.</li>
<li><b>Pro</b>: + antimalware com GuardDuty (~US$ 0,41 por mil documentos).</li>
<li><b>Enterprise</b>: + cópia em outra região (~US$ 0,19 por mil documentos de 1 MB) e Object Lock.</li>
</ul>
<p>Assim o preço acompanha o custo, e cada cliente paga pelo nível de segurança que quer.</p>
"""


def gerar():
    corpo = [CSS_EXTRA,
             '<h1>Análise da Apresentação, Alta Disponibilidade e FinOps</h1>',
             '<p class="subtitulo">Startup XYZ — Gestão de Documentos para IA | O que corrigir nos slides, o que mostrar na demo e quanto custa</p>',
             f'<div class="equipe">Equipe: {base.EQUIPE}</div><hr class="lar">',
             '<p>A seção 1 é para quem cuida da apresentação: cada item diz o que está nos slides, o que existe de fato no projeto e como ajustar. '
             'As seções 2 a 4 são para quem cuida da demo e da conta AWS.</p>',
             secao1(), secao2(), secao3(), secao4()]
    base.imprimir("analise.html", base.pagina("ANÁLISE E FINOPS", "\n".join(corpo)), "Analise_Apresentacao_HA_FinOps.pdf")


if __name__ == "__main__":
    gerar()

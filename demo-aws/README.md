# Startup XYZ — Gestão de documentos para IA (demo do TCC)

Arquitetura serverless na AWS que recebe documentos de clientes, isola cada cliente, protege os arquivos e reduz o custo do histórico sem apagar nada.

```
Cliente ──login──▶ Cognito (JWT)
   │
   ├─ pede URL ─▶ API Gateway (valida JWT, throttling) ─▶ Lambda ─▶ STS (credencial de 15 min só do prefixo do usuário)
   │                                                        │
   ◀──────────────── URL pré-assinada ──────────────────────┘
   │
   └─ envia/baixa direto ─▶ S3 (privado, SSE-KMS, versioning) ──365 dias──▶ Glacier Deep Archive
```

## Estrutura

| Caminho | O que é |
|---|---|
| `infra/template.base.yaml` | Template CloudFormation (fonte). |
| `infra/template.yaml` | Template pronto para o deploy, com o código da Lambda embutido. Gerado por `infra/build_template.py`. |
| `lambda/app.py` | Código da Lambda de autorização. |
| `app/index.html` | Página da demonstração (login, upload, lista, teste de isolamento). |
| `app/amostras/` | PDFs de teste. |
| `manual/` | Manual passo a passo com prints do console. |

## Pré-requisitos

- Conta AWS com acesso ao console (região **sa-east-1**, São Paulo).
- Python 3 instalado (só para servir a página da demo em `localhost`).

## Deploy (resumo — detalhes e prints no manual)

1. Se alterou `lambda/app.py`, gere o template: `python infra/build_template.py`
2. Console → CloudFormation → **Criar pilha** → *Fazer upload de um arquivo de modelo* → `infra/template.yaml`
3. Nome da pilha: `xyz-docs`. Parâmetros:

| Parâmetro | Padrão | Para que serve |
|---|---|---|
| `AllowedOrigin` | `http://localhost:8000` | Origem liberada no CORS da API e do bucket. |
| `AlertEmail` | vazio | E-mail para alarmes e AWS Budget. Vazio = sem e-mail. |
| `MonthlyBudgetUSD` | `10` | Limite do AWS Budget. |
| `EnforceMalwareScan` | `false` | `true` = o app só lê objetos marcados como limpos pelo GuardDuty (exige GuardDuty Malware Protection ativo no bucket, que não está disponível no plano gratuito). |

4. Marque a caixa de capacidades do IAM e clique em **Enviar**. Leva cerca de 2 minutos.
5. Anote a aba **Saídas**: `ApiUrl`, `UserPoolClientId`, `Region`.
6. Cognito → grupo `xyz-docs-usuarios` → **Criar usuário** (dois usuários de teste, senha definida por vocês).

## Rodar a demo

```bash
cd app
python -m http.server 8000 --bind 127.0.0.1
```

Abra `http://localhost:8000`, preencha a Configuração com as saídas da pilha e faça login.

Variáveis de ambiente da Lambda (nenhuma credencial fica no código — a Lambda usa a role dela):

| Variável | Exemplo | Uso |
|---|---|---|
| `BUCKET` | `xyz-docs-<conta>` | Bucket dos documentos. |
| `ROLE_ARN` | `arn:aws:iam::<conta>:role/xyz-user-access-role` | Role que a Lambda assume com session policy. |
| `KMS_KEY_ARN` | `arn:aws:kms:sa-east-1:<conta>:key/...` | Chave do SSE-KMS. |
| `APP_CHECK` | `true` | `false` simula um bug de autorização para provar que o STS bloqueia mesmo assim. |

## Apagar tudo depois da apresentação

1. S3 → bucket `xyz-docs-<conta>` → **Esvaziar** (logado como root; a política do bucket só deixa o root apagar versões).
2. CloudFormation → pilha `xyz-docs` → **Excluir**.
3. A chave KMS entra em exclusão agendada (7–30 dias) e para de ser cobrada.
4. Opcional: apagar o bucket `cf-templates-...` que o CloudFormation cria ao fazer upload do template.

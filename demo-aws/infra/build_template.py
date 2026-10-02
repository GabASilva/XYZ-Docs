"""Gera infra/template.yaml embutindo lambda/app.py no ZipFile da funcao.
Uso: python infra/build_template.py
"""
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
base = (raiz / 'infra' / 'template.base.yaml').read_text(encoding='utf-8')
codigo = (raiz / 'lambda' / 'app.py').read_text(encoding='utf-8')
indentado = '\n'.join(('          ' + l) if l.strip() else '' for l in codigo.splitlines())
(raiz / 'infra' / 'template.yaml').write_text(base.replace('__LAMBDA_CODE__', indentado), encoding='utf-8')
print('infra/template.yaml gerado')

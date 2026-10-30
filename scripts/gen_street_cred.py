#!/usr/bin/env python3
"""Gera assets/street-cred.svg (RUN_07) com dados da API GraphQL do GitHub.

Calcula:
  - total de contribuições desde a criação da conta
  - streak atual (se hoje ainda não tem contribuição, conta até ontem)
  - maior streak, com as datas
  - número de repositórios públicos

contributionsCollection aceita no máximo 1 ano por consulta, então o script faz
uma consulta por ano, de createdAt até hoje. As datas são em UTC, como na API.
A consulta usa só a stdlib (urllib); o SVG usa tema.py pra embutir a fonte.

uso:
  GITHUB_TOKEN=... python3 scripts/gen_street_cred.py
  GH_USER muda o usuário consultado (padrão: daniykt).

Com o GITHUB_TOKEN padrão do Actions só entram contribuições públicas; um PAT
com read:user (secret GH_STATS_TOKEN no workflow) conta as privadas também.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

import tema
from tema import AMARELO, MAGENTA, BRANCO, TEXTO2, TEXTO3, BORDA_SEC, PAD, largura

API = 'https://api.github.com/graphql'
USUARIO = os.environ.get('GH_USER', 'daniykt')
MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
W = 840
BLOCO_H = 110
UM_DIA = timedelta(days=1)

Q_USUARIO = '''query($login: String!) {
  user(login: $login) {
    createdAt
    repositories(privacy: PUBLIC, ownerAffiliations: OWNER) { totalCount }
  }
}'''

Q_CALENDARIO = '''query($login: String!, $de: DateTime!, $ate: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $de, to: $ate) {
      contributionCalendar { weeks { contributionDays { date contributionCount } } }
    }
  }
}'''


def graphql(query, **variaveis):
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        sys.exit('defina GITHUB_TOKEN no ambiente')
    req = urllib.request.Request(
        API, data=json.dumps({'query': query, 'variables': variaveis}).encode(),
        headers={'Authorization': f'bearer {token}', 'Content-Type': 'application/json',
                 'User-Agent': 'daniykt-street-cred'})
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.load(r)
    if resp.get('errors'):
        sys.exit(f'erro da API: {resp["errors"]}')
    return resp['data']


def iso(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')


def contribuicoes(login, criado, agora):
    """{date: contagem} de criado até agora, uma consulta por ano."""
    dias, de = {}, criado
    while de < agora:
        ate = min(de + timedelta(days=365) - timedelta(seconds=1), agora)
        dados = graphql(Q_CALENDARIO, login=login, de=iso(de), ate=iso(ate))
        for semana in dados['user']['contributionsCollection']['contributionCalendar']['weeks']:
            for d in semana['contributionDays']:
                dia = datetime.fromisoformat(d['date']).date()
                if criado.date() <= dia <= agora.date():
                    dias[dia] = d['contributionCount']
        de = ate + timedelta(seconds=1)
    return dias


def streak_atual(dias, hoje):
    """(dias, início, fim). Se hoje ainda está zerado, a contagem vai até ontem."""
    fim = hoje if dias.get(hoje, 0) else hoje - UM_DIA
    ini = fim
    while dias.get(ini, 0):
        ini -= UM_DIA
    n = (fim - ini).days
    return (n, ini + UM_DIA, fim) if n else (0, None, None)


def maior_streak(dias):
    melhor, n, ini, anterior = (0, None, None), 0, None, None
    for dia in sorted(dias):
        if not dias[dia] or (anterior and dia != anterior + UM_DIA):
            n = 0
        if dias[dia]:
            if n == 0:
                ini = dia
            n += 1
            if n > melhor[0]:
                melhor = (n, ini, dia)
        anterior = dia
    return melhor


def data_pt(d, hoje, com_ano=False):
    s = f'{d.day} {MESES[d.month - 1]}'
    return f'{s} {d.year}' if com_ano or d.year != hoje.year else s


def periodo(ini, fim, hoje):
    """'27 out → 29 out'; o ano só aparece quando não é o atual."""
    if not ini:
        return 'sem streak ativo'
    if ini == fim:
        return data_pt(ini, hoje)
    if ini.year == fim.year:
        return f'{data_pt(ini, hoje.replace(year=ini.year))} → {data_pt(fim, hoje)}'
    return f'{data_pt(ini, hoje, True)} → {data_pt(fim, hoje, True)}'


def numero(n):
    return f'{n:,}'.replace(',', '.')


def bloco(F, x, y, w, rotulo, valor, cor, detalhe, unidade=None, destaque=False):
    borda = MAGENTA if destaque else BORDA_SEC
    c = [f'<rect x="{x + .5:g}" y="{y + .5}" width="{w - 1:g}" height="{BLOCO_H - 1}" fill="none" stroke="{borda}"/>',
         F.texto(x + 16, y + 28, rotulo, 11, 700, TEXTO3, espaco=1.5),
         F.texto(x + 16, y + 70, valor, 32, 800, cor)]
    if unidade:
        c.append(F.texto(x + 16 + largura(valor, 32, 800) + 8, y + 70, unidade, 13, cor=TEXTO2))
    tam = 12
    while largura(detalhe, tam) > w - 32 and tam > 9:
        tam -= .5
    c.append(F.texto(x + 16, y + 94, detalhe, tam, cor=TEXTO2))
    return ''.join(c)


def street_cred(total, desde, atual, maior, repos, hoje):
    F = tema.Fontes()
    gap = 12
    bw = (W - 2 * PAD - 3 * gap) / 4
    xs = [PAD + i * (bw + gap) for i in range(4)]
    desde_txt = f'desde {MESES[desde.month - 1]} {desde.year}'
    atual_txt, maior_txt = periodo(atual[1], atual[2], hoje), periodo(maior[1], maior[2], hoje)
    corpo = ''.join([
        bloco(F, xs[0], PAD, bw, 'CONTRIBUIÇÕES', numero(total), BRANCO, desde_txt),
        bloco(F, xs[1], PAD, bw, 'STREAK ATUAL', numero(atual[0]), AMARELO, atual_txt, 'dias', destaque=True),
        bloco(F, xs[2], PAD, bw, 'MAIOR STREAK', numero(maior[0]), BRANCO, maior_txt, 'dias'),
        bloco(F, xs[3], PAD, bw, 'REPOS', numero(repos), BRANCO, 'públicos'),
    ])
    titulo = (f'RUN_07 Street cred, atualizado todo dia. Contribuições: {numero(total)} {desde_txt}. '
              f'Streak atual: {atual[0]} dias ({atual_txt}). Maior streak: {maior[0]} dias ({maior_txt}). '
              f'Repos: {repos} públicos.')
    return tema.card_secao('RUN_07', 'STREET CRED', 7, corpo, PAD + BLOCO_H + PAD, F, titulo,
                           subtitulo='atualizado todo dia')


def main():
    agora = datetime.now(timezone.utc).replace(microsecond=0)
    hoje = agora.date()
    u = graphql(Q_USUARIO, login=USUARIO)['user']
    criado = datetime.fromisoformat(u['createdAt'].replace('Z', '+00:00'))
    dias = contribuicoes(USUARIO, criado, agora)
    atual, maior = streak_atual(dias, hoje), maior_streak(dias)
    total, repos = sum(dias.values()), u['repositories']['totalCount']
    print(f'{USUARIO}: {total} contribuições desde {criado.date()}, streak atual {atual[0]}, '
          f'maior {maior[0]}, {repos} repos públicos')
    tema.salvar('street-cred.svg', street_cred(total, criado.date(), atual, maior, repos, hoje))


if __name__ == '__main__':
    main()

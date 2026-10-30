#!/usr/bin/env python3
"""Gera as seções do README em SVG — tema Cyberpunk: Edgerunners.

Lê scripts/perfil.json e grava em assets/:
  identity.svg        RUN_01: imagem + terminal (bio, chrome, comms)
  charsheet.svg       RUN_02: retrato + ficha + atributos
  journal.svg         RUN_03: foco do momento como quest log
  gigs-titulo.svg     RUN_04: só a barra de título
  gig-<id>.svg        um card por projeto (o primeiro com 840, os outros com 412)
  chrome.svg          RUN_05: prosa + inventário de tecnologias com os logos (simple-icons, CC0)
  formacao.svg        RUN_06: formação + slot vazio pra certificados

Cada seção é um SVG só, com a barra de título dentro da moldura (tema.card_secao).
Valor 'TODO: x' do perfil.json aparece como '[x]'. Imagem que não existe vira
um placeholder listrado com o rótulo entre colchetes.

uso:  python3 scripts/gen_cards.py
"""
import itertools
import json
import os
import re

import tema
from tema import (AMARELO, MAGENTA, FUNDO, TEXTO, TEXTO2, TEXTO3, CINZA, VERDE,
                  BORDA_SEC, VAZIO, CHIP, PAD, esc, largura)

PERFIL = os.path.join(tema.HERE, 'perfil.json')
ICONES = os.path.join(tema.HERE, 'icones')

W = 840
W_GIG = 412                              # gigs secundários (dois lado a lado)
NUMERO = '#1e1e28'                       # numeração decorativa dos gigs (marca d'água, fora da checagem de contraste)
CLARO = tema.TEXTO2                      # secundário: objetivos, citação
APAGADO = tema.TEXTO3                    # terciário: comentários do terminal
SLOT = '#101018'                         # fundo dos slots do chrome
IDENTITY_STACK = ('Frontend', 'Backend')  # linhas de terminal.stack que aparecem na identity

ICONE = {
    'HTML': 'html5', 'CSS': 'css', 'JavaScript': 'javascript', 'TypeScript': 'typescript',
    'React': 'react', 'Vite': 'vite', 'Tailwind': 'tailwindcss', 'Node.js': 'nodedotjs',
    'Supabase': 'supabase', 'PostgreSQL': 'postgresql', 'Figma': 'figma', 'Git': 'git',
    'Next.js': 'nextdotjs', 'Vitest': 'vitest', 'Acessibilidade': 'acessibilidade',
}


def val(v):
    """'TODO: x' → '[x]'."""
    s = str(v)
    return f'[{s[6:]}]' if s.startswith('TODO: ') else s


def fundo(w, h):
    return f'<rect width="{w}" height="{h}" fill="{FUNDO}"/>'


def listras(F, x, y, w, h, rotulo, pid):
    """Placeholder de imagem: listras diagonais escuras + rótulo no centro."""
    return (f'<defs><pattern id="{pid}" width="12" height="12" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate(45)"><rect width="12" height="12" fill="#0f0f16"/>'
            f'<rect width="5" height="12" fill="#17171f"/></pattern></defs>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#{pid})"/>'
            + F.texto(x + w / 2, y + h / 2 + 4, rotulo, 12, cor=TEXTO3, anchor='middle'))


_avisados = set()


def imagem(F, caminho, x, y, w, h, rotulo, pid):
    uri = tema.img_base64(os.path.join(tema.RAIZ, caminho), w, h)
    if not uri:
        if caminho not in _avisados:
            _avisados.add(caminho)
            print(f'  aviso: {caminho} não existe, usando placeholder')
        return listras(F, x, y, w, h, rotulo, pid)
    return (f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="{uri}" '
            f'preserveAspectRatio="xMidYMid slice"/>')


def losango(cx, cy, r, cor, cheio):
    pts = f'{cx},{cy - r} {cx + r},{cy} {cx},{cy + r} {cx - r},{cy}'
    pinta = f'fill="{cor}"' if cheio else f'fill="none" stroke="{cor}" stroke-width="1.5"'
    return f'<polygon points="{pts}" {pinta}/>'


def icone(nome, cor):
    """Logo 24x24: path do simple-icons (preenchido) ou ícone de traço nosso."""
    s = open(os.path.join(ICONES, ICONE[nome] + '.svg'), encoding='utf-8').read()
    if 'stroke=' in s.split('>', 1)[0]:
        miolo = re.sub(r'<title>.*?</title>', '', s[s.index('>') + 1:s.rindex('</svg>')])
        return (f'<g fill="none" stroke="{cor}" stroke-width="1.5" stroke-linecap="round" '
                f'stroke-linejoin="round">{miolo.strip()}</g>')
    return ''.join(f'<path d="{d}" fill="{cor}"/>' for d in re.findall(r'<path d="([^"]+)"', s))


# ───────── identity ─────────

def rico_linhas(F, x, y, s, tam, max_w, passo=20):
    """Texto com **amarelo** e __magenta__ em negrito, quebrado em linhas de até max_w.
    O destaque sobrevive à quebra mesmo quando atravessa várias palavras."""
    chars = []
    for p in re.split(r'(\*\*.+?\*\*|__.+?__)', s):
        cor = AMARELO if p.startswith('**') else MAGENTA if p.startswith('__') else None
        chars += [(ch, cor) for ch in (p[2:-2] if cor else p)]
    palavras, atual = [], []
    for ch, cor in chars + [(' ', None)]:
        if ch == ' ':
            if atual:
                palavras.append(atual)
            atual = []
        else:
            atual.append((ch, cor))
    linhas, linha = [], []
    for p in palavras:
        teste = linha + ([(' ', None)] if linha else []) + p
        if linha and largura(''.join(ch for ch, _ in teste), tam) > max_w:
            linhas.append(linha)
            linha = p
        else:
            linha = teste
    linhas.append(linha)
    out = []
    for i, linha in enumerate(linhas):
        spans = []
        for cor, grupo in itertools.groupby(linha, key=lambda t: t[1]):
            txt = ''.join(ch for ch, _ in grupo)
            spans.append(f'<tspan fill="{cor}" font-weight="700">{esc(F.usar(txt, 700))}</tspan>'
                         if cor else esc(F.usar(txt)))
        out.append(f'<text x="{x}" y="{y + i * passo}" font-size="{tam}" fill="{TEXTO}">{"".join(spans)}</text>')
    return out, y + (len(linhas) - 1) * passo


def secao(F, x, y, nome, fim, direita=''):
    """'┌─ // NOME ───────── direita' ocupando até x=fim."""
    base, cauda = f'┌─ // {nome} ', f' {direita}' if direita else ''
    n = int((fim - x - largura(base + cauda, 13, 700)) // largura('─', 13, 700))
    return F.texto(x, y, base + '─' * n + cauda, 13, 700, MAGENTA)


def linhas_rotuladas(F, x, y, pares, passo=22):
    col = max(largura(k + ':', 13, 700) for k, _ in pares) + 14
    out = []
    for k, v in pares:
        out.append(F.texto(x, y, k + ':', 13, 700, AMARELO) + F.texto(x + col, y, val(v), 13))
        y += passo
    return out, y - passo


def identity(P):
    """RUN_01: imagem 270x270 à esquerda + terminal (prompt, bio, chrome, comms) à direita."""
    F, T, c = tema.Fontes(), P['terminal'], []
    lado = 270
    c.append(imagem(F, T['imagem'], PAD, PAD, lado, lado, '[imagem]', 'ph-identity'))
    c.append(f'<rect x="{PAD + .5}" y="{PAD + .5}" width="{lado - 1}" height="{lado - 1}" fill="none" stroke="{BORDA_SEC}"/>')

    x0, fim = PAD + lado + 28, W - PAD
    prompt = 'daniykt@nightcity:~$'
    y = 46
    c.append(F.texto(x0, y, prompt, 14, 700, AMARELO, extra=' filter="url(#glow)"'))
    c.append(F.texto(x0 + largura(prompt, 14, 700) + 12, y, '// uplink stable', 12, cor=APAGADO))
    c.append(f'<line x1="{x0}" y1="{y + 16.5}" x2="{fim}" y2="{y + 16.5}" stroke="{VAZIO}"/>')

    linhas, y = rico_linhas(F, x0, y + 44, P['bio'], 13, fim - x0)
    c += linhas

    stack = [par for par in T['stack'] if par[0] in IDENTITY_STACK]
    c.append(secao(F, x0, y + 36, 'CHROME', fim))
    linhas, y = linhas_rotuladas(F, x0, y + 60, stack)
    c += linhas

    c.append(secao(F, x0, y + 36, 'COMMS', fim))
    linhas, y = linhas_rotuladas(F, x0, y + 60, T['comms'])
    c += linhas

    h = max(PAD + lado + PAD, y + 20)
    defs = ('<defs><pattern id="scanlines" patternUnits="userSpaceOnUse" width="2" height="3">'
            '<rect width="2" height="1" fill="#ffffff" opacity="0.025"/></pattern>'
            '<filter id="glow" x="-20%" y="-20%" width="140%" height="140%">'
            '<feGaussianBlur stdDeviation="0.6" result="blur"/>'
            '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>')
    corpo = defs + ''.join(c) + f'<rect width="{W}" height="{h}" fill="url(#scanlines)"/>'
    bio = re.sub(r'\*\*|__', '', P['bio'])
    stack_txt = '; '.join(f'{k}: {v}' for k, v in stack)
    comms_txt = ', '.join(v for _, v in T['comms'])
    return tema.card_secao('RUN_01', 'IDENTITY', 1, corpo, h, F,
                           f'RUN_01 Identity. daniykt@nightcity: {bio} Chrome — {stack_txt}. Comms: {comms_txt}.')


# ───────── charsheet ─────────

def charsheet(P):
    """RUN_02: retrato à esquerda, ficha + atributos + citação à direita."""
    F, c = tema.Fontes(), []
    px, py, ps = PAD, PAD, 250
    pers = P['personagem']
    c.append(imagem(F, pers['imagem'], px, py, ps, ps, '[retrato]', 'ph-retrato'))
    c.append(f'<rect x="{px + .5}" y="{py + .5}" width="{ps - 1}" height="{ps - 1}" fill="none" stroke="{MAGENTA}" stroke-width="1.5"/>')
    c.append(F.texto(px, py + ps + 22, val(pers['codigo']), 12, 700, MAGENTA, espaco=1))
    c.append(F.texto(px + ps, py + ps + 22, 'ID VERIFIED ✓', 11, cor=TEXTO3, anchor='end', espaco=1))

    x, fim = px + ps + 30, W - PAD
    c.append(F.texto(x, 58, val(P['nome']), 34, 800, AMARELO))
    c.append(F.texto(x, 82, val(P['classe']), 12, 700, MAGENTA, espaco=3))

    y = 116
    for rot, chave in (('ORIGIN', 'origin'), ('CREW', 'crew'), ('CYBERWARE', 'cyberware'), ('STATUS', 'status')):
        c.append(F.texto(x, y, rot, 11, 700, TEXTO3, espaco=1))
        c.append(F.texto(x + 100, y, val(P[chave]), 13, cor=MAGENTA if rot == 'STATUS' else TEXTO))
        y += 22

    y += 6
    c.append(F.texto(x, y, 'ATTRIBUTES', 11, 700, TEXTO3, espaco=2))
    attrs = {k: v for k, v in P['atributos'].items() if not k.startswith('_')}
    for nome, n in attrs.items():
        y += 19
        cor = MAGENTA if nome == 'COOL' else AMARELO
        c.append(F.texto(x, y, nome, 11, 700, TEXTO, espaco=1))
        for i in range(10):
            c.append(f'<rect x="{x + 60 + i * 20}" y="{y - 9}" width="16" height="10" fill="{cor if i < n else VAZIO}"/>')
        c.append(F.texto(x + 270, y, f'{n}/10', 11, cor=TEXTO3))

    y += 16
    c.append(f'<line x1="{x}" y1="{y}" x2="{fim}" y2="{y}" stroke="{VAZIO}"/>')
    for linha in tema.quebrar(f'“{val(P["citacao"])}”', 12, fim - x):
        y += 20
        c.append(F.texto(x, y, linha, 12, cor=CLARO, extra=' font-style="italic"'))
    h = max(py + ps + 22 + 20, y + 24)

    attr_txt = ', '.join(f'{k} {v}/10' for k, v in attrs.items())
    return tema.card_secao('RUN_02', 'CHARACTER SHEET', 2, ''.join(c), h, F,
                           f'RUN_02 Character sheet. {val(P["nome"])}, {val(P["classe"])}, {val(pers["codigo"])}, ID verified. '
                           f'Origin {val(P["origin"])}; crew {val(P["crew"])}; cyberware {val(P["cyberware"])}; '
                           f'status: {val(P["status"])} Attributes: {attr_txt}. “{val(P["citacao"])}”')


# ───────── journal ─────────

def journal(P):
    """RUN_03: abas à esquerda (190px), itens do journal à direita."""
    F, c, J = tema.Fontes(), [], P['journal']
    abas = (('MAIN JOB', 'MAIN JOB'), ('SIDE JOBS', 'SIDE JOB'), ('GIGS', 'GIG'))
    y = PAD
    for i, (rotulo, tipo) in enumerate(abas):
        n = sum(1 for j in J if j['tipo'] == tipo)
        if i == 0:
            c.append(f'<rect x="{PAD}" y="{y}" width="170" height="36" fill="{AMARELO}"/>')
            c.append(F.texto(PAD + 14, y + 23, f'{rotulo} · {n}', 12, 800, FUNDO, espaco=1, fundo=AMARELO))
        else:
            c.append(f'<rect x="{PAD + .5}" y="{y + .5}" width="169" height="35" fill="none" stroke="{BORDA_SEC}"/>')
            c.append(F.texto(PAD + 14, y + 23, f'{rotulo} · {n}', 12, 700, TEXTO3, espaco=1))
        y += 46
    fim_abas = y - 10

    x, y = PAD + 190 + 26, 44
    for j in J:
        cor, cheio = {'MAIN JOB': (AMARELO, True), 'SIDE JOB': (MAGENTA, False)}.get(j['tipo'], (CINZA, False))
        c.append(losango(x + 6, y - 5, 6, cor, cheio))
        titulo = val(j['titulo'])
        c.append(F.texto(x + 22, y, titulo, 14, 700, TEXTO))
        if j.get('tracked'):
            tx = x + 22 + largura(titulo, 14, 700) + 12
            tw = largura('TRACKED', 10, 700, 1.5) + 12
            c.append(f'<rect x="{tx + .5:g}" y="{y - 12.5}" width="{tw - 1:g}" height="16" fill="none" stroke="{AMARELO}"/>')
            c.append(F.texto(tx + 6, y - 1, 'TRACKED', 10, 700, AMARELO, espaco=1.5))
        c.append(f'<rect x="{x + 22.5}" y="{y + 11.5}" width="9" height="9" fill="none" stroke="{CLARO}"/>')
        c.append(F.texto(x + 38, y + 20, val(j['objetivo']), 12, cor=CLARO))
        y += 62
    h = max(fim_abas + PAD, y - 62 + 20 + 28)

    c.append(f'<line x1="{PAD + 190.5}" y1="{PAD}" x2="{PAD + 190.5}" y2="{h - PAD}" stroke="{VAZIO}"/>')
    itens = ' '.join(f'{j["tipo"]}{" (tracked)" if j.get("tracked") else ""}: {val(j["titulo"])} — {val(j["objetivo"])}'
                     for j in J)
    return tema.card_secao('RUN_03', 'JOURNAL', 3, ''.join(c), h, F,
                           f'RUN_03 Journal, foco no momento. {itens}', subtitulo='foco no momento')


# ───────── gigs ─────────

def gigs_titulo():
    """RUN_04: só a barra de título. Os gigs ficam em cards separados porque link
    dentro de SVG não funciona no README (cada card vai num <a> próprio)."""
    F = tema.Fontes()
    return tema.card_secao('RUN_04', 'GIGS EM DESTAQUE', 4, '', 0, F, 'RUN_04 Gigs em destaque.')


def gig_texto(F, g, n, x, y, w):
    """Cabeçalho, nome, descrição e chips. Devolve (elementos, y do fim dos chips)."""
    c = [F.texto(x, y, f'GIG {n:02d} · {val(g["equipe"])} · {val(g["tag"])}', 11, 700, MAGENTA, espaco=2)]
    y += 38
    c.append(F.texto(x, y, val(g['nome']).upper(), 30, 800, AMARELO))
    y += 6
    for linha in tema.quebrar(val(g['descricao']), 13, w):
        y += 19
        c.append(F.texto(x, y, linha, 13))
    if 'minha_parte' in g:
        for linha in tema.quebrar('Minha parte: ' + val(g['minha_parte']), 12, w):
            y += 20
            c.append(F.texto(x, y, linha, 12, cor=TEXTO2))
    y += 14
    cx = x
    for s in g['stack']:
        cw = largura(s, 11, 700) + 20
        if cx > x and cx + cw > x + w:
            cx, y = x, y + 30
        c.append(f'<rect x="{cx + .5:g}" y="{y + .5}" width="{cw - 1:g}" height="21" fill="none" stroke="{CHIP}"/>')
        c.append(F.texto(cx + 10, y + 15, s, 11, 700, AMARELO))
        cx += cw + 8
    return c, y + 22


def gig_card(P, i, h_min):
    """i=0: card de 840 com coluna de 170px à direita (número + link);
    senão 412 de largura com o número no canto superior direito e o link embaixo."""
    F, g = tema.Fontes(), P['gigs'][i]
    n = f'{i + 1:02d}'
    if i == 0:
        w, col = W, 170
        c, fim = gig_texto(F, g, i + 1, PAD, 40, W - col - 2 * PAD)
        H = max(h_min, fim + PAD + 4)
        cx = W - col / 2
        c.append(f'<line x1="{W - col + .5}" y1="{PAD}" x2="{W - col + .5}" y2="{H - PAD}" stroke="{VAZIO}"/>')
        c.append(F.texto(cx, 98, n, 64, 800, NUMERO, anchor='middle', fundo=None))
        c.append(F.texto(cx, H - 30, 'ABRIR REPO ↗', 12, 700, AMARELO, anchor='middle', espaco=2))
    else:
        w = W_GIG
        c, fim = gig_texto(F, g, i + 1, PAD, 40, W_GIG - 2 * PAD)
        H = max(h_min, fim + 62)
        c.append(F.texto(W_GIG - PAD, 46, n, 26, 800, NUMERO, anchor='end', fundo=None))
        c.append(F.texto(PAD, H - 24, 'ABRIR REPO ↗', 12, 700, AMARELO, espaco=2))

    corpo = fundo(w, H) + ''.join(c) + tema.moldura_hud(0, 0, w, H, BORDA_SEC)
    extra = f' Minha parte: {val(g["minha_parte"])}.' if 'minha_parte' in g else ''
    titulo = (f'Gig {n} · {val(g["equipe"])} · {val(g["tag"])}: {val(g["nome"])}. '
              f'{val(g["descricao"])}{extra} Stack: {", ".join(g["stack"])}. Abrir repo.')
    return tema.svg(w, H, corpo, F, titulo), H


# ───────── chrome ─────────

def chrome(P):
    """RUN_05: prosa da stack, divisória e o inventário de cyberware com os logos."""
    F, c = tema.Fontes(), []
    linhas, y = rico_linhas(F, PAD, 38, P['chrome_texto'], 13, W - 2 * PAD, passo=21)
    c += linhas
    y += 22
    c.append(f'<line x1="{PAD}" y1="{y + .5}" x2="{W - PAD}" y2="{y + .5}" stroke="{VAZIO}"/>')

    y += 36
    c.append(F.texto(PAD, y, 'RIPPERDOC // CYBERWARE INVENTORY', 14, 800, AMARELO, espaco=1))
    lx = W - PAD
    c.append(F.texto(lx, y, 'na fila', 11, cor=TEXTO3, anchor='end'))
    lx -= largura('na fila', 11) + 16
    c.append(f'<rect x="{lx + .5:g}" y="{y - 8.5}" width="9" height="9" fill="none" stroke="{MAGENTA}" stroke-dasharray="2 2"/>')
    lx -= 14
    c.append(F.texto(lx, y, 'instalado', 11, cor=TEXTO3, anchor='end'))
    lx -= largura('instalado', 11) + 16
    c.append(f'<rect x="{lx:g}" y="{y - 9}" width="10" height="10" fill="{AMARELO}"/>')

    y += 24
    for grupo in P['chrome']:
        fila = grupo.get('fila')
        if fila:
            y += 6
            c.append(f'<line x1="{PAD}" y1="{y + .5}" x2="{W - PAD}" y2="{y + .5}" stroke="{VAZIO}"/>')
            y += 20
        for k, parte in enumerate(grupo['grupo'].split(' ', 1)):
            c.append(F.texto(PAD, y + 40 + k * 15, parte, 11, 700, MAGENTA, espaco=1))
        borda = (f'stroke="{MAGENTA}" stroke-dasharray="4 3"' if fila else f'stroke="{CHIP}"')
        topo, logo, nome_cor = (MAGENTA, CINZA, TEXTO3) if fila else (AMARELO, AMARELO, TEXTO)
        for n, item in enumerate(grupo['itens']):
            sx = PAD + 116 + n * 96
            c.append(f'<rect x="{sx + .5}" y="{y + .5}" width="85" height="85" fill="{SLOT}" {borda}/>')
            c.append(f'<rect x="{sx}" y="{y}" width="86" height="3" fill="{topo}"/>')
            if item in ICONE:
                c.append(f'<g transform="translate({sx + 27} {y + 16}) scale({32 / 24:.4f})">{icone(item, logo)}</g>')
            tam = 10
            while largura(item, tam) > 78:
                tam -= .5
            c.append(F.texto(sx + 43, y + 72, item, tam, cor=nome_cor, anchor='middle', fundo=SLOT))
        y += 100
    h = y - 14 + PAD

    prosa = re.sub(r'\*\*|__', '', P['chrome_texto'])
    grupos = ' '.join(f'{g["grupo"]}: {", ".join(g["itens"])}.' for g in P['chrome'])
    return tema.card_secao('RUN_05', 'CHROME INSTALADO', 5, ''.join(c), h, F,
                           f'RUN_05 Chrome instalado. {prosa} Ripperdoc // cyberware inventory — {grupos}')


# ───────── formação ─────────

def formacao(P):
    """RUN_06: duas colunas (instalado / instalando) + slot vazio pra certificados."""
    F, c = tema.Fontes(), []
    cursos = [f for f in P['formacao'] if f['status'] != 'slot']
    slots = [f for f in P['formacao'] if f['status'] == 'slot']
    cw = 375
    gap = W - 2 * PAD - 2 * cw
    fundo_col = 0
    for k, f in enumerate(cursos[:2]):
        x = PAD + k * (cw + gap)
        feito = f['status'] == 'instalado'
        cor = VERDE if feito else AMARELO
        c.append(f'<rect x="{x}" y="27" width="10" height="10" fill="{cor}"/>')
        c.append(F.texto(x + 18, 36, 'INSTALADO' if feito else 'INSTALANDO', 12, 700, cor, espaco=2))
        c.append(F.texto(x + cw, 36, f'{f["inicio"]} → {f["fim"]}', 12, cor=TEXTO3, anchor='end'))
        if feito:
            c.append(f'<rect x="{x}" y="52" width="{cw}" height="3" fill="{VERDE}"/>')
        else:
            atual, total = f['semestre'], f['semestres']
            bw = (cw - (total - 1) * 6) / total
            for s in range(total):
                cor_s = AMARELO if s < atual - 1 else MAGENTA if s == atual - 1 else VAZIO
                c.append(f'<rect x="{x + s * (bw + 6):g}" y="48" width="{bw:g}" height="10" fill="{cor_s}"/>')
        y = 66
        for linha in tema.quebrar(val(f['curso']), 14, cw, 700):
            y += 20
            c.append(F.texto(x, y, linha, 14, 700, TEXTO))
        escola = val(f['escola']) + ('' if feito else f' · semestre {f["semestre"]} de {f["semestres"]}')
        y += 20
        c.append(F.texto(x, y, escola, 12, cor=TEXTO2))
        fundo_col = max(fundo_col, y)
    c.append(f'<line x1="{W / 2 + .5:g}" y1="{PAD}" x2="{W / 2 + .5:g}" y2="{fundo_col + 6}" stroke="{VAZIO}"/>')

    y = fundo_col + 26
    for f in slots:
        c.append(f'<rect x="{PAD + .5}" y="{y + .5}" width="{W - 2 * PAD - 1}" height="49" fill="none" stroke="{CINZA}" '
                 f'stroke-opacity=".6" stroke-dasharray="6 4"/>')
        c.append(F.texto(PAD + 20, y + 30, 'EMPTY SLOT', 12, 700, TEXTO3, espaco=2))
        c.append(F.texto(PAD + 20 + largura('EMPTY SLOT', 12, 700, 2) + 16, y + 30, val(f['texto']), 12, cor=TEXTO3))
        y += 62
    h = y - 12 + PAD

    desc = ' '.join(f'{"Instalado" if f["status"] == "instalado" else "Instalando"} ({f["inicio"]} → {f["fim"]}): '
                    f'{val(f["curso"])}, {val(f["escola"])}'
                    f'{"" if f["status"] == "instalado" else " · semestre %d de %d" % (f["semestre"], f["semestres"])}.'
                    for f in cursos)
    return tema.card_secao('RUN_06', 'RIPPERDOC LOG', 6, ''.join(c), h, F,
                           f'RUN_06 Ripperdoc log, formação. {desc} Empty slot {" ".join(val(s["texto"]) for s in slots)}.',
                           subtitulo='formação')


def main():
    with open(PERFIL, encoding='utf-8') as f:
        P = json.load(f)
    tema.salvar('identity.svg', identity(P))
    tema.salvar('charsheet.svg', charsheet(P))
    tema.salvar('journal.svg', journal(P))

    gigs = P['gigs']
    tema.salvar('gigs-titulo.svg', gigs_titulo())
    s, _ = gig_card(P, 0, 180)
    tema.salvar(f'gig-{gigs[0]["id"]}.svg', s)
    h = max(gig_card(P, i, 0)[1] for i in range(1, len(gigs)))   # mesma altura lado a lado
    for i in range(1, len(gigs)):
        tema.salvar(f'gig-{gigs[i]["id"]}.svg', gig_card(P, i, h)[0])

    tema.salvar('chrome.svg', chrome(P))
    tema.salvar('formacao.svg', formacao(P))


if __name__ == '__main__':
    main()

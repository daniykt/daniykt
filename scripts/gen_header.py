#!/usr/bin/env python3
"""Gera assets/header.svg animado — tema Cyberpunk: Edgerunners.

Produz um header 900x300 com:
  - nome 'daniykt' em letras grandes com gradient animado (holo-shine)
  - chromatic aberration glitch (3 cópias RGB, ativa em 85-91% do ciclo)
  - linha de comando digitada caractere por caractere (SMIL clipPath)
  - subtítulo + frase do Johnny Silverhand piscando
  - scanlines CRT + sweep bar descendo
  - status bar com NAVI ● JACKED_IN piscando

A JetBrains Mono vai embutida (subset em base64, via tema.Fontes), porque o
GitHub mostra o SVG como <img> e aí ele não carrega fonte de fora.
SMIL funciona dentro do <img> do GitHub README.

uso:  python3 scripts/gen_header.py
"""
import html
import os
import re

import tema

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets', 'header.svg')

# ───────── CONFIG — mude aqui pra customizar ─────────
W, H = 900, 300
NAME = 'daniykt'
CMD = '$ ./jack_in --user=daniykt --city=nightmato --mode=edgerunner'
SUB = 'front-end · web designer · 22 anos · matão/sp · fatec dsm'
QUOTE = '> "wake the f*ck up samurai, we have a city to burn"'

# paleta Edgerunners (CDPR)
YELLOW, MAGENTA, CYAN = '#FCEE09', '#FF003C', '#00F0FF'
BG, TEXT, DIM = '#0a0a0f', '#e8e8e8', '#b8b8c8'   # terciário (contraste >= 4.5:1)
FONT = "'JetBrains Mono','Fira Code','DejaVu Sans Mono',Menlo,Consolas,monospace"
# ─────────────────────────────────────────────────────


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def typing(text, x, y, cw, dur, idd='tp'):
    """Texto 'digitado' char por char via clipPath animado (SMIL)."""
    n = len(text)
    vals = ';'.join(f'{i*cw:.1f}' for i in range(n+1)) + f';{n*cw:.1f};0'
    kts = ';'.join(f'{0.55*i/n:.4f}' for i in range(n+1)) + ';0.97;1.0'
    return (f'<clipPath id="{idd}"><rect x="{x}" y="{y-20}" width="0" height="28">'
            f'<animate attributeName="width" values="{vals}" keyTimes="{kts}" '
            f'dur="{dur}s" calcMode="discrete" repeatCount="indefinite"/></rect></clipPath>'
            f'<text x="{x}" y="{y}" class="cmd" clip-path="url(#{idd})" '
            f'xml:space="preserve">{esc(text)}</text>')


name = f'<text x="{W/2}" y="190" class="name" text-anchor="middle">{NAME}</text>'

css = f"""
text {{ font-family: {FONT}; }}
.bg   {{ fill: {BG}; }}
.dim  {{ fill: {DIM}; font-size: 12px; letter-spacing: 1px; }}
.yel  {{ fill: {YELLOW}; }}
.cmd  {{ fill: {TEXT}; font-size: 15px; }}
.sub  {{ fill: #c9c9d6; font-size: 14px; letter-spacing: .5px; }}
.name {{ font-size: 108px; font-weight: 900; letter-spacing: -4px; }}
.main {{ fill: url(#ng); }}
.gr   {{ fill: {MAGENTA}; opacity: 0; mix-blend-mode: screen; animation: g1 5s infinite steps(1); }}
.gc   {{ fill: {CYAN};    opacity: 0; mix-blend-mode: screen; animation: g2 5s infinite steps(1); }}
.jit  {{ animation: jit 5s infinite steps(1); }}
.blink{{ animation: blink 1s infinite steps(1); }}
.flick{{ animation: flick 7s infinite; }}
.sweep{{ animation: sweep 6s linear infinite; }}
@keyframes g1 {{ 0%,84%,100%{{opacity:0;transform:none}} 85%{{opacity:.85;transform:translate(-5px,1px)}} 87%{{opacity:.85;transform:translate(4px,-2px)}} 89%{{opacity:.7;transform:translate(-2px,0)}} 91%{{opacity:0}} }}
@keyframes g2 {{ 0%,84%,100%{{opacity:0;transform:none}} 85%{{opacity:.85;transform:translate(5px,-1px)}} 87%{{opacity:.85;transform:translate(-3px,2px)}} 89%{{opacity:.7;transform:translate(3px,0)}} 91%{{opacity:0}} }}
@keyframes jit {{ 0%,84%,92%,100%{{transform:none}} 86%{{transform:translate(2px,0) skewX(-6deg)}} 88%{{transform:translate(-3px,0)}} 90%{{transform:translate(1px,0) skewX(4deg)}} }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
@keyframes flick {{ 0%,100%{{opacity:1}} 43%{{opacity:.2}} 44%{{opacity:1}} 46%{{opacity:.4}} 47%{{opacity:1}} }}
@keyframes sweep {{ from{{transform:translateY(0)}} to{{transform:translateY({H+60}px)}} }}
"""

body = f"""<defs>
<linearGradient id="ng" x1="0" y1="0" x2="1" y2="0">
<stop offset="0" stop-color="{YELLOW}"/>
<stop offset=".45" stop-color="#fff6a6"/>
<stop offset=".5" stop-color="{MAGENTA}"/>
<stop offset=".55" stop-color="#fff6a6"/>
<stop offset="1" stop-color="{YELLOW}"/>
<animateTransform attributeName="gradientTransform" type="translate"
  values="-1 0;1 0" dur="6s" repeatCount="indefinite"/>
</linearGradient>
<linearGradient id="sweepg" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#fff" stop-opacity="0"/>
<stop offset=".85" stop-color="#fff" stop-opacity=".05"/>
<stop offset="1" stop-color="#fff" stop-opacity=".12"/>
</linearGradient>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
<rect width="4" height="2" fill="#000" opacity=".28"/>
</pattern>
</defs>
<rect class="bg" width="{W}" height="{H}" rx="14"/>
<text x="22" y="30" class="dim">// EDGERUNNER_01 // NIGHTMATO</text>
<text x="{W-22}" y="30" class="dim" text-anchor="end">NAVI ▸ <tspan class="yel blink">●</tspan> JACKED_IN</text>
{typing(CMD, 36, 70, 9.0, 9)}
<g class="jit">
  <g class="gr">{name}</g>
  <g class="gc">{name}</g>
  <g class="main">{name}</g>
</g>
<text x="{W/2}" y="230" class="sub" text-anchor="middle">{esc(SUB)}</text>
<text x="{W/2}" y="258" class="dim flick" text-anchor="middle" style="font-size:13px">{esc(QUOTE)} <tspan class="yel blink">█</tspan></text>
<rect width="{W}" height="{H}" fill="url(#scan)" pointer-events="none"/>
<rect class="sweep" x="0" y="-60" width="{W}" height="60" fill="url(#sweepg)"/>
"""

F = tema.Fontes()
F.usar(html.unescape(re.sub(r'<[^>]+>', '', body)))   # todo texto do corpo, peso normal
F.usar(NAME, 900)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="daniykt — edgerunner in nightmato">
<title>daniykt — edgerunner header</title>
<style>{F.css()}{css}</style>
{body}
</svg>
'''

if __name__ == '__main__':
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f'ok header.svg {len(svg.encode())//1024} KB')

#!/usr/bin/env python3
"""Gera assets/footer.svg animado — tema Cyberpunk: Edgerunners.

Produz um footer 900x150 com:
  - 'NEVER FADE AWAY' em JetBrains Mono 800
  - chromatic aberration glitch (cópias RGB, ativa em 80-90% do ciclo)
  - fatias horizontais do título deslizando durante o glitch
  - subtítulo 'the ones who do go legend · see you on the net, choom'
  - scanlines CRT

Sem dependências — só stdlib. CSS keyframes funcionam dentro do <img> do GitHub README.

uso:  python3 scripts/gen_footer.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'assets', 'footer.svg')

# ───────── CONFIG — mude aqui pra customizar ─────────
W, H = 900, 150
TITLE = 'NEVER FADE AWAY'
SUB_A = 'the ones who do go legend'
SUB_B = 'see you on the net, choom'

# paleta Edgerunners (CDPR)
YELLOW, MAGENTA, CYAN = '#FCEE09', '#FF003C', '#00F0FF'
BG, DIM = '#0a0a0f', '#5c5c6e'
FONT = "'JetBrains Mono','Fira Code','DejaVu Sans Mono',Menlo,Consolas,monospace"
# ─────────────────────────────────────────────────────


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


title = f'<text x="{W/2}" y="88" class="title" text-anchor="middle">{esc(TITLE)}</text>'

css = f"""
text {{ font-family: {FONT}; }}
.bg    {{ fill: {BG}; }}
.dim   {{ fill: {DIM}; font-size: 11px; letter-spacing: 1px; }}
.mag   {{ fill: {MAGENTA}; }}
.sub   {{ fill: #9a9ab0; font-size: 14px; letter-spacing: .5px; }}
.title {{ font-size: 64px; font-weight: 800; letter-spacing: 4px; }}
.main  {{ fill: {YELLOW}; }}
.gr    {{ fill: {MAGENTA}; opacity: 0; mix-blend-mode: screen; animation: g1 4s infinite steps(1); }}
.gc    {{ fill: {CYAN};    opacity: 0; mix-blend-mode: screen; animation: g2 4s infinite steps(1); }}
.s1    {{ fill: {YELLOW};  opacity: 0; animation: s1 4s infinite steps(1); }}
.s2    {{ fill: {YELLOW};  opacity: 0; animation: s2 4s infinite steps(1); }}
.jit   {{ animation: jit 4s infinite steps(1); }}
.blink {{ animation: blink 1s infinite steps(1); }}
@keyframes g1  {{ 0%,79%,100%{{opacity:0;transform:none}} 80%{{opacity:.9;transform:translate(-6px,1px)}} 83%{{opacity:.9;transform:translate(4px,-1px)}} 86%{{opacity:.7;transform:translate(-3px,0)}} 90%{{opacity:0}} }}
@keyframes g2  {{ 0%,79%,100%{{opacity:0;transform:none}} 80%{{opacity:.9;transform:translate(6px,-1px)}} 83%{{opacity:.9;transform:translate(-4px,1px)}} 86%{{opacity:.7;transform:translate(3px,0)}} 90%{{opacity:0}} }}
@keyframes s1  {{ 0%,81%,88%,100%{{opacity:0;transform:none}} 82%{{opacity:1;transform:translate(14px,0)}} 85%{{opacity:1;transform:translate(-8px,0)}} }}
@keyframes s2  {{ 0%,83%,90%,100%{{opacity:0;transform:none}} 84%{{opacity:1;transform:translate(-12px,0)}} 87%{{opacity:1;transform:translate(6px,0)}} }}
@keyframes jit {{ 0%,79%,91%,100%{{transform:none}} 81%{{transform:translate(2px,0) skewX(-6deg)}} 85%{{transform:translate(-3px,0)}} 89%{{transform:translate(1px,0) skewX(4deg)}} }}
@keyframes blink {{ 50% {{ opacity: 0; }} }}
"""

body = f"""<defs>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
<rect width="4" height="2" fill="#000" opacity=".28"/>
</pattern>
<clipPath id="slice1"><rect x="0" y="46" width="{W}" height="14"/></clipPath>
<clipPath id="slice2"><rect x="0" y="70" width="{W}" height="10"/></clipPath>
</defs>
<rect class="bg" width="{W}" height="{H}" rx="14"/>
<text x="22" y="26" class="dim">// END_OF_TRANSMISSION</text>
<text x="{W-22}" y="26" class="dim" text-anchor="end">SIGNAL ▸ <tspan class="mag blink">●</tspan> LIVE</text>
<g class="jit">
  <g class="gr">{title}</g>
  <g class="gc">{title}</g>
  <g class="main">{title}</g>
  <g clip-path="url(#slice1)"><g class="s1">{title}</g></g>
  <g clip-path="url(#slice2)"><g class="s2">{title}</g></g>
</g>
<text x="{W/2}" y="124" class="sub" text-anchor="middle">{esc(SUB_A)} <tspan class="mag">·</tspan> {esc(SUB_B)}</text>
<rect width="{W}" height="{H}" fill="url(#scan)" pointer-events="none"/>
"""

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="never fade away — see you on the net, choom">
<title>daniykt — edgerunner footer</title>
<style>{css}</style>
{body}
</svg>
'''

if __name__ == '__main__':
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(svg)
    print(f'ok footer.svg {len(svg.encode())//1024} KB')

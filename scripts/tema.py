"""Tema compartilhado dos SVGs — Cyberpunk: Edgerunners.

O GitHub mostra SVG como <img>, e nesse modo o SVG não carrega nada de fora.
Por isso tudo aqui vai embutido no próprio arquivo:
  - Fontes: junta os caracteres usados por peso e gera @font-face em base64
    (WOFF com subset só desses caracteres, via fontTools)
  - largura() / quebrar(): métricas reais da JetBrains Mono pra posicionar e quebrar texto
  - moldura_hud(): a moldura assinatura (borda fina + 4 cantos em L amarelos)
  - img_base64(): imagem redimensionada em JPEG q80 como data URI
  - svg(): monta o documento com role="img", <title> e aria-label

uso (dentro de outro script em scripts/):
  import tema
  F = tema.Fontes()
  corpo = F.texto(20, 40, 'olá', tam=14, peso=700, cor=tema.AMARELO)
  tema.salvar('exemplo.svg', tema.svg(300, 80, corpo, F, 'exemplo'))
"""
import base64
import io
import os
from functools import lru_cache

from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(HERE, '..')
ASSETS = os.path.join(RAIZ, 'assets')
FONTES = os.path.join(HERE, 'fontes')

# ───────── paleta Edgerunners ─────────
AMARELO, MAGENTA, CIANO = '#FCEE09', '#FF003C', '#00F0FF'   # ciano só pro glitch
FUNDO, TEXTO, CINZA = '#0a0a0f', '#e8e8e8', '#8b8b9e'
VERDE = '#3fb950'                                            # só pra "concluído"
BORDA_SEC = '#3a1622'      # borda dos cards secundários
VAZIO = '#2a2a35'          # blocos vazios, divisórias
CHIP = '#4a4410'           # borda de chip / slot instalado

FAMILIA = "'JetBrains Mono',monospace"
PESOS = {400: 'JetBrainsMono-Regular.ttf', 700: 'JetBrainsMono-Bold.ttf', 800: 'JetBrainsMono-ExtraBold.ttf'}
CANTO, CANTO_E = 16, 2     # cantos em L: 16px de braço, 2px de espessura


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def peso_real(peso):
    """Peso embutido que o navegador vai escolher pra um font-weight pedido (regra do CSS)."""
    return 400 if peso <= 500 else 700 if peso <= 700 else 800


@lru_cache(maxsize=None)
def _fonte(peso):
    return TTFont(os.path.join(FONTES, PESOS[peso_real(peso)]))


@lru_cache(maxsize=None)
def _metricas(peso):
    f = _fonte(peso)
    cmap, hmtx = f.getBestCmap(), f['hmtx']
    return cmap, hmtx, f['head'].unitsPerEm


def largura(texto, tamanho, peso=400, espaco=0):
    """Largura do texto em px, com letter-spacing opcional."""
    cmap, hmtx, upm = _metricas(peso)
    total = sum(hmtx[cmap[ord(c)]][0] if ord(c) in cmap else 600 for c in texto)
    return total * tamanho / upm + espaco * len(texto)


def quebrar(texto, tamanho, largura_max, peso=400):
    """Quebra o texto em linhas que cabem em largura_max (por palavra)."""
    linhas, atual = [], ''
    for palavra in texto.split():
        teste = f'{atual} {palavra}' if atual else palavra
        if atual and largura(teste, tamanho, peso) > largura_max:
            linhas.append(atual)
            atual = palavra
        else:
            atual = teste
    return linhas + [atual] if atual else linhas


class Fontes:
    """Coleta os caracteres usados por peso e embute só esse subset."""

    def __init__(self, familia='JetBrains Mono'):
        self.familia = familia
        self.usados = {p: set() for p in PESOS}

    def usar(self, texto, peso=400):
        self.usados[peso_real(peso)].update(str(texto))
        return texto

    def texto(self, x, y, s, tam=13, peso=400, cor=TEXTO, anchor=None, espaco=0, extra=''):
        """<text> já registrado nas fontes."""
        self.usar(s, peso)
        a = f' text-anchor="{anchor}"' if anchor else ''
        ls = f' letter-spacing="{espaco}"' if espaco else ''
        return (f'<text x="{x:g}" y="{y:g}" font-size="{tam}" font-weight="{peso}" '
                f'fill="{cor}"{a}{ls}{extra}>{esc(s)}</text>')

    def css(self):
        regras = []
        for peso, chars in self.usados.items():
            if not chars:
                continue
            cmap = _metricas(peso)[0]
            faltando = sorted(c for c in chars if ord(c) not in cmap and not c.isspace())
            if faltando:
                print(f'  aviso: JetBrains Mono {peso} sem glifo para {faltando!r}')
            regras.append(f"@font-face{{font-family:'{self.familia}';font-weight:{peso};"
                          f"src:url(data:font/woff;base64,{_woff(peso, ''.join(sorted(chars)))}) format('woff');}}")
        return '\n'.join(regras)


@lru_cache(maxsize=None)
def _woff(peso, chars):
    opts = subset.Options()
    opts.flavor = 'woff'
    opts.layout_features = []      # sem ligaduras: só os glifos pedidos
    opts.hinting = False
    opts.notdef_outline = False
    fonte = TTFont(os.path.join(FONTES, PESOS[peso]))
    s = subset.Subsetter(opts)
    s.populate(unicodes={ord(c) for c in chars} | {32})
    s.subset(fonte)
    fonte.flavor = 'woff'
    buf = io.BytesIO()
    fonte.save(buf)
    return base64.b64encode(buf.getvalue()).decode('ascii')


def moldura_hud(x, y, w, h, borda=MAGENTA):
    """Borda fina + 4 cantos em L amarelos (CANTO x CANTO_E px) — a assinatura visual."""
    c, e = CANTO, CANTO_E
    x2, y2 = x + w, y + h
    ret = [(x, y, c, e), (x, y, e, c), (x2 - c, y, c, e), (x2 - e, y, e, c),
           (x, y2 - e, c, e), (x, y2 - c, e, c), (x2 - c, y2 - e, c, e), (x2 - e, y2 - c, e, c)]
    d = ''.join(f'M{a:g} {b:g}h{rw:g}v{rh:g}h{-rw:g}z' for a, b, rw, rh in ret)
    return (f'<rect x="{x + .5:g}" y="{y + .5:g}" width="{w - 1:g}" height="{h - 1:g}" '
            f'fill="none" stroke="{borda}" stroke-width="1"/>'
            f'<path d="{d}" fill="{AMARELO}"/>')


def img_base64(caminho, largura, altura=None, escala=2):
    """Data URI JPEG q80. Com altura, corta pra preencher (object-fit: cover).
    escala=2 guarda o dobro de pixels pra ficar nítido em tela retina."""
    if not os.path.isfile(caminho):
        return None
    img = ImageOps.exif_transpose(Image.open(caminho)).convert('RGB')
    if altura:
        img = ImageOps.fit(img, (largura * escala, altura * escala), Image.Resampling.LANCZOS)
    else:
        img = img.resize((largura * escala, round(img.height * largura * escala / img.width)),
                         Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=80, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')


def svg(w, h, corpo, fontes, titulo, css=''):
    """Documento SVG acessível com as fontes embutidas."""
    t = esc(titulo)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{t}">\n'
            f'<title>{t}</title>\n'
            f'<style>\n{fontes.css()}\ntext {{ font-family: {FAMILIA}; }}\n{css}</style>\n'
            f'{corpo}\n</svg>\n')


def salvar(nome, conteudo):
    caminho = os.path.join(ASSETS, nome)
    with open(caminho, 'w', encoding='utf-8', newline='\n') as f:
        f.write(conteudo)
    print(f'ok {nome} {len(conteudo.encode()) / 1024:.0f} KB')

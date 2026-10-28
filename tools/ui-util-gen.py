# Generates the inline utility CSS (subset of Tailwind 3 used by the app) so the page needs no CDN runtime.
import re, sys
src = open(sys.argv[1], encoding='utf8').read()
lines = [l for l in src.split('\n') if len(l) < 20000]
text = '\n'.join(lines)
C = {'slate': {'200':'#e2e8f0','300':'#cbd5e1','400':'#94a3b8','500':'#64748b','600':'#475569','700':'#334155','800':'#1e293b','900':'#0f172a','950':'#020617'},
 'sky': {'200':'#bae6fd','300':'#7dd3fc','400':'#38bdf8','500':'#0ea5e9','800':'#075985','950':'#082f49'},
 'amber': {'200':'#fde68a','300':'#fcd34d','400':'#fbbf24','500':'#f59e0b'},
 'emerald': {'200':'#a7f3d0','300':'#6ee7b7','400':'#34d399','500':'#10b981'},
 'rose': {'300':'#fda4af','400':'#fb7185','500':'#f43f5e'}, 'red': {'400':'#f87171'}, 'green': {'400':'#4ade80'}}
# contrast lift for small text on dark glass (audit C32)
TEXT_LIFT = {'#64748b': '#8391a7', '#94a3b8': '#a3b1c6'}
FS = {'9px': '11px', '10px': '11px', '11px': '12px', '12px': '12px', '13px': '13px', '15px': '16px', '16px': '16px'}   # type scale, 11 px minimum (audit C24)
def col(s):
    if s == 'white': return '#fff'
    if s == 'black': return '#000'
    if s == 'transparent': return 'transparent'
    m = re.match(r'^([a-z]+)-(\d+)(?:/(\d+))?$', s)
    if not m or m.group(1) not in C or m.group(2) not in C[m.group(1)]: return None
    h = C[m.group(1)][m.group(2)]
    if m.group(3):
        a = int(m.group(3)) / 100; r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
        return f'rgba({r},{g},{b},{a:g})'
    return h
def sp(v): return '1px' if v == 'px' else f'{float(v) * 0.25:g}rem'
FIX = {'flex':'display:flex','inline-flex':'display:inline-flex','grid':'display:grid','hidden':'display:none','block':'display:block','inline':'display:inline','inline-block':'display:inline-block',
 'items-center':'align-items:center','items-end':'align-items:flex-end','items-start':'align-items:flex-start','justify-between':'justify-content:space-between','justify-center':'justify-content:center','justify-end':'justify-content:flex-end',
 'flex-wrap':'flex-wrap:wrap','flex-1':'flex:1 1 0%','flex-col':'flex-direction:column','shrink-0':'flex-shrink:0','min-w-0':'min-width:0','w-full':'width:100%','h-full':'height:100%',
 'border':'border-width:1px','border-t':'border-top-width:1px','border-b':'border-bottom-width:1px','rounded':'border-radius:.25rem','rounded-md':'border-radius:.375rem','rounded-lg':'border-radius:.5rem','rounded-full':'border-radius:9999px','rounded-xl':'border-radius:.75rem',
 'font-semibold':'font-weight:600','font-bold':'font-weight:700','font-medium':'font-weight:500','font-normal':'font-weight:400','text-xs':'font-size:12px;line-height:1.4','text-sm':'font-size:14px;line-height:1.35','text-right':'text-align:right','text-center':'text-align:center','text-left':'text-align:left',
 'truncate':'overflow:hidden;text-overflow:ellipsis;white-space:nowrap','whitespace-nowrap':'white-space:nowrap','leading-snug':'line-height:1.375','leading-relaxed':'line-height:1.6','leading-tight':'line-height:1.25',
 'absolute':'position:absolute','relative':'position:relative','fixed':'position:fixed','pointer-events-none':'pointer-events:none','pointer-events-auto':'pointer-events:auto','cursor-pointer':'cursor:pointer','cursor-grab':'cursor:grab','cursor-crosshair':'cursor:crosshair',
 'overflow-hidden':'overflow:hidden','overflow-auto':'overflow:auto','col-span-2':'grid-column:span 2/span 2','uppercase':'text-transform:uppercase','italic':'font-style:italic','select-none':'user-select:none','tracking-wide':'letter-spacing:.025em'}
def esc(c): return re.sub(r'([:\[\]/.%#()])', r'\\\1', c)
def rule(c):
    pre = ''; base = c
    m = re.match(r'^(sm|md|lg|hover|active):(.+)$', c)
    if m: pre, base = m.group(1), m.group(2)
    d = FIX.get(base)
    if not d:
        m = re.match(r'^(-?)(m|p)([trblxy]?)-([\d.]+|px|auto)$', base)
        if m:
            v = 'auto' if m.group(4) == 'auto' else (('-' if m.group(1) else '') + sp(m.group(4)))
            P = 'margin' if m.group(2) == 'm' else 'padding'
            S = {'': [''], 't': ['-top'], 'r': ['-right'], 'b': ['-bottom'], 'l': ['-left'], 'x': ['-left', '-right'], 'y': ['-top', '-bottom']}[m.group(3)]
            d = ';'.join(f'{P}{x}:{v}' for x in S)
    if not d:
        m = re.match(r'^gap-([\d.]+)$', base)
        if m: d = f'gap:{sp(m.group(1))}'
    if not d:
        m = re.match(r'^space-y-([\d.]+)$', base)
        if m: return f'.{esc(c)}>*+*{{margin-top:{sp(m.group(1))}}}'
    if not d:
        m = re.match(r'^(w|h|min-h|min-w|max-w|max-h)-\[(.+)\]$', base)
        if m: d = {'w':'width','h':'height','min-h':'min-height','min-w':'min-width','max-w':'max-width','max-h':'max-height'}[m.group(1)] + ':' + m.group(2)
    if not d:
        m = re.match(r'^(w|h)-([\d.]+)$', base)
        if m: d = ('width' if m.group(1) == 'w' else 'height') + ':' + sp(m.group(2))
    if not d:
        m = re.match(r'^(top|left|right|bottom)-([\d.]+)$', base)
        if m: d = f'{m.group(1)}:{sp(m.group(2))}'
    if not d:
        m = re.match(r'^z-(\d+)$', base)
        if m: d = f'z-index:{m.group(1)}'
    if not d:
        m = re.match(r'^grid-cols-(\d+)$', base)
        if m: d = f'grid-template-columns:repeat({m.group(1)},minmax(0,1fr))'
    if not d:
        m = re.match(r'^text-\[(\d+px)\]$', base)
        if m: d = 'font-size:' + FS.get(m.group(1), m.group(1))
    if not d:
        m = re.match(r'^(text|bg|border|accent)-(.+)$', base)
        if m:
            v = col(m.group(2))
            if v:
                if m.group(1) == 'text': v = TEXT_LIFT.get(v, v)
                d = {'text':'color','bg':'background-color','border':'border-color','accent':'accent-color'}[m.group(1)] + ':' + v
    if not d: return ''
    sel = '.' + esc(c) + (':hover' if pre == 'hover' else ':active' if pre == 'active' else '')
    r = f'{sel}{{{d}}}'
    if pre in ('sm', 'md', 'lg'): r = '@media (min-width:%dpx){%s}' % ({'sm': 640, 'md': 768, 'lg': 1024}[pre], r)
    return r
toks = set(re.findall(r'[A-Za-z0-9:\[\]/.#%()-]+', text))
out = []
order = lambda r: (0 if not r.startswith('@media') else 1)
rules = sorted({r for t in toks for r in [rule(t)] if r}, key=lambda r: (order(r), ':hover' in r or ':active' in r, r))
pre = ("*,::before,::after{box-sizing:border-box;border-width:0;border-style:solid;border-color:#334155}"
       "body{margin:0;line-height:1.5}h1,h2,h3,h4,p,figure,blockquote{margin:0}ol,ul{list-style:none;margin:0;padding:0}"
       "button,input,select,textarea{font:inherit;color:inherit;margin:0;padding:0;line-height:inherit}button,select{text-transform:none}"
       "button,[role=button]{cursor:pointer;background-color:transparent;background-image:none}:disabled{cursor:default}"
       "img,svg,video,canvas{display:block;vertical-align:middle}svg.ic{display:inline-block}table{border-collapse:collapse}[hidden]{display:none}summary{display:list-item}")
print('<style id="ui-util">/* utility classes (generated subset; replaces the Tailwind CDN runtime) */\n' + pre + '\n' + '\n'.join(rules) + '\n</style>')

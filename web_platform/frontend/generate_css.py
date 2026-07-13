"""
从 index.html 中提取所有 Tailwind 工具类，生成本地 CSS。
"""
import re
from collections import OrderedDict

# ── 读取 HTML ──
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# ── 提取所有 class 属性值 ──
classes = set()
for m in re.finditer(r'class=["\']([^"\']+)["\']', html):
    for cls in m.group(1).split():
        cls = cls.strip()
        if cls:
            classes.add(cls)

# ── Tailwind CSS 规则映射 ──
# 这是最常用的一批规则，覆盖 html 中用到的类

# 颜色映射（Tailwind 默认色板）
colors = {
    "slate":  {"50":"#f8fafc","100":"#f1f5f9","200":"#e2e8f0","300":"#cbd5e1","400":"#94a3b8","500":"#64748b","600":"#475569","700":"#334155","800":"#1e293b","900":"#0f172a"},
    "gray":   {"50":"#f9fafb","100":"#f3f4f6","200":"#e5e7eb","300":"#d1d5db","400":"#9ca3af","500":"#6b7280","600":"#4b5563","700":"#374151","800":"#1f2937","900":"#111827"},
    "indigo": {"50":"#eef2ff","100":"#e0e7ff","200":"#c7d2fe","300":"#a5b4fc","400":"#818cf8","500":"#6366f1","600":"#4f46e5","700":"#4338ca","800":"#3730a3","900":"#312e81"},
    "purple": {"50":"#faf5ff","100":"#f3e8ff","200":"#e9d5ff","300":"#d8b4fe","400":"#a855f7","500":"#8b5cf6","600":"#7c3aed","700":"#6d28d9","800":"#5b21b6","900":"#4c1d95"},
    "green":  {"50":"#f0fdf4","100":"#dcfce7","200":"#bbf7d0","300":"#86efac","400":"#4ade80","500":"#22c55e","600":"#16a34a","700":"#15803d","800":"#166534","900":"#14532d"},
    "red":    {"50":"#fef2f2","100":"#fee2e2","200":"#fecaca","300":"#fca5a5","400":"#f87171","500":"#ef4444","600":"#dc2626","700":"#b91c1c","800":"#991b1b","900":"#7f1d1d"},
    "amber":  {"50":"#fffbeb","100":"#fef3c7","200":"#fde68a","300":"#fcd34d","400":"#fbbf24","500":"#f59e0b","600":"#d97706","700":"#b45309","800":"#92400e","900":"#78350f"},
    "blue":   {"50":"#eff6ff","100":"#dbeafe","200":"#bfdbfe","300":"#93c5fd","400":"#60a5fa","500":"#3b82f6","600":"#2563eb","700":"#1d4ed8","800":"#1e40af","900":"#1e3a8a"},
    "emerald":{"50":"#ecfdf5","100":"#d1fae5","200":"#a7f3d0","300":"#6ee7b7","400":"#34d399","500":"#10b981","600":"#059669","700":"#047857","800":"#065f46","900":"#064e3b"},
    "white":  {"default":"#ffffff"},
    "black":  {"default":"#000000"},
}

# 间距映射
spacing = {
    "0":"0","0.5":"0.125rem","1":"0.25rem","1.5":"0.375rem",
    "2":"0.5rem","2.5":"0.625rem","3":"0.75rem","3.5":"0.875rem",
    "4":"1rem","5":"1.25rem","6":"1.5rem","7":"1.75rem",
    "8":"2rem","9":"2.25rem","10":"2.5rem","11":"2.75rem",
    "12":"3rem","14":"3.5rem","16":"4rem","20":"5rem",
    "24":"6rem","28":"7rem","32":"8rem","36":"9rem",
    "40":"10rem","44":"11rem","48":"12rem","52":"13rem",
    "56":"14rem","60":"15rem","64":"16rem","72":"18rem",
    "80":"20rem","96":"24rem",
    "px":"1px","auto":"auto","full":"100%","screen":"100vh",
    "1/2":"50%","1/3":"33.333333%","2/3":"66.666667%",
}

# 字体大小
font_sizes = {
    "xs":"0.75rem","sm":"0.875rem","base":"1rem",
    "lg":"1.125rem","xl":"1.25rem","2xl":"1.5rem",
    "3xl":"1.875rem","4xl":"2.25rem",
}

# 圆角
rounds = {
    "none":"0","sm":"0.125rem","md":"0.375rem",
    "lg":"0.5rem","xl":"0.75rem","2xl":"1rem","3xl":"1.5rem","full":"9999px",
}

# 生成 CSS
def generate():
    css_lines = ["/* Tailwind本地CSS — 零外网依赖 */", "*,::before,::after{box-sizing:border-box;margin:0;padding:0}"]

    # ── 背景色 bg-{color}-{shade} ──
    for name, shades in colors.items():
        for shade, hex_val in shades.items():
            shade_suffix = f"-{shade}" if shade != "default" else ""
            class_name = f"bg-{name}{shade_suffix}"
            if class_name in classes:
                css_lines.append(f".{class_name}{{background-color:{hex_val}}}")

            # bg-{color}-{shade}/50 等透明度
            for opacity in ["20","25","30","40","50","60","70","80","90"]:
                op_class = f"bg-{name}{shade_suffix}/{opacity}"
                if op_class in classes:
                    val = int(int(opacity) / 100 * 255)
                    css_lines.append(f".{op_class}{{background-color:rgba({hex_to_rgb(hex_val)},{opacity}/100)}}")

    # ── 文字颜色 ──
    for name, shades in colors.items():
        for shade, hex_val in shades.items():
            shade_suffix = f"-{shade}" if shade != "default" else ""
            class_name = f"text-{name}{shade_suffix}"
            if class_name in classes:
                css_lines.append(f".{class_name}{{color:{hex_val}}}")

    # ── 边框颜色 ──
    for name, shades in colors.items():
        for shade, hex_val in shades.items():
            shade_suffix = f"-{shade}" if shade != "default" else ""
            class_name = f"border-{name}{shade_suffix}"
            if class_name in classes:
                css_lines.append(f".{class_name}{{border-color:{hex_val}}}")

    # ── Padding / Margin ──
    for prop_short, prop_full in [("p","padding"),("px","padding-left;padding-right"),("py","padding-top;padding-bottom"),("pt","padding-top"),("pb","padding-bottom"),("pl","padding-left"),("pr","padding-right"),("m","margin"),("mx","margin-left;margin-right"),("my","margin-top;margin-bottom"),("mt","margin-top"),("mb","margin-bottom"),("ml","margin-left"),("mr","margin-right")]:
        for sp_key, sp_val in spacing.items():
            class_name = f"{prop_short}-{sp_key}"
            if class_name in classes:
                props = prop_full.split(";")
                rules = ";".join(f"{p}:{sp_val}" for p in props)
                css_lines.append(f".{class_name}{{{rules}}}")

    # ── 间距 gap / space ──
    for sp_key, sp_val in spacing.items():
        for prefix in ["gap","gap-x","gap-y","space-x","space-y"]:
            class_name = f"{prefix}-{sp_key}"
            if class_name in classes:
                css_lines.append(f".{class_name} > * + * {{{'margin-top' if 'y' in prefix else 'margin-left'}:{sp_val}}}")

    # ── 宽度/高度 ──
    for sp_key, sp_val in spacing.items():
        for prefix in ["w","h","max-w","max-h","min-w","min-h"]:
            class_name = f"{prefix}-{sp_key}"
            if class_name in classes:
                prop = {"w":"width","h":"height","max-w":"max-width","max-h":"max-height","min-w":"min-width","min-h":"min-height"}[prefix]
                css_lines.append(f".{class_name}{{{prop}:{sp_val}}}")

    # ── 字体大小 ──
    for key, val in font_sizes.items():
        class_name = f"text-{key}"
        if class_name in classes:
            css_lines.append(f".{class_name}{{font-size:{val}}}")

    # ── 圆角 ──
    for key, val in rounds.items():
        class_name = f"rounded-{key}"
        if class_name in classes:
            css_lines.append(f".{class_name}{{border-radius:{val}}}")

    # ── 字体粗细 ──
    for weight in ["normal","medium","semibold","bold","extrabold"]:
        class_name = f"font-{weight}"
        if class_name in classes:
            vals = {"normal":"400","medium":"500","semibold":"600","bold":"700","extrabold":"800"}
            css_lines.append(f".{class_name}{{font-weight:{vals[weight]}}}")

    # ── Display ──
    for d in ["hidden","block","inline","inline-block","flex","inline-flex","grid","inline-grid"]:
        class_name = d
        if class_name in classes:
            css_lines.append(f".{class_name}{{display:{d.replace('hidden','none')}}}")

    # ── Flex / Grid ──
    flex_align = {
        "items-center":"align-items:center","items-start":"align-items:flex-start","items-end":"align-items:flex-end",
        "justify-center":"justify-content:center","justify-between":"justify-content:space-between",
        "justify-start":"justify-content:flex-start","justify-end":"justify-content:flex-end",
        "flex-col":"flex-direction:column","flex-row":"flex-direction:row",
        "flex-wrap":"flex-wrap:wrap","flex-nowrap":"flex-wrap:nowrap",
        "shrink-0":"flex-shrink:0","grow":"flex-grow:1",
    }
    for cls, rule in flex_align.items():
        if cls in classes:
            css_lines.append(f".{cls}{{{rule}}}")

    # ── Grid columns ──
    for i in range(1,13):
        cls = f"grid-cols-{i}"
        if cls in classes:
            css_lines.append(f".{cls}{{grid-template-columns:repeat({i},minmax(0,1fr))}}")
    for i in range(1,13):
        cls = f"col-span-{i}"
        if cls in classes:
            css_lines.append(f".{cls}{{grid-column:span {i}/span {i}}}")
    # md:grid-cols-* variants
    for i in range(1,13):
        cls = f"md:col-span-{i}"
        if cls in classes:
            css_lines.append(f"@media(min-width:768px){{.{cls}{{grid-column:span {i}/span {i}}}}}")
        cls = f"md:grid-cols-{i}"
        if cls in classes:
            css_lines.append(f"@media(min-width:768px){{.{cls}{{grid-template-columns:repeat({i},minmax(0,1fr))}}}}")
    for i in range(1,13):
        cls = f"lg:grid-cols-{i}"
        if cls in classes:
            css_lines.append(f"@media(min-width:1024px){{.{cls}{{grid-template-columns:repeat({i},minmax(0,1fr))}}}}")

    # ── Position / Overflow / Z-index ──
    pos_map = {"relative":"position:relative","absolute":"position:absolute","fixed":"position:fixed","sticky":"position:sticky"}
    for cls, rule in pos_map.items():
        if cls in classes: css_lines.append(f".{cls}{{{rule}}}")
    for cls in ["overflow-hidden","overflow-auto","overflow-x-auto","overflow-y-auto","overflow-x-hidden"]:
        if cls in classes: css_lines.append(f".{cls}{{{cls.replace('overflow','overflow').replace('-',':')}}}")
    for i in range(0,51,10):
        cls = f"z-{i}"
        if cls in classes: css_lines.append(f".{cls}{{z-index:{i}}}")

    # ── Border ──
    if "border" in classes: css_lines.append(f".border{{border-width:1px;border-style:solid;border-color:#e2e8f0}}")
    for dir in ["t","b","l","r","x","y"]:
        prop = {"t":"top","b":"bottom","l":"left","r":"right","x":"left;right","y":"top;bottom"}[dir]
        for w in ["0","2","4","8"]:
            cls = f"border-{dir}-{w}"
            if cls in classes:
                rules = ";".join(f"border-{p}-width:{w}px" for p in prop.split(";"))
                css_lines.append(f".{cls}{{{rules}}}")
    for style in ["solid","dashed","dotted","none"]:
        cls = f"border-{style}"
        if cls in classes: css_lines.append(f".{cls}{{border-style:{style}}}")

    # ── 阴影 ──
    shadows = {
        "shadow-sm":"box-shadow:0 1px 2px 0 rgba(0,0,0,.05)",
        "shadow":"box-shadow:0 1px 3px 0 rgba(0,0,0,.1),0 1px 2px -1px rgba(0,0,0,.1)",
        "shadow-md":"box-shadow:0 4px 6px -1px rgba(0,0,0,.1),0 2px 4px -2px rgba(0,0,0,.1)",
        "shadow-lg":"box-shadow:0 10px 15px -3px rgba(0,0,0,.1),0 4px 6px -4px rgba(0,0,0,.1)",
        "shadow-xl":"box-shadow:0 20px 25px -5px rgba(0,0,0,.1),0 8px 10px -6px rgba(0,0,0,.1)",
    }
    for cls, rule in shadows.items():
        if cls in classes: css_lines.append(f".{cls}{{{rule}}}")

    # ── Opacity ──
    for i in [0,5,10,20,25,30,40,50,60,70,75,80,90,95,100]:
        cls = f"opacity-{i}"
        if cls in classes: css_lines.append(f".{cls}{{opacity:{i/100}}}")

    # ── Transition ──
    if "transition-all" in classes: css_lines.append(".transition-all{transition-property:all;transition-timing-function:cubic-bezier(0.4,0,0.2,1);transition-duration:150ms}")
    if "transition-colors" in classes: css_lines.append(".transition-colors{transition-property:color,background-color,border-color,text-decoration-color,fill,stroke;transition-timing-function:cubic-bezier(0.4,0,0.2,1);transition-duration:150ms}")
    if "transition-transform" in classes: css_lines.append(".transition-transform{transition-property:transform;transition-timing-function:cubic-bezier(0.4,0,0.2,1);transition-duration:150ms}")
    if "duration-300" in classes: css_lines.append(".duration-300{transition-duration:300ms}")

    # ── 文本对齐 / 装饰 ──
    for ta in ["left","center","right","justify"]:
        cls = f"text-{ta}"
        if cls in classes: css_lines.append(f".{cls}{{text-align:{ta}}}")
    truncate_rules = {"truncate":"overflow:hidden;text-overflow:ellipsis;white-space:nowrap","whitespace-nowrap":"white-space:nowrap"}
    for cls, rule in truncate_rules.items():
        if cls in classes: css_lines.append(f".{cls}{{{rule}}}")

    # ── Tracking (letter-spacing) ──
    trackings = {"tracking-tight":"letter-spacing:-0.025em","tracking-wide":"letter-spacing:0.025em","tracking-wider":"letter-spacing:0.05em"}
    for cls, val in trackings.items():
        if cls in classes: css_lines.append(f".{cls}{{{val}}}")

    # ── 行高 ──
    line_heights = {"leading-tight":"line-height:1.25","leading-normal":"line-height:1.5","leading-relaxed":"line-height:1.625","leading-none":"line-height:1"}
    for cls, val in line_heights.items():
        if cls in classes: css_lines.append(f".{cls}{{{val}}}")

    # ── Cursor ──
    cursors = {"cursor-pointer":"cursor:pointer","cursor-not-allowed":"cursor:not-allowed","cursor-default":"cursor:default"}
    for cls, rule in cursors.items():
        if cls in classes: css_lines.append(f".{cls}{{{rule}}}")

    # ── Outline ──
    if "outline-none" in classes: css_lines.append(".outline-none{outline:2px solid transparent;outline-offset:2px}")

    # ── Hover variants ──
    hover_map = {
        "hover:bg-slate-50":"background-color:#f8fafc",
        "hover:bg-slate-50\\/50":"background-color:rgba(248,250,252,0.5)",
        "hover:bg-slate-100":"background-color:#f1f5f9",
        "hover:bg-green-100":"background-color:#dcfce7",
        "hover:bg-indigo-700":"background-color:#4338ca",
        "hover:bg-indigo-50\\/50":"background-color:rgba(238,242,255,0.5)",
        "hover:text-indigo-600":"color:#4f46e5",
        "hover:text-indigo-800":"color:#3730a3",
        "hover:from-indigo-700":"--tw-gradient-from:#4338ca",
        "hover:to-purple-700":"--tw-gradient-to:#6d28d9",
        "hover:border-indigo-400":"border-color:#818cf8",
        "hover:bg-indigo-50\\/50":"background-color:rgba(238,242,255,0.5)",
    }
    for cls, rule in hover_map.items():
        if cls in classes or cls.replace("\\","") in " ".join(classes):
            css_lines.append(f".{cls}:hover{{{rule}}}")

    # ── Group hover variants ──
    if any("group-hover:" in c for c in classes):
        if "group-hover:scale-110" in classes:
            css_lines.append(".group:hover .group-hover\\:scale-110{transform:scale(1.1)}")
        if "group-hover:block" in classes:
            css_lines.append(".group:hover .group-hover\\:block{display:block}")

    # ── Peer variants ──
    if any("peer-" in c for c in classes):
        css_lines.append(".peer:checked ~ .peer-checked\\:bg-indigo-600{background-color:#4f46e5}")
        css_lines.append(".peer:checked ~ .peer-checked\\:text-white{color:#fff}")

    # ── Focus variants ──
    focus_rules = {
        "focus:ring-2":"box-shadow:var(--tw-ring-inset) 0 0 0 calc(2px + var(--tw-ring-offset-width)) var(--tw-ring-color)",
        "focus:ring-indigo-500":"--tw-ring-color:#6366f1;--tw-ring-opacity:1",
        "focus:ring-indigo-500\\/20":"--tw-ring-color:rgba(99,102,241,0.2)",
        "focus:border-indigo-500":"border-color:#6366f1",
    }
    for cls, rule in focus_rules.items():
        if cls in classes:
            css_lines.append(f".{cls}:focus{{{rule}}}")

    # ── Disabled variants ──
    dis_rules = {
        "disabled:opacity-50":"opacity:0.5",
        "disabled:cursor-not-allowed":"cursor:not-allowed",
    }
    for cls, rule in dis_rules.items():
        if cls in classes:
            css_lines.append(f".{cls}:disabled{{{rule}}}")

    # ── 通用：uppercase / font-mono / backdrop-blur / list-disc ──
    misc = {
        "uppercase":"text-transform:uppercase",
        "font-mono":"font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace",
        "backdrop-blur":"backdrop-filter:blur(8px)",
        "list-disc":"list-style-type:disc",
        "table":"display:table",
        "contents":"display:contents",
        "antialiased":"-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale",
        "select-none":"user-select:none",
        "pointer-events-none":"pointer-events:none",
        "invisible":"visibility:hidden",
        "visible":"visibility:visible",
        "sr-only":"position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border-width:0",
        "break-all":"word-break:break-all",
    }
    for cls, rule in misc.items():
        if cls in classes:
            css_lines.append(f".{cls}{{{rule}}}")

    # ── Gradient ──
    if "bg-gradient-to-r" in classes:
        css_lines.append(".bg-gradient-to-r{background-image:linear-gradient(to right,var(--tw-gradient-from),var(--tw-gradient-to))}")
    if "bg-gradient-to-b" in classes:
        css_lines.append(".bg-gradient-to-b{background-image:linear-gradient(to bottom,var(--tw-gradient-from),var(--tw-gradient-to))}")
    grad_froms = {
        "from-indigo-600":"--tw-gradient-from:#4f46e5;--tw-gradient-to:rgba(79,70,229,0);--tw-gradient-stops:var(--tw-gradient-from),var(--tw-gradient-to)",
        "from-green-50\\/50":"--tw-gradient-from:rgba(240,253,244,0.5);--tw-gradient-to:rgba(240,253,244,0);--tw-gradient-stops:var(--tw-gradient-from),var(--tw-gradient-to)",
        "from-red-50\\/50":"--tw-gradient-from:rgba(254,242,242,0.5);--tw-gradient-to:rgba(254,242,242,0)",
        "from-amber-50\\/50":"--tw-gradient-from:rgba(255,251,235,0.5);--tw-gradient-to:rgba(255,251,235,0)",
        "from-blue-50\\/50":"--tw-gradient-from:rgba(239,246,255,0.5);--tw-gradient-to:rgba(239,246,255,0)",
        "from-purple-50\\/50":"--tw-gradient-from:rgba(250,245,255,0.5);--tw-gradient-to:rgba(250,245,255,0)",
        "from-indigo-600":"--tw-gradient-from:#4f46e5;--tw-gradient-to:rgba(79,70,229,0)",
    }
    tos = {
        "to-purple-600":"--tw-gradient-to:#7c3aed",
        "to-green-50\\/50":"--tw-gradient-to:rgba(240,253,244,0.5)",
        "to-red-50\\/50":"--tw-gradient-to:rgba(254,242,242,0.5)",
        "to-amber-50\\/50":"--tw-gradient-to:rgba(255,251,235,0.5)",
        "to-blue-50\\/50":"--tw-gradient-to:rgba(239,246,255,0.5)",
        "to-purple-50\\/50":"--tw-gradient-to:rgba(250,245,255,0.5)",
    }
    for cls, rule in grad_froms.items():
        if cls in classes: css_lines.append(f".{cls}{{{rule}}}")
    for cls, rule in tos.items():
        if cls in classes: css_lines.append(f".{cls}{{{rule}}}")

    # ── Divide ──
    for name, shades in colors.items():
        for shade, hex_val in shades.items():
            shade_suffix = f"-{shade}" if shade != "default" else ""
            cls = f"divide-{name}{shade_suffix}"
            if cls in classes:
                css_lines.append(f".{cls} > * + * {{border-color:{hex_val}}}")
    if "divide-y" in classes:
        css_lines.append(".divide-y > * + * {border-top-width:1px;border-bottom-width:0}")
    if "divide-x" in classes:
        css_lines.append(".divide-x > * + * {border-left-width:1px;border-right-width:0}")

    # ── min-height ──
    if "min-h-screen" in classes:
        css_lines.append(".min-h-screen{min-height:100vh}")

    # ── Responsive (md: / lg:) ──
    responsive = {}
    # md:col-span-2, md:col-span-4, md:col-span-6, md:col-span-12, lg:grid-cols-2
    for cls in classes:
        if cls.startswith("md:") or cls.startswith("lg:"):
            responsive[cls] = True

    # 部分常用响应式规则
    for bp, min_w in [("md:","768px"),("lg:","1024px"),("xl:","1280px")]:
        bp_classes = [c for c in classes if c.startswith(bp)]
        if bp_classes:
            # 生成一个媒体查询，把常用的规则放进去
            rules = []
            for cls in bp_classes:
                base = cls[len(bp):]
                # md:col-span-2 → .md\:col-span-2 { grid-column: span 2 / span 2 }
                esc = cls.replace(":", "\\:")
                if base.startswith("col-span-"):
                    n = base.split("-")[-1]
                    try:
                        int(n)
                        rules.append(f".{esc}{{grid-column:span {n}/span {n}}}")
                    except: pass
                elif base.startswith("grid-cols-"):
                    n = base.split("-")[-1]
                    try:
                        int(n)
                        rules.append(f".{esc}{{grid-template-columns:repeat({n},minmax(0,1fr))}}")
                    except: pass
            if rules:
                css_lines.append(f"@media(min-width:{min_w}){{{';'.join(rules)}}}")

    # ── margin-left:auto ──
    if "ml-auto" in classes: css_lines.append(".ml-auto{margin-left:auto}")
    if "mr-auto" in classes: css_lines.append(".mr-auto{margin-right:auto}")
    if "mx-auto" in classes: css_lines.append(".mx-auto{margin-left:auto;margin-right:auto}")

    # ── Ring ──
    css_lines.append("""
:root{--tw-ring-inset: ;--tw-ring-offset-width:0px;--tw-ring-offset-color:#fff;--tw-ring-color:rgba(59,130,246,.5);--tw-ring-offset-shadow:0 0 #0000;--tw-ring-shadow:0 0 #0000;--tw-shadow:0 0 #0000}
""")

    return "\n".join(css_lines)


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return ",".join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))


if __name__ == "__main__":
    css = generate()
    # 统计
    class_count = len(classes)
    line_count = css.count("\n")
    size_kb = len(css) / 1024
    print(f"// 扫描到 {class_count} 个类名 → 生成 {line_count} 条规则 → {size_kb:.1f}KB")

    with open("tailwind-local.css", "w", encoding="utf-8") as f:
        f.write(css)
    print("// 已写入 tailwind-local.css")

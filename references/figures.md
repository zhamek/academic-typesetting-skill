# 插图

插图出问题多半不是"画得不好看"，而是**尺寸、字体、格式**三件事没和正文对上。

画什么、怎么配色、面板怎么排，找 `nature-figure`（数据图）或 `figkit-bw-figure`（黑白矢量示意图）。
本文只管"怎么让它干净地落进文档"。

## 1 按印刷宽度作图

最省事的做法：**画布宽度 = 最终印刷宽度**。

```python
FIG_W = 6.30            # inch；16.0 cm 版心
fig = plt.figure(figsize=(FIG_W, 4.2))
```

这样脚本里写 `fontsize=8` 印出来就是 8pt，不需要事后缩放，也不会出现"图里 9pt 缩到 7pt 看不清"。

反过来若画布 7.2 inch 却插进 16cm 宽，缩放系数 0.886，所有字都偷偷变小 11%。

版心宽参考：A4 + 2.5cm 边距 = 16.0cm；双栏期刊单栏 89mm、通栏 183mm；16:9 幻灯片正文区约 12in。

## 2 图内字体必须和正文同族

```python
from matplotlib.font_manager import FontProperties
SUN = FontProperties(fname=r"C:\Windows\Fonts\simsun.ttc")
HEI = FontProperties(fname=r"C:\Windows\Fonts\simhei.ttf")
TNR = FontProperties(family="Times New Roman")
```

- 中文用宋体（说明性小字）或黑体（标签），西文/数字 Times。
- 不要混用：一张图里出现三种字体族，比字号小更显廉价。

### 两个会静默回退的坑（实测）

| 坑 | 现象 | 修法 |
| --- | --- | --- |
| mathtext | 图里 `$CO_2$`、`g·L$^{-1}$` 的上下标变成 **DejaVu Sans**（无衬线），和旁边的 Times 不搭 | 图内干脆不写数学：写"二氧化碳"、`g / L`；实在要写则设 `rcParams['mathtext.fontset']='custom'` 并指定 Times |
| 中文缺字 | 字体文件里没有 `₂`(U+2082)、`⁻`(U+207B) 这类字符，会掉回默认字体 | 同上，换成文字或普通上下标写法 |

验收方法：出图后查一遍字体。

```python
import fitz
for span in [s for p in fitz.open("fig.pdf") for b in p.get_text("dict")["blocks"]
             for l in b.get("lines", []) for s in l["spans"]]:
    assert "DejaVu" not in span["font"], span
```

## 3 矢量优先

- PDF 后端出 **PDF**（`pdf.fonttype=42`，TrueType 嵌入），Word/PPT 用 **SVG**。
- 位图只用于电镜、凝胶这类本来就没有矢量的图，且 ≥ 300 dpi。
- 有效分辨率算法：`dpi = 像素宽 / (显示宽度 inch)`。一张 2000px 的图放在 16cm（6.3in）宽上是 317dpi，合格；放在 8cm 宽就浪费。
- 不允许"PDF 里贴位图"冒充矢量——`qa_pdf.py` 会把 `page.get_images()` 非空的页报出来。

## 4 图注

图注在图下方，先一句"这张图说明什么"，再一句方法和统计。

```
图 2　酿酒酵母青蒿酸合成路线与滴度提升。(A) 途径模块与区室分工，箭头上方为酶或化学步骤；
(B) 2006 年与 2013 年报道的发酵滴度（对数刻度）。流程为概念示意，未按化学计量与区室比例绘制。
```

- 分图用 (A)(B)(C)，与图内面板字母一致。
- 概念示意图必须注明"未按比例/未按计量"——这是诚实，也是免责。
- 图注里不要重复正文结论句。

## 5 图和表的取舍

| 内容 | 用图 | 用表 |
| --- | --- | --- |
| 趋势、分布、比较的方向 | ✓ | |
| 精确数值、多属性并列 | | ✓ |
| 流程、机制、空间关系 | ✓ | |
| 同一组数据既画图又列表 | 只留一个，另一个进附录 | |

同一份内容"表 3 已经写全了，再画一张图 1 复述"是评审最常挑的冗余。

## 6 落地检查

1. 插入时写 `width=\linewidth`（或 `width=183mm`），不要让图按原始尺寸落地。
2. 出图后跑 `contact_sheet.py` 看整页效果：图是否和正文左右边界对齐、图题是否孤零零留在上一页。
3. 图比版心宽 2–3pt 是 `bbox_inches='tight'` 的 pad 造成的，`width=\linewidth` 一并解决。

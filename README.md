# A320 点阵模型 / A320 Point-Lattice Model

用**点阵（点云）方式**对空客 **A320-200** 外形进行近似参数化建模，生成的坐标点可直接导入
CATIA（或其他 CAD）做**多截面曲面 / NURBS 蒙皮 / 点云拟合**。

A structured **point lattice** of an approximate Airbus **A320-200** outer-mould-line,
ready for CATIA surface lofting (multi-section surface, NURBS skinning, cloud-to-surface).

> ⚠️ **免责声明 / Disclaimer**：本模型使用**公开的、近似的** A320 尺寸，仅为布局示意、
> 教学与可视化用途，**不是**工程/适航/制造数据。所有坐标单位为 **毫米（mm）**。

---

## 1. 内容 / Contents

| 文件 / File | 说明 / Description |
| --- | --- |
| `generate_lattice.py` | 点阵生成脚本（可改参数重新生成，含机翼扭转角 + 翼尖小翼） |
| `A320_point_lattice.xlsx` | 点阵总表，每个部件一个 Sheet + 参数表 |
| `csv/` | 每个部件一个 CSV，便于 CATIA 导入 |
| `A320.obj` | 全机三角网格（用于快速预览 / 导入网格） |
| `preview.png` | 全机渲染预览图 |
| `build_in_catia.py` | **CATIA COM 自动化**：自动建点、样条线框、放样曲面 |
| `import_points.CATScript` | CATIA VBA 宏：把 CSV 批量导入为几何点（手动备选） |
| `preview.py` | 渲染 `A320.obj` 为 PNG（需 matplotlib） |

部件 Sheets：`Fuselage`（机身）、`Wing`（机翼）、`Winglet`（翼尖小翼）、`H_Tail`（平尾）、`V_Tail`（垂尾）、`Engine`（发动机舱）。

---

## 2. 坐标系 / Coordinate System

| 轴 | 方向 | 说明 |
| --- | --- | --- |
| **原点 O** | 机头尖端 | 机身中心线（Y=0）与机身纵轴高度（Z=0）交点 |
| **+X** | 纵向，指向机尾 | longitudinal, toward tail |
| **+Y** | 展向，指向**右翼**（starboard） | spanwise |
| **+Z** | 竖直向上 | vertical, up |
| **单位** | **毫米 mm** | 1 m = 1000 mm |

CATIA 中对应：`X → 长度 / Y → 宽度 / Z → 高度`（CATIA 默认绝对轴即如此，直接导入即可）。

---

## 3. 表格列说明 / Sheet Columns

| 列 | 含义 |
| --- | --- |
| `ID` | 部件内唯一序号 |
| `Station` | 沿**纵向/展向/高度**方向的截面编号 |
| `Section` | 同一截面上绕**截面/翼型**的周向点编号 |
| `Side` | `L`（左）/ `R`（右）/ `C`（对称中面）/ 空 |
| `X, Y, Z` | 坐标（mm） |

**点阵结构**：同一 `Station` 内的 `Section` 顺序固定（闭合环：后缘下表面 → 前缘 → 后缘上表面）。
把不同 `Station` 间**相同 `Section`** 的点连起来，就是 CATIA 放样所需的引导线（guide curves）。

---

## 4. 部件几何要点 / Component geometry

- **机身 Fuselage**：绕 X 轴的回转体 + 椭圆截面（宽 3.95 m / 高 4.14 m），机头与尾锥按半径型线插值。
- **机翼 Wing**：NACA 2412，后掠 25°，根弦 7.4 m → 梢弦 1.4 m，上反角 5.1°，半展长 17.05 m；
  **几何扭转角（washout）**：根 +3°（抬头）线性扭转到梢 **-2°**（低头），共 5° 扭转。
- **翼尖小翼 Winglet**：鲨鳍式（sharklet），高 2.4 m，外倾 30°，后掠 50°，梢弦 0.65 m，NACA 0010 薄对称翼型。
- **平尾 H_Tail**：NACA 0012，展长 12.45 m，后掠 30°。
- **垂尾 V_Tail**：NACA 0010 对称翼型，高 6.2 m，后掠 40°。
- **发动机舱 Engine**：绕 X 轴的回转体（CFM56-5B 级别，最大直径 ≈ 2.01 m，长 ≈ 3.3 m），左右各一，吊挂在机翼下方。

所有参数集中在 `generate_lattice.py` 各函数中，可随时调整。

---

## 5. 生成方法 / How to regenerate

```bash
pip install -r requirements.txt
python generate_lattice.py     # 产出 xlsx + csv + obj
python preview.py              # 可选：渲染预览图（需 matplotlib）
```

---

## 6. 导入 CATIA / Import into CATIA

### 方法 A：一键自动建模（推荐）
在装有 CATIA V5（Windows）的机器上：
```bash
pip install pywin32
python build_in_catia.py
```
脚本会**启动 CATIA**（或连接已运行的实例），自动：新建 Part → 导入全部点阵到几何图形集
→ 建立截面闭合样条 + 展向引导样条 → **多截面放样曲面** → 适配视图。

### 方法 B：Excel 宏（手动建点）
1. 打开 CATIA Part，`工具 → 宏` 导入 `import_points.CATScript`，运行后选择 `csv/` 下某个 CSV，
   自动把每个点建成 `HybridShapePointCoord`。
2. 之后用 **多截面曲面**（Multi-Section Surface）选择各 `Station` 的截面环放样。

### 方法 C：网格导入
`A320.obj`（或另存为 STL）可直接 `File → Open` 作为网格查看。

---

## 7. 仓库结构 / Repo layout

```
A320-point-lattice/
├── generate_lattice.py
├── A320_point_lattice.xlsx
├── A320.obj
├── preview.png
├── csv/            (Fuselage / Wing / Winglet / H_Tail / V_Tail / Engine .csv)
├── build_in_catia.py
├── import_points.CATScript
├── preview.py
├── requirements.txt
└── README.md
```

---

## 8. 参数 / Key parameters (approximate A320-200)

| 参数 | 值 |
| --- | --- |
| 机身长 | 37.57 m |
| 机身最大宽 / 高 | 3.95 m / 4.14 m |
| 翼展 | 34.10 m（翼尖小翼外扩后 ≈ 36.5 m） |
| 翼根 / 翼梢弦 | 7.4 m / 1.4 m |
| 机翼根/梢安装角 | +3° / −2°（5° washout） |
| 翼尖小翼高 / 外倾 | 2.4 m / 30° |
| 平尾展长 | 12.45 m |
| 垂尾高 | 6.2 m |
| 发动机舱最大直径 | ≈ 2.01 m |
| 发动机展向位置 | 距中心线 ±5.75 m |

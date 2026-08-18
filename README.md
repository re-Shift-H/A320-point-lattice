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
| `generate_lattice.py` | 生成点阵的 Python 脚本（可改参数重新生成） |
| `A320_point_lattice.xlsx` | 点阵总表，每个部件一个 Sheet + 参数表 |
| `csv/` | 每个部件一个 CSV，便于 CATIA 直接导入 |
| `import_points.CATScript` | CATIA VBA 宏：把 CSV 批量导入为几何点 |

部件 Sheets：`Fuselage`（机身）、`Wing`（机翼）、`H_Tail`（平尾）、`V_Tail`（垂尾）、`Engine`（发动机舱）。

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

每个部件 Sheet 的列：

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
- **机翼 Wing**：NACA 2412，后掠 25°，根弦 7.4 m → 梢弦 1.4 m，上反角 5.1°，半展长 17.05 m。
- **平尾 H_Tail**：NACA 0012，展长 12.45 m，后掠 30°。
- **垂尾 V_Tail**：NACA 0010 对称翼型，高 6.2 m，后掠 40°。
- **发动机舱 Engine**：绕 X 轴的回转体（CFM56-5B 级别，最大直径 ≈ 2.01 m，长 ≈ 3.3 m），左右各一，吊挂在机翼下方。

所有参数均集中在 `generate_lattice.py` 顶部各函数中，可随时调整。

---

## 5. 生成方法 / How to regenerate

```bash
pip install -r requirements.txt
python generate_lattice.py
```

输出：`A320_point_lattice.xlsx` 与 `csv/*.csv`。

---

## 6. 导入 CATIA / Import into CATIA

### 方法 A：Excel 宏（推荐，直接建点 + 命名）
1. 打开 CATIA（新建或打开一个 Part）。
2. `工具 → 宏 → 宏...`（Tools → Macro → Macros），创建/导入 `import_points.CATScript`。
3. 运行后选择 `csv/` 下某个 CSV（如 `Fuselage.csv`），脚本会新建几何图形集并把每个点
   建成 `HybridShapePointCoord`。
4. 之后可用 **多截面曲面** 或 **点云 → 网格 → 曲面** 生成蒙皮。

### 方法 B：Excel 点导入
1. 打开一个 Part，进入 `Generative Shape Design`（创成式外形设计）。
2. 插入几何图形集，`点` → `坐标点`，逐个输入（适合少量点）。
3. 或用 CATIA 的 "Import Points" / 脚本批量导入 CSV。

### 方法 C：第三方点云工具
把 CSV 另存为 `.asc` / `.xyz`（空格分隔 X Y Z），用 CATIA 的 **Digitized Shape Editor**（DSE）
或 `Cloud import` 读入为点云，再做 mesh/曲面。

---

## 7. 仓库结构 / Repo layout

```
A320-point-lattice/
├── generate_lattice.py
├── A320_point_lattice.xlsx
├── csv/
│   ├── Fuselage.csv
│   ├── Wing.csv
│   ├── H_Tail.csv
│   ├── V_Tail.csv
│   └── Engine.csv
├── import_points.CATScript
├── requirements.txt
└── README.md
```

---

## 8. 参数 / Key parameters (approximate A320-200)

| 参数 | 值 |
| --- | --- |
| 机身长 | 37.57 m |
| 机身最大宽 / 高 | 3.95 m / 4.14 m |
| 翼展 | 34.10 m（鲨鳍小翼型为 35.8 m） |
| 翼根 / 翼梢弦 | 7.4 m / 1.4 m |
| 平尾展长 | 12.45 m |
| 垂尾高 | 6.2 m |
| 发动机舱最大直径 | ≈ 2.01 m |
| 发动机展向位置 | 距中心线 ±5.75 m |

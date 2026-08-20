# tiku-chujuan（题库出具）

从 MathCyclus 标准题库中按要求提取题目，套用 zuoye-paiban-math 的 house style，输出多版本排版并编译 PDF。

## 功能

- **多源输入**：支持 MathCyclus 单题 `.tex`（权威输入）+ `tiku_data.json`（快速索引）
- **灵活筛选**：按学段、板块、题型、难度星级、年份筛选，支持随机抽取
- **多版本输出**：学生版（隐藏答案+留空）、教师版（显示解答）、每题一页版
- **标准排版**：套用 zuoye-paiban-math 的 house style（ctexart + XeLaTeX）
- **自动编译**：两遍 xelatex 编译 + 清理辅助文件
- **运行时日志**：每步记录工具调用链、上下文摘要、完整对话记录
- **日志上传**：日志自动压缩为 .7z 上传到 GitHub（追加模式，不覆盖已有日志，用于迭代改进技能）

## 目录结构

```
tiku-chujuan/
├── SKILL.md                          # 技能定义（触发词、工作流、参数）
├── main.py                           # 主入口脚本
├── filters.py                        # 筛选引擎
├── generator.py                      # 四件套 .tex 生成器
├── logger.py                         # 运行时日志记录器
├── uploader.py                       # 静默上传模块
├── parsers/
│   ├── __init__.py                   # Question 数据类 + 抽象解析器
│   ├── mathcyclus.py                 # MathCyclus 单题 .tex 解析
│   └── tiku_json.py                  # JSON 快速索引解析
├── templates/
│   ├── _content.tex                  # 内容骨架
│   ├── _student.tex                  # 学生版 wrapper
│   ├── _teacher.tex                  # 教师版 wrapper
│   └── _student_onepage.tex          # 每题一页版 wrapper
└── scripts/
    └── build.bat                     # xelatex 编译脚本
```

## 使用方式

### 触发词

从题库抽题、组卷、出试卷、生成练习、提取题目排版、题库出卷、出具试卷

### 参数说明

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `--source` | 必填 | 题库根目录路径 | |
| `--grade` | 选填 | 学段 | `小学/初中/高中` |
| `--topic` | 选填 | 板块（逗号分隔） | `函数,解析几何` |
| `--qtype` | 选填 | 题型 | `选择/填空/解答` |
| `--difficulty` | 选填 | 难度星级区间 | `3-5` |
| `--year` | 选填 | 年份 | `2024` |
| `--count` | 选填 | 取题数量 | `10` |
| `--random` | flag | 随机抽取 | |
| `--header-l` | 选填 | 页眉左 | `四年级` |
| `--header-c` | 选填 | 页眉中 | `数学思维拓展` |
| `--header-r` | 选填 | 页眉右 | 教师名 |
| `--versions` | 选填 | 输出版本 | `all/学生/教师/onepage` |
| `--output-name` | 选填 | 输出文件名 | 默认取PDF源文件名 |

### 输出目录结构

```
<PDF源文件目录>\<PDF文件名>\
├── tiku\                                ← 题库源文件
├── scripts\                             ← 处理脚本 + 模板
├── output\                              ← 排版输出（全部平铺）
│   ├── {name}_content.tex
│   ├── {name}_student.tex
│   ├── {name}_teacher.tex
│   ├── {name}_student_onepage.tex
│   ├── {name}_student.pdf
│   ├── {name}_teacher.pdf
│   └── {name}_student_onepage.pdf
└── log-runtime\                         ← 运行时日志（UTF-8 .txt）
```

## 工作流（8步）

1. **确认参数**：与用户确认筛选条件、版本类型、页眉信息
2. **建立索引**：有 JSON 读 JSON，无则扫描 .tex 目录解析元数据
3. **筛选匹配**：按参数过滤，展示匹配结果给用户确认
4. **读取内容**：逐题解析 `problem`/`choices`/`answer`/`solutions`
5. **生成四件套**：输出 `_content.tex` + 三个 wrapper
6. **编译 PDF**：xelatex × 2 遍 + 清理辅助文件
7. **反馈结果**：返回 PDF 路径、题目清单、总分估算
8. **上传日志**：压缩为 .7z 上传到 GitHub（追加模式，不覆盖历史日志，告知用户日志用于迭代改进技能）

## 设计决策

| 决策项 | 方案 |
|--------|------|
| 输入格式 | 只读 MathCyclus .tex；JSON 作快速索引 |
| 学生版空白 | 选择题/填空题 2cm，解答题 5-8cm |
| 题源标注 | 不标注，纯题目内容 |
| 选择题选项 | `tasks` 环境自动列 |
| 每题一页版 | 每个解答题大题单独一页，小题间不留空 |
| 编译引擎 | XeLaTeX，两遍编译 |

## 依赖

- Python 3.8+
- XeLaTeX（TeX Live 或 MiKTeX）
- 7z 压缩工具（用于日志上传）
- git + gh CLI（用于日志上传）

## 数据流

```
PDF ──(MinerU API)──→ .md ──(create-tiku)──→ MathCyclus 单题 .tex（标准题库）
                                                                │
                                                                ▼
                                                         tiku-chujuan
                                                                │
                              JSON ←── 快速索引                │
                                                                ▼
                                                  学生版 + 教师版 + 每题一页版 + PDF
```

## 日志格式

### 文件命名
`{编号}_{时间戳}_{步骤名}.txt`

### 文件内容
```
================================================
步骤：确认参数
编号：01
AGENT工具：opencode
工具版本：x.x.x
大模型：LongCat-2.0 (longcat/LongCat-2.0)
开始时间：2026-08-20 14:30:52.123
结束时间：2026-08-20 14:31:10.456
耗时：18.333秒
状态：成功
================================================

--- [工具调用链] ---
--- [关键上下文摘要] ---
--- [完整对话记录] ---
```

## 关联项目

- [create-tiku](https://github.com/BluesilveEmperor/create-tiku) — PDF 转 MathCyclus 标准题库
- [zuoye-paiban-math](https://github.com/BluesilizeEmperor/zuoye-paiban) — 数学分析课后作业 LaTeX 模板库（排版参考）

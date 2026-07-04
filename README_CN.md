# MedVision AI — 医学影像 AI 诊断系统

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-≥3.10-blue" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/status-active-brightgreen" alt="Status">
  <img src="https://img.shields.io/badge/modalities-CT|MR|XR-informational" alt="Modalities">
</p>

<p align="center">
  <strong>AI 驱动的 DICOM 分析 · 异常检测 · 结构化放射学报告 · 多模态支持</strong>
</p>

---

## 目录

- [项目概述](#项目概述)
- [为什么选择 MedVision AI](#为什么选择-medvision-ai)
- [系统架构](#系统架构)
- [核心功能](#核心功能)
- [快速开始](#快速开始)
- [分析管道](#分析管道)
- [窗宽窗位预设](#窗宽窗位预设)
- [CLI 参考](#cli-参考)
- [开发指南](#开发指南)
- [许可证](#许可证)

---

## 项目概述

**MedVision AI** 是一个 AI 驱动的医学影像诊断系统，旨在辅助放射科医师分析 DICOM 检查、检测临床显著发现并生成结构化放射学报告。它支持多种成像模态（CT、MRI、X 射线），提供从 DICOM 加载到报告生成的完整管道。

MedVision AI 完善了 `github-big-proj` 医疗技术套件，与 BioOmics Bridge（proj3 — 生物数据）、PharmaGuard（proj4 — 药物安全）和 GeneSight AI（proj7 — 基因组学）形成完整闭环，将 AI 辅助诊断影像纳入该生态系统。

### 解决什么问题？

放射科面临日益增长的影像量与有限的专科医师资源之间的矛盾。研究表明，放射科医师因疲劳和认知过载会漏诊约 3-5% 的显著发现。MedVision AI 通过以下方式应对：

- **AI 辅助检测**：多模型集成实现一致、无需休息的异常检测。
- **自动化报告**：数秒内生成结构化放射学报告，而非数小时。
- **优先级排序**：标记关键发现供放射科医师立即审核。
- **标准化**：跨检查的一致性术语和结构化输出。
- **多模态**：CT、MRI 和 X 射线的统一分析管道。

---

## 系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                    MedVision AI CLI                           │
│  analyze  │  info  │  report  │  preprocess                  │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                 Diagnostic Engine（诊断引擎）                  │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌─────────┐ │
│  │ 加载     │→ │ 异常检测     │→ │ 报告生成 │→ │ 导出    │ │
│  │ DICOM    │  │              │  │          │  │ JSON    │ │
│  └──────────┘  └──────────────┘  └──────────┘  └─────────┘ │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                   核心模块                                    │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ DICOMLoader│  │ Detector     │  │ ReportGenerator      │ │
│  │            │  │              │  │                      │ │
│  │ - 解析     │  │ - 结节       │  │ - 结构化报告         │ │
│  │ - 元数据   │  │ - 肿块       │  │ - 临床印象           │ │
│  │ - 序列     │  │ - 骨折       │  │ - 建议               │ │
│  │ - 检查     │  │ - 积液       │  │ - JSON 导出          │ │
│  │            │  │ - 病变       │  │ - PDF 导出           │ │
│  └────────────┘  └──────────────┘  └──────────────────────┘ │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ PreprocessingPipeline（预处理管道）                    │   │
│  │ - HU 窗宽窗位（6 种预设）                              │   │
│  │ - 重采样与归一化                                      │   │
│  │ - 异常值去除                                          │   │
│  │ - 内存估算                                            │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## 核心功能

### 基础能力

| 功能 | 说明 |
|------|------|
| **DICOM 检查加载** | 解析 DICOM 目录、提取元数据、按序列组织 |
| **多模态支持** | CT、MRI（脑/脊柱/关节）、X 射线（胸部） |
| **异常检测** | 跨模态 13 种发现类型，含严重程度分级 |
| **结构化报告** | JSON + 人类可读文本报告，含临床印象 |
| **PDF 导出** | 通过 ReportLab 生成放射学报告 PDF |
| **CT 窗宽窗位** | 6 种标准窗宽窗位预设（肺窗、纵隔窗、骨窗、脑窗、腹窗、肝窗） |
| **预处理管道** | HU 提取、重采样、归一化、尺寸标准化 |
| **确定性结果** | 基于种子的可重现性，满足验证研究需求 |

### 各模态支持的发现类型

| 模态 | 支持的发现 |
|------|-----------|
| **CT** | 结节、肿块、钙化、病变、水肿、积液、出血、动脉瘤、肺不张、实变 |
| **MRI** | 病变、肿块、水肿、出血、狭窄 |
| **X 射线** | 结节、骨折、实变、积液、气胸、肺不张、钙化、肿块 |

### 严重程度分级

| 级别 | 说明 | 响应措施 |
|------|------|----------|
| **危急** | 危及生命，需立即处理 | 标记为 STAT 审核 |
| **高度** | 临床显著，可能需要干预 | 优先当日审核 |
| **中度** | 中等临床意义 | 常规审核 + 随访 |
| **低度** | 低度可疑，可能良性 | 记录备查 |
| **偶发** | 偶发发现，与主要指征无关 | 在报告中注明 |

---

## 快速开始

### 环境要求

- Python 3.10+
- pip

### 安装

```bash
git clone https://github.com/lanekingkong/github-big-proj12.git
cd github-big-proj12

pip install -e ".[all]"
```

### 首次分析

```bash
# 完整分析管道
medvision analyze /path/to/dicom/study --output report.json

# 检查信息
medvision info /path/to/dicom/study

# 从分析结果生成报告
medvision report analysis_result.json --format pdf --output report.pdf

# 预处理规划
medvision preprocess /path/to/dicom/study --window lung
```

### 示例输出

```
放射学报告
============================================================
患者 ID: P000123
模态: CT
检查日期: 2026-06-15
生成时间: 2026-06-28 14:30:00

发现 (2):
  [高度] 右上叶：右上叶疑似结节 (12.5mm) — 严重程度：高
  [中度] 左下叶：左下叶肺不张 — 严重程度：中

印象:
  发现 1 个高度显著发现。发现 1 个中度临床意义发现。

建议:
  1. 按 Fleischner 指南，3-6 个月后随访胸部 CT 评估结节稳定性。
  2. 结合病史、体格检查和实验室检查进行临床相关性评估。
============================================================
[AI 生成] ⚠ 待放射科医师审核
```

---

## 分析管道

### 1. DICOM 加载

```python
from medvision.core.engine import DiagnosticEngine

engine = DiagnosticEngine()
study = engine.load_study("/path/to/dicom/study")

print(f"患者: {study.patient_id}")
print(f"模态: {study.modality}")
print(f"序列数: {len(study.series)}")
print(f"总切片数: {study.total_slices}")
```

### 2. 异常检测

```python
result = engine.detect_anomalies(study)

print(f"发现数: {len(result.findings)}")
print(f"置信度: {result.confidence:.2%}")
print(f"处理时间: {result.processing_time_seconds:.2f}s")

for finding in result.findings:
    print(f"  [{finding.severity.value}] {finding.description}")
```

### 3. 报告生成

```python
report = engine.generate_report(study, result)
print(report.summary())

# 保存为 JSON
report.save("report.json")

# 导出为 PDF
report.export_pdf("report.pdf")
```

### 4. 预处理

```python
from medvision.core.preprocessor import (
    PreprocessingConfig,
    PreprocessingPipeline,
    WindowSettings,
    WindowPreset,
)

config = PreprocessingConfig(
    window=WindowSettings.preset(WindowPreset.LUNG),
)
pipeline = PreprocessingPipeline(config)

# 无需加载图像即可规划预处理
info = pipeline.process_metadata_only(slice_count=200, slice_thickness=1.0)
print(f"处理步骤: {len(info['steps'])}")

# 估算内存需求
mem = pipeline.estimate_memory(slice_count=300)
print(f"预计内存: {mem['total_estimated_mb']} MB")
```

---

## 窗宽窗位预设

CT 成像使用 Hounsfield Unit (HU) 表示组织密度。不同的窗宽窗位设置优化特定解剖结构的可视化：

| 预设 | 窗宽 (HU) | 窗位 (HU) | 最佳用途 |
|------|-----------|-----------|----------|
| **肺窗** | 1500 | -600 | 肺实质、结节、间质病变 |
| **纵隔窗** | 400 | 40 | 软组织、淋巴结、血管 |
| **骨窗** | 1800 | 400 | 骨折、骨病变、脊柱 |
| **脑窗** | 80 | 40 | 脑实质、灰白质 |
| **腹窗** | 400 | 40 | 腹腔脏器、游离液体 |
| **肝窗** | 150 | 30 | 肝实质、肝内病变 |

---

## CLI 参考

```bash
# 完整分析管道（加载 → 检测 → 报告）
medvision analyze <dicom_dir> [--output report.json]

# 显示 DICOM 检查信息
medvision info <dicom_dir>

# 从分析结果生成报告
medvision report <analysis.json> [--format pdf|text] [--output report.pdf]

# 预处理规划
medvision preprocess <dicom_dir> [--window lung|mediastinal|bone|brain|abdomen|liver]
```

### 常用选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--output` | 输出文件路径 | stdout |
| `--format` | 报告格式（pdf、text） | text |
| `--window` | CT 窗宽窗位预设 | mediastinal |
| `--seed` | 可重现性的随机种子 | 42 |

---

## 开发指南

### 项目结构

```
github_big_proj12/
├── src/
│   └── medvision/
│       ├── __init__.py          # 包导出
│       ├── cli.py               # CLI 入口（analyze/info/report/preprocess）
│       └── core/
│           ├── __init__.py      # 核心模块导出
│           ├── models.py        # DICOM 模型（Study, Series, Finding, Report）
│           ├── engine.py        # DiagnosticEngine — 完整管道编排器
│           ├── loader.py        # DICOMLoader — DICOM 检查解析
│           ├── detector.py      # AnomalyDetector — 多模型发现检测
│           ├── reporter.py      # ReportGenerator — 结构化报告创建
│           └── preprocessor.py  # PreprocessingPipeline — HU 窗宽窗位和归一化
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_core.py             # 单元和集成测试
├── pyproject.toml               # 项目元数据和依赖
├── LICENSE                      # MIT 许可证
├── .gitignore
├── README.md                    # 英文文档
└── README_CN.md                 # 中文文档
```

### 运行测试

```bash
pip install -e ".[dev]"
pytest tests/ -v
pytest tests/ -v --cov=medvision --cov-report=html
```

### 添加新的成像模态

1. 在 `models.py` 中将新模态添加到 `ImagingModality` 枚举
2. 在 `detector.py` 中将区域映射添加到 `_REGIONS` 字典
3. 在 `detector.py` 中将发现类型分布添加到 `_FINDING_DISTRIBUTIONS`
4. 为新模态添加测试用例
5. 更新文档

---

## 许可证

本项目基于 MIT 许可证发布。详见 [LICENSE](LICENSE)。

---

<p align="center">
  <strong>MedVision AI</strong> — <a href="https://github.com/lanekingkong">lanekingkong</a> 的 github-big-proj 生态系统项目
</p>

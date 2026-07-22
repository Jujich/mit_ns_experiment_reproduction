# Runbook: MIT Nuclear Modularity — воспроизведение и расширение

Операционное руководство по всей работе в репозитории: что сделано, как устроено, как прогнать, что ожидать, куда смотреть при сбоях.

| | |
|---|---|
| **Источник** | Lapp, C.W. (1989). *A Methodology for Modular Nuclear Power Plant Design and Construction*. MIT PhD |
| **Кейс** | Shearon Harris → Modular Shearon Harris II |
| **Стек** | Python 3.10+, `mit_ns/` + `scripts/` |
| **Заказчикский контекст** | Росатом |

---

## 1. Карта документов

| Документ | Когда читать |
|---|---|
| **Этот runbook** | Операции: setup, команды, приёмка, troubleshooting |
| [ROSATOM_RESULTS.md](ROSATOM_RESULTS.md) | Отчёт о результатах + детальная инструкция воспроизведения |
| [ROSATOM_BRIEF.md](ROSATOM_BRIEF.md) | Короткий бриф: сделано / next / не обещаем |
| [METRICS_AND_GLOSSARY.md](METRICS_AND_GLOSSARY.md) | Метрики, формулы, аббревиатуры, provenance, назначение файлов (§12) |
| [README.md](../README.md) | Краткое описание репозитория |

---

## 2. Что сделано (объём работ)

### 2.1. Было до расширения (коллега / initial commit)

- Оцифровка матрицы 25×25 (Fig. 6-1) и Tables 6-10…6-13
- Notebook `MIT_Nuclear_Benchmark_v7.ipynb`: BEA-style vs GA+LS / SA / Spectral по **inter-module cut**
- Исторический DV Modular SH II ≈ **$51.78M** (vs Original **$76.45M**, −32.3%)
- Reference: GA+LS улучшает cut на **~25–35%** vs BEA

### 2.2. Добавлено в расширении

| Блок | Суть |
|---|---|
| Пакет `mit_ns/` | Воспроизводимая библиотека вместо «только notebook» |
| Table 9-1 / экономика | Полный side-by-side DV + Ch.9 capital costs / savings ranges |
| DV-proxy | Оптимизация Design-Value-like метрики (суррогаты без pipe/layout) |
| Constraints | Soft-penalties nuclear vs secondary |
| Methodology navigator | Steps 1–12 + LLM context pack |
| PDF extract | Ускорение оцифровки таблиц |
| Docs | BRIEF / RESULTS / METRICS / этот RUNBOOK |

### 2.3. Что сознательно вне scope

- Полный автодизайн АЭС / CAD/BIM
- Точный PPRV по сырым pipe runs
- PWBS / завод модулей (Ch.7–8)
- Побитовая копия BEA-программы 1989

---

## 3. Архитектура потока

```text
PDF диссертации + оцифрованные CSV
        │
        ▼
┌───────────────────┐
│  mit_ns/data.py   │  загрузка матрицы, Table 9-x, constraints
│  validation.py    │  MEINT=1228, DV=$51.78M
└─────────┬─────────┘
          │
          ├─► objective.py (cut) ──► bea / ga_ls / sa / spectral
          │                              │
          │                              ▼
          │                     benchmark.py ──► outputs/benchmark_*.csv
          │
          ├─► dv_proxy.py ──► run_dv_proxy.py ──► outputs/dv_proxy_results.csv
          │
          ├─► economics.py ──► run_economics.py ──► outputs/economics_*.csv
          │
          ├─► constraints.py ──► run_constraints_demo.py
          │
          └─► methodology / pdf_extract ──► context pack / extractions
                                              │
                                              ▼
                                    make_dashboard.py ──► dashboard PNG
```

---

## 4. Быстрый старт (обязательный минимум)

```bash
cd mit_ns_experiment_reproduction

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# smoke (~1–2 мин)
python scripts/run_benchmark.py --quick
python scripts/run_dv_proxy.py --quick
python scripts/run_economics.py
MPLCONFIGDIR=.mplconfig python scripts/make_dashboard.py
```

**Приёмка smoke:** в логе есть `MEINT` / DV ≈ $51.78M; GA+LS лучше BEA по cut на всех K; файлы в `outputs/` обновились.

---

## 5. Полный операционный чеклист

Выполнять по порядку из корня репо при активном `.venv`.

### A. Валидация данных (без долгих оптимизаторов)

```bash
python -c "
from mit_ns.validation import run_all_validations
from mit_ns.data import load_table_9_1
print(run_all_validations())
print(load_table_9_1())
"
```

| Критерий | Ожидание |
|---|---|
| MEINT | `1228` |
| Modular SH II DV | `≈ 51.78` ($M) |
| Original DV (Table 9-1) | `≈ 76.45` ($M) |

### B. Cut-benchmark

```bash
# быстро
python scripts/run_benchmark.py --quick

# как в отчёте (дольше)
python scripts/run_benchmark.py --runs 30
```

| Выход | Назначение |
|---|---|
| `outputs/benchmark_results.csv` | best/mean/std cut по K×method |
| `outputs/optimizer_run_log.csv` | лог запусков |
| `outputs/best_assignments.json` | лучшие назначения система→модуль |

Reference (30 runs, notebook):

| K | BEA cut | GA+LS cut | Улучшение |
|---:|---:|---:|---:|
| 3 | 79 | 51 | 35.4% |
| 4 | 188 | 134 | 28.7% |
| 5 | 268 | 201 | 25.0% |
| 6 | 356 | 250 | 29.8% |

> При `--quick` best может быть хуже (например 55 вместо 51) — это нормально.

### C. DV-proxy

```bash
python scripts/run_dv_proxy.py --quick
# или: python scripts/run_dv_proxy.py --runs 10
```

| Выход | Назначение |
|---|---|
| `outputs/dv_proxy_results.csv` | BEA / cut_only / dv_proxy: cut + компоненты + DV |

**Интерпретация:** cut-only почти не двигает DV-proxy vs BEA; режим `dv_proxy` снижает DV-proxy, но может **увеличить** cut → cut ≠ Design Value.

### D. Экономика Ch.9

```bash
python scripts/run_economics.py
```

| Выход | Назначение |
|---|---|
| `outputs/economics_case1_grid.csv` | IDC-сетка Case 1 |
| `outputs/economics_case2_grid.csv` | IDC-сетка Case 2 |
| `outputs/economics_sensitivity_grid.csv` | объединение |
| `outputs/economics_vs_thesis.csv` | model vs thesis ranges |
| `outputs/economics_abstract_band.json` | коридор **26–46%** |

### E. Constraints + methodology + PDF

```bash
python scripts/run_constraints_demo.py
python scripts/methodology_navigator.py --list
python scripts/methodology_navigator.py --export-context
python scripts/methodology_navigator.py --step 3
# опционально (нужен pdftotext):
python scripts/extract_pdf_tables.py
```

### F. Дашборд

```bash
MPLCONFIGDIR=.mplconfig python scripts/make_dashboard.py
# → outputs/dashboard_benchmark.png
```

---

## 6. Скрипты: шпаргалка

| Команда | Отвечает за |
|---|---|
| `python scripts/run_benchmark.py [--quick\|--runs N]` | Cut-benchmark всех методов |
| `python scripts/run_dv_proxy.py [--quick\|--runs N]` | Cut-only vs DV-proxy |
| `python scripts/run_economics.py` | Экономика / AFUDC sensitivity |
| `python scripts/run_constraints_demo.py` | Mixing penalties nuclear/secondary |
| `python scripts/methodology_navigator.py --list\|--step N\|--export-context\|--ask "..."` | Навигатор методологии |
| `python scripts/extract_pdf_tables.py [--table …] [--llm]` | Extract таблиц из PDF |
| `python scripts/make_dashboard.py` | PNG-дашборд |

Опционально: исходный notebook коллеги

```bash
jupyter notebook MIT_Nuclear_Benchmark_v7.ipynb
```

---

## 7. Ключевые метрики (кратко)

| Метрика | Смысл | Где в коде |
|---|---|---|
| **inter-module cut** | Сумма связей между разными модулями | `mit_ns/objective.py` |
| **MEINT** | Контроль оцифровки матрицы (= 1228) | `mit_ns/validation.py` |
| **DV** | `535·MOM + 472·MAV + 1268·PPRV + 36·CVV + 196·MFV` | диссертация + `validation` / Table 9-1 |
| **DV_proxy** | То же с суррогатами MAV/CVV/MFV/PPRV для новых partition | `mit_ns/dv_proxy.py` |
| **savings%** | Экономия Total с IDC: срок × ставка × modular fraction | `mit_ns/economics.py` |

Полные формулы и словарь аббревиатур: [METRICS_AND_GLOSSARY.md](METRICS_AND_GLOSSARY.md).

---

## 8. Структура репозитория (расширение)

```text
mit_ns/          библиотека (алгоритмы, метрики, валидация)
scripts/         CLI entrypoints
data/            оцифровки Table 9-x, systems, systems
outputs/         результаты прогонов (CSV/JSON/PNG)
docs/            BRIEF, RESULTS, METRICS, RUNBOOK
requirements.txt зависимости
```

Назначение **каждого** файла расширения: [METRICS_AND_GLOSSARY.md §12](METRICS_AND_GLOSSARY.md#12-назначение-файлов-проекта-расширение-работы).

Исходные (до расширения): PDF, notebook, `input_matrix_figure_6_1.csv`, `dv_coefficients.csv`, `table_6_10…13_*.csv`.

---

## 9. Troubleshooting

| Симптом | Что сделать |
|---|---|
| `ModuleNotFoundError: mit_ns` | Запускать из корня репо; `source .venv/bin/activate` |
| `No module named deap / sklearn / …` | `pip install -r requirements.txt` |
| Matplotlib / fontconfig ошибки | `MPLCONFIGDIR=.mplconfig python scripts/make_dashboard.py` |
| `pdftotext` not found | Установить Poppler **или** пропустить `extract_pdf_tables.py` |
| GA+LS cut хуже, чем в README | Увеличить `--runs` (reference = 30); `--quick` занижает best |
| DV «не сходится» | Проверить, что CVV берётся `calculated_result` (Case 2), не printed; см. validation |
| Пустой / старый `outputs/` | Перегнать соответствующий `scripts/run_*.py` |
| Нужен LLM в навигаторе | `OPENAI_API_KEY=… python scripts/methodology_navigator.py --ask "..."`; без ключа работает offline |

---

## 10. Приёмка для передачи заказчику

- [ ] `run_all_validations()` → MEINT 1228, DV Modular ≈ $51.78M, Original ≈ $76.45M  
- [ ] `benchmark_results.csv`: GA+LS best < BEA на K=3…6  
- [ ] `dv_proxy_results.csv`: видна разница cut-only vs dv_proxy  
- [ ] `economics_abstract_band.json`: band [26, 46]  
- [ ] `dashboard_benchmark.png` актуален  
- [ ] В коммуникации разделены: (а) исторический redesign SH II, (б) улучшение cut GA+LS, (в) DV-proxy как отдельный эксперимент  

Формулировка для письма: [ROSATOM_RESULTS.md §11](ROSATOM_RESULTS.md#11-формулировка-для-письма--презентации).

---

## 11. Типичные сценарии использования

### «Просто перепроверить цифры отчёта»

```bash
source .venv/bin/activate
python scripts/run_benchmark.py --runs 30
python scripts/run_dv_proxy.py --runs 10
python scripts/run_economics.py
MPLCONFIGDIR=.mplconfig python scripts/make_dashboard.py
```

### «Показать инженеру методологию Ch.5»

```bash
python scripts/methodology_navigator.py --list
python scripts/methodology_navigator.py --step 8
python scripts/methodology_navigator.py --export-context
# затем открыть outputs/methodology_context_pack.json
```

### «Демо constraint-aware»

```bash
python scripts/run_constraints_demo.py
# смотреть outputs/constraint_aware_results.json
```

### «Только экономика 26–46%»

```bash
python scripts/run_economics.py
cat outputs/economics_abstract_band.json
```

---

## 12. Ограничения коммуникации (чеклист)

1. BEA-style ≈ идея BEA, не оригинальный бинарник 1989.  
2. −32% DV и −26…46% capital cost — из **диссертационного redesign**, не из GA+LS.  
3. DV-proxy использует **суррогаты**; без pipe/layout это не полный DV Lapp.  
4. Не обещать автодизайн АЭС — ИИ усиливает измеримые этапы (матрица, DV-proxy, constraints, экономика).

---

## 13. Следующие шаги (roadmap)

| Приоритет | Шаг | Нужны данные |
|---|---|---|
| Сделано | Cut-benchmark + DV-proxy + экономика + docs | открытая диссертация |
| Далее | Жёстче связать partition с инженерными constraints | правила Росатома |
| Пилот | Та же методика на матрице ВВЭР / СМР | P&ID / интерфейсы / DSM |
| Тяжёлое | Полный PPRV, PWBS, factory layout | pipe runs, production data |

Детали: [ROSATOM_BRIEF.md](ROSATOM_BRIEF.md).

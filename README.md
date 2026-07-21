# MIT Nuclear Modularity Benchmark Reproduction

Воспроизведение и расширение диссертации **Christopher W. Lapp (MIT, 1989)**  
*A Methodology for Modular Nuclear Power Plant Design and Construction* — кейс **Shearon Harris**.

## Сопроводительное описание

### Что сделано изначально (матричный benchmark)

Исходная работа 1989 группировала системы в модули эвристикой **BEA (Bond Energy Algorithm)**. Мы восстановили матрицу взаимодействий **25×25** и сравнили:

- **BEA-style greedy baseline**
- **GA+LS** — генетический алгоритм + локальный поиск
- **SA** — simulated annealing
- **Spectral / Louvain** — графовые baseline

Целевая функция исходного benchmark: **минимизация межмодульных связей (inter-module cut)**.

| Количество модулей | BEA-style | GA+LS | Улучшение |
|---:|---:|---:|---:|
| 3 | 79 | 51 | 35.4% |
| 4 | 188 | 134 | 28.7% |
| 5 | 268 | 201 | 25.0% |
| 6 | 356 | 250 | 29.8% |

> Это улучшение относится к **матричному разбиению**, а не к полному автодизайну АЭС.

### Исторический Design Value (диссертация)

| Вариант | Design Value |
|---|---:|
| Original Plant (thesis headline) | $76.45M |
| Modular SH II | $51.78M |
| Снижение | 32.3% |

Компоненты Table 9-1 (Original vs SH II) оцифрованы в [`data/table_9_1_dv_comparison.csv`](data/table_9_1_dv_comparison.csv).

---

## Расширения с ИИ (после исходного benchmark)

| Модуль | Что делает | Как запустить |
|---|---|---|
| Cut benchmark | воспроизводимый пакет BEA/GA/SA/Spectral/Louvain | `python scripts/run_benchmark.py` |
| DV-proxy | GA минимизирует прокси Design Value, сравнение с cut-only | `python scripts/run_dv_proxy.py` |
| Экономика Ch.9 | AFUDC sensitivity, коридор 26–46% | `python scripts/run_economics.py` |
| Methodology navigator | Steps 1–12 + LLM context pack | `python scripts/methodology_navigator.py --list` |
| PDF extract | pdftotext (+ optional LLM) | `python scripts/extract_pdf_tables.py` |

Документы для заказчика:
- бриф / следующие шаги: [`docs/ROSATOM_BRIEF.md`](docs/ROSATOM_BRIEF.md)
- отчёт о результатах воспроизведения: [`docs/ROSATOM_RESULTS.md`](docs/ROSATOM_RESULTS.md)
- метрики, ход работ и словарь аббревиатур: [`docs/METRICS_AND_GLOSSARY.md`](docs/METRICS_AND_GLOSSARY.md)

### DV-proxy (главный следующий эксперимент)

Полный пересчёт PPRV/MAV/CVV/MFV для произвольного partition требует pipe/layout данных, которых нет в открытой диссертации. Поэтому:

- **MOM** = inter-module cut (из матрицы);
- **MAV / CVV / MFV / PPRV** — суррогаты по формулам + статистике размеров модулей;
- **DV_proxy = 535·MOM + 472·MAV̂ + 1268·PPRV̂ + 36·CVV̂ + 196·MFV̂**.

Это позволяет честно ответить: *улучшает ли оптимизатор не только cut, но и Design-Value-like метрику?*

### Экономика

Оцифрованы капитальные стоимости Case 1/2 (Tables 9-8a,b) и тезисные диапазоны savings (Ch.9.6.3). Модель IDC с равномерным расходованием средств строит сетку срок × ставка × доля modular schedule (50/65/80%).

---

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# быстрый smoke
python scripts/run_benchmark.py --quick
python scripts/run_dv_proxy.py --quick
python scripts/run_economics.py
python scripts/methodology_navigator.py --export-context
python scripts/extract_pdf_tables.py
```

Полный benchmark (30 прогонов): `python scripts/run_benchmark.py --runs 30`.

Результаты пишутся в [`outputs/`](outputs/) (`benchmark_results.csv`, `dv_proxy_results.csv`, `dashboard_benchmark.png`, экономика, constraints, methodology context).

Таблица GA+LS в начале README — из исходного notebook (30 runs). Регенерация в `outputs/` может слегка отличаться при меньшем `--runs`.

---

## Структура репозитория

```
mit_ns/                 # библиотека алгоритмов и метрик
scripts/                # CLI entrypoints
data/                   # Table 9-1/9-2, constraints, systems, economics
docs/ROSATOM_BRIEF.md   # краткий бриф
MIT_Nuclear_Benchmark_v7.ipynb  # исходный notebook коллеги
*.csv (корень)          # исходные оцифровки Fig/Tables 6.x
22549470-MIT.pdf        # диссертация
```

---

## Ограничения

- BEA-style — приближение идеи, не бит-в-бит код 1989.
- CVV: в диссертации printed vs calculated расходятся; используется calculated.
- PPRV без pipe-данных не восстанавливается точно (суррогат / историческое значение).
- Исторические −32% DV и −26…46% capital cost — результат redesign SH II в диссертации, не выход GA+LS.

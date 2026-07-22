# Отчёт о результатах воспроизведения эксперимента

**Источник:** Christopher W. Lapp, *A Methodology for Modular Nuclear Power Plant Design and Construction*, MIT, 1989  
**Объект кейса:** АЭС Shearon Harris (модульный redesign — Shearon Harris II)  
**Заказчик контекста:** Росатом  
**Формат работы:** воспроизведение вычислительных этапов диссертации + сравнение с современными методами оптимизации / ИИ

Сопутствующие документы:

- краткий бриф (следующие шаги): [ROSATOM_BRIEF.md](ROSATOM_BRIEF.md)
- метрики, ход работ и словарь аббревиатур: [METRICS_AND_GLOSSARY.md](METRICS_AND_GLOSSARY.md)
- общий runbook: [RUNBOOK.md](RUNBOOK.md)
- инструкция по воспроизведению: [§9 в этом файле](#9-инструкция-по-воспроизведению)

---

## 1. Цель воспроизведения

Проверить, можно ли **воспроизвести и усилить** ключевой вычислительный этап методологии MIT 1989 — разбиение систем АЭС на модули по матрице взаимодействий — с помощью современных алгоритмов, и связать результат с метриками **Design Value** и экономикой строительства из той же диссертации.

**Что именно воспроизводилось**


| Этап диссертации                   | Что сделано                                              |
| ---------------------------------- | -------------------------------------------------------- |
| Матрица связей систем (Fig. 6-1)   | Оцифрована матрица 25×25                                 |
| BEA / группировка модулей          | Реализован BEA-style baseline + современные оптимизаторы |
| Design Value (формула + Table 9-1) | Валидированы компоненты Original vs Modular SH II        |
| Экономика Ch.9 (AFUDC / schedule)  | Воспроизведена чувствительность и коридор savings 26–46% |


**Что сознательно не воспроизводилось end-to-end:** полный 3D-layout, pipe routing (PPRV по сырым трассам), PWBS/завод модулей (Ch.7–8), автодизайн АЭС без инженера.

---

## 2. Историческая валидация Design Value

По оцифрованной Table 9-1 и коэффициентам диссертации:

```text
DV = 535·MOM + 472·MAV + 1268·PPRV + 36·CVV + 196·MFV
```

### 2.1. Компоненты Original vs Modular SH II


| Компонент | Shearon Harris | Shearon Harris II | SH II / SH |
| --------- | -------------- | ----------------- | ---------- |
| MOM       | 2112           | 1180              | 56%        |
| MAV       | 4236           | 2895              | 68%        |
| PPRV      | 5901           | 2773              | 54%        |
| CVV       | 1 801 000      | 1 266 483         | 70%        |
| MFV       | 5102           | 3444              | 67%        |


### 2.2. Итоговый Design Value


| Вариант        | Design Value | Изменение  |
| -------------- | ------------ | ---------- |
| Original Plant | **$76.45M**  | —          |
| Modular SH II  | **$51.78M**  | **−32.3%** |


Вывод: численные результаты диссертационного redesign **воспроизводятся** из оцифрованных таблиц с точностью до заявленных headline-значений.

> Важно: снижение DV на 32.3% — результат **экспертного redesign SH II в диссертации**, а не выход современного оптимизатора.

---

## 3. Основной эксперимент: разбиение матрицы 25×25

### 3.1. Постановка

- Вход: симметричная матрица взаимодействий 25 систем (MEINT = 1228).
- Задача: разбить системы на `K ∈ {3,4,5,6}` модулей.
- Целевая функция: минимизация **inter-module cut** (сумма связей между разными модулями).
- Ограничения размера модуля: `min_size = 2`, `max_size = max(5, 25/K + 3)`.

### 3.2. Методы


| Метод              | Роль                                    |
| ------------------ | --------------------------------------- |
| BEA-style          | Baseline, приближение эвристики 1989    |
| GA+LS              | Генетический алгоритм + локальный поиск |
| SA                 | Simulated annealing                     |
| Spectral / Louvain | Графовые ML/community baselines         |


### 3.3. Результаты (reference run, notebook / 30 запусков)


| K   | BEA-style cut | GA+LS cut | Улучшение GA+LS vs BEA |
| --- | ------------- | --------- | ---------------------- |
| 3   | 79            | 51        | **35.4%**              |
| 4   | 188           | 134       | **28.7%**              |
| 5   | 268           | 201       | **25.0%**              |
| 6   | 356           | 250       | **29.8%**              |


**Вывод:** на матричном этапе методологии 1989 современные оптимизаторы стабильно превосходят BEA-эвристику. Снижение межмодульных связей составляет **примерно 25–35%**.

Графовые baselines (Spectral / Louvain) на этой задаче **не превосходят** BEA по cut; лучший результат даёт именно оптимизация (GA+LS, частично SA).

---

## 4. Расширение: DV-proxy (cut ≠ Design Value)

Чтобы ответить на вопрос «улучшает ли оптимизация не только cut, но и Design Value?», введён прокси-критерий:

- **MOM** считается напрямую из partition (как cut);
- **MAV / CVV / MFV / PPRV** — суррогаты (полных pipe/layout данных в открытой диссертации нет).

### 4.1. Сводка (регенерированный прогон)


| K   | Режим             | Cut | DV-proxy   |
| --- | ----------------- | --- | ---------- |
| 3   | BEA-style         | 79  | 53.41M     |
| 3   | cut-only (GA)     | 55  | 53.36M     |
| 3   | **dv-proxy (GA)** | 164 | **50.60M** |
| 4   | cut-only          | 134 | 55.17M     |
| 4   | **dv-proxy**      | 289 | **52.35M** |
| 5   | cut-only          | 210 | 57.21M     |
| 5   | **dv-proxy**      | 582 | **53.73M** |
| 6   | cut-only          | 253 | 58.80M     |
| 6   | **dv-proxy**      | 441 | **55.66M** |


### 4.2. Интерпретация для Росатома

1. Оптимизация только по cut **почти не меняет** DV-proxy относительно BEA (разница доли процента).
2. Прямая минимизация DV-proxy **снижает** прокси-стоимость, но может **увеличить** cut.
3. Практический смысл: **межмодульный разрез — необходимый, но недостаточный критерий**. Для проектной ценности нужны Design Value и инженерные ограничения вместе.

Это главный методологический результат расширения относительно исходного benchmark коллеги.

---

## 5. Экономика строительства (Chapter 9)

Воспроизведены капитальные стоимости кейсов диссертации и чувствительность к сроку / ставке процента.


| Кейс   | Conventional                  | Modular                  | База сравнения               |
| ------ | ----------------------------- | ------------------------ | ---------------------------- |
| Case 1 | SH conventional **197.2M**    | SH II modular **135.7M** | дизайн + метод строительства |
| Case 2 | SH II conventional **143.6M** | SH II modular **135.7M** | только метод строительства   |


### 5.1. Тезисные средние savings (Ch.9.6.3)


| Кейс   | Срок conventional | Средняя экономия (диссертация) |
| ------ | ----------------- | ------------------------------ |
| Case 1 | 7 лет             | **~46%**                       |
| Case 2 | 7 лет             | **~26%**                       |


Именно этот коридор даёт заявленные в abstract **26–46%** потенциальной экономии капитальных затрат при модульном подходе.

### 5.2. Что это значит

- Основной экономический рычаг в диссертации — **сжатие графика строительства** и снижение AFUDC (проценты на капитал в период строительства), плюс эффект redesign.
- Case 2 показывает: даже при **одинаковом** дизайне SH II модульное строительство даёт заметный, но меньший выигрыш, чем redesign+modular вместе (Case 1).

---

## 6. ИИ-сопровождение методологии (дополнительный слой)

Помимо численных экспериментов подготовлен прикладной контур:

- **навигатор по 12 шагам** проектирования (Ch.5) с checklist и статусом воспроизведения;
- **constraint-aware** разбиение (nuclear / secondary, safety tags);
- извлечение таблиц из PDF для ускорения оцифровки.

Назначение: показать Росатому модель **«ИИ как помощник инженера»**, а не замену проектной организации.

---

## 7. Итоговые выводы

1. **Воспроизведение успешно:** матрица, Design Value Modular SH II (51.78M) и компоненты Table 9-1 подтверждены численно.
2. **Современная оптимизация лучше BEA 1989** на этапе модульного разбиения матрицы: **−25…35%** inter-module cut.
3. **Cut ≠ полная проектная ценность:** DV-proxy показывает, что минимизация только связей между модулями не гарантирует лучший Design Value.
4. **Экономический narrative диссертации** (26–46% при модульности + сжатии срока) воспроизведён как отдельный, валидируемый блок.
5. **Готовый следующий шаг для пилота:** перенос того же benchmark на матрицу связей российского объекта (ВВЭР / СМР) при предоставлении P&ID / интерфейсных данных.

---

## 8. Ограничения (для корректной коммуникации)

- BEA-style в коде — **воспроизведение идеи**, не побитовая копия программы Lapp 1989.
- Без pipe/layout данных полный пересчёт PPRV/MAV/CVV для произвольного partition невозможен; используются суррогаты.
- Исторические −32% DV и −26…46% capital cost **не являются** результатом GA+LS.
- Работа не заменяет нормативную / safety-верификацию и CAD/BIM-проектирование АЭС.

---

## 9. Инструкция по воспроизведению

Ниже — как заново прогнать расширение работы (пакет `mit_ns/`, скрипты, артефакты в `outputs/`) на чистом окружении. Исходный notebook коллеги (`MIT_Nuclear_Benchmark_v7.ipynb`) при этом **не обязателен**: вся логика вынесена в Python-модули.

### 9.1. Требования

- Python 3.10+ (проверено на 3.12)
- `pdftotext` (Poppler) — только для `scripts/extract_pdf_tables.py`; остальное работает без него
- ОС: macOS / Linux (команды ниже для bash/zsh)

### 9.2. Установка

Из корня репозитория:

```bash
cd mit_ns_experiment_reproduction

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Зависимости: `numpy`, `pandas`, `matplotlib`, `seaborn`, `scikit-learn`, `deap`, `networkx` (см. `[requirements.txt](../requirements.txt)`).

### 9.3. Быстрая проверка (smoke, ~1–2 мин)

```bash
# 1) Исторический DV + cut-benchmark (мало прогонов)
python scripts/run_benchmark.py --quick

# 2) Сравнение cut-only vs DV-proxy
python scripts/run_dv_proxy.py --quick

# 3) Экономика Ch.9 (IDC / savings)
python scripts/run_economics.py

# 4) Constraint-aware демо
python scripts/run_constraints_demo.py

# 5) Словарь методологии + LLM context pack
python scripts/methodology_navigator.py --list
python scripts/methodology_navigator.py --export-context

# 6) Дашборд по уже лежащим CSV в outputs/
MPLCONFIGDIR=.mplconfig python scripts/make_dashboard.py
```

Ожидаемое поведение smoke:

- валидация печатает `MEINT = 1228`, Modular SH II DV ≈ **$51.78M**;
- GA+LS на всех K лучше BEA-style по cut (точные числа при `--quick` могут отличаться от reference 30-run);
- в `outputs/` появляются/обновляются CSV/JSON/PNG.

### 9.4. Полное воспроизведение (как в отчёте)

```bash
# Cut-benchmark: 30 стохастических прогонов на метод (как в notebook)
python scripts/run_benchmark.py --runs 30

# DV-proxy: больше прогонов → стабильнее best
python scripts/run_dv_proxy.py --runs 10

python scripts/run_economics.py
python scripts/run_constraints_demo.py
python scripts/methodology_navigator.py --export-context
python scripts/extract_pdf_tables.py          # нужен pdftotext

MPLCONFIGDIR=.mplconfig python scripts/make_dashboard.py
```


| Скрипт                             | Что воспроизводит                                         | Главный выход                                                                     |
| ---------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `scripts/run_benchmark.py`         | BEA / Spectral / Louvain / GA+LS / SA по inter-module cut | `outputs/benchmark_results.csv`, `optimizer_run_log.csv`, `best_assignments.json` |
| `scripts/run_dv_proxy.py`          | cut-only GA vs DV-proxy GA vs BEA                         | `outputs/dv_proxy_results.csv`                                                    |
| `scripts/run_economics.py`         | IDC-сетка + сверка с Ch.9.6.3 (26–46%)                    | `outputs/economics_*.csv`, `economics_abstract_band.json`                         |
| `scripts/run_constraints_demo.py`  | nuclear/secondary mixing penalties                        | `outputs/constraint_aware_results.json`                                           |
| `scripts/methodology_navigator.py` | Steps 1–12 + context pack                                 | `outputs/methodology_context_pack.json`                                           |
| `scripts/extract_pdf_tables.py`    | извлечение Table 9-1/9-2/6-2 из PDF                       | `outputs/pdf_extractions.json`                                                    |
| `scripts/make_dashboard.py`        | сводный график                                            | `outputs/dashboard_benchmark.png`                                                 |


### 9.5. Только валидация исторических цифр (без оптимизаторов)

```bash
python -c "
from mit_ns.validation import run_all_validations
from mit_ns.data import load_table_9_1
print(run_all_validations())
print(load_table_9_1())
"
```

Ожидание: `dv_modular_sh2_musd ≈ 51.78`, `dv_original_from_table_9_1_musd ≈ 76.45`, `meint_undirected = 1228`.

### 9.6. Исходный notebook (опционально)

```bash
jupyter notebook MIT_Nuclear_Benchmark_v7.ipynb
# или: jupyter lab
```

Notebook — исходная реализация (cut-benchmark + исторический DV). Пакет `mit_ns/` покрывает тот же контур и расширения (DV-proxy, экономика, constraints).

### 9.7. Что сверить с этим отчётом


| Утверждение в отчёте                | Где проверить после прогона                                                                                                   |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| DV Modular SH II = $51.78M (−32.3%) | вывод `run_benchmark.py` / `run_all_validations()`; `[data/table_9_1_dv_comparison.csv](../data/table_9_1_dv_comparison.csv)` |
| GA+LS лучше BEA на ~25–35% cut      | `outputs/benchmark_results.csv` (колонки `best` для BEA-style и GA+LS)                                                        |
| DV-proxy ≠ cut-only                 | `outputs/dv_proxy_results.csv`                                                                                                |
| Коридор savings 26–46%              | `outputs/economics_abstract_band.json`, `economics_vs_thesis.csv`                                                             |
| Дашборд                             | `outputs/dashboard_benchmark.png`                                                                                             |


### 9.8. Замечания по воспроизводимости

1. **Стохастика:** GA+LS / SA зависят от seed; при `--runs 30` best обычно близок к таблице §3.3, при `--quick` best может быть хуже (например cut=55 вместо 51 для K=3).
2. **Время:** полный `--runs 30` занимает порядка минут–десятков минут (CPU); `--quick` — для CI/smoke.
3. **Matplotlib:** если нет прав на `~/.matplotlib`, задайте `MPLCONFIGDIR=.mplconfig` (как в командах выше).
4. **Детали метрик и provenance файлов:** `[METRICS_AND_GLOSSARY.md](METRICS_AND_GLOSSARY.md)`.

---

## 10. Материалы


| Материал                      | Путь                                                                          |
| ----------------------------- | ----------------------------------------------------------------------------- |
| Краткий бриф / следующие шаги | `[docs/ROSATOM_BRIEF.md](ROSATOM_BRIEF.md)`                                   |
| Метрики и словарь аббревиатур | `[docs/METRICS_AND_GLOSSARY.md](METRICS_AND_GLOSSARY.md)`                     |
| Техническое README            | `[README.md](../README.md)`                                                   |
| Сводка cut-benchmark          | `[outputs/benchmark_results.csv](../outputs/benchmark_results.csv)`           |
| DV-proxy сравнение            | `[outputs/dv_proxy_results.csv](../outputs/dv_proxy_results.csv)`             |
| Table 9-1 side-by-side        | `[outputs/table_9_1_side_by_side.csv](../outputs/table_9_1_side_by_side.csv)` |
| Экономика vs thesis           | `[outputs/economics_vs_thesis.csv](../outputs/economics_vs_thesis.csv)`       |
| Дашборд                       | `[outputs/dashboard_benchmark.png](../outputs/dashboard_benchmark.png)`       |
| Исходная диссертация          | `[22549470-MIT.pdf](../22549470-MIT.pdf)`                                     |


---

## 11. Формулировка для письма / презентации

> По диссертации MIT (Lapp, 1989) мы воспроизвели матричный этап модульного проектирования Shearon Harris и подтвердили исторический Design Value Modular SH II ($51.78M, −32.3% к original). Современный оптимизатор GA+LS снижает межмодульные связи на 25–35% относительно BEA-эвристики 1989 года. Дополнительно показано, что оптимизация только по cut не эквивалентна улучшению Design Value, а экономический коридор модульности 26–46% из главы 9 воспроизводится как отдельный чувствительный анализ. Следующий практический шаг — перенос методики на данные российского объекта.


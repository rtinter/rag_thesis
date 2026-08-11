# Retrieval-Augmented Generation im Hochschulkontext: <br>Architektur und Evaluation eines On-Premise-Systems für Lehrmaterialien

Repository zur gleichnamigen Bachelorthesis. Das Mono-Repository ist zweigeteilt:

- **[notebooks/](notebooks/)** — die Jupyter-Notebooks, in denen die Experimente und die
  abschließende Evaluation der Thesis iterativ entstanden sind.
- **[backend/](backend/) + [frontend/](frontend/)** — der Prototyp einer RAG-Applikation mit
  Hybridsearch und Reranking.

<br>

## Inhalt

| Abschnitt | Inhalt |
|---|---|
| [Funktionen der Applikation](#funktionen-der-applikation) | Was das System tut |
| [Systemumgebung](#systemumgebung) | Modelle, Dienste und [Ressourcen](#ressourcen) |
| [Welcher Setup-Pfad ist der Richtige?](#welcher-setup-pfad-ist-der-richtige) | Weiche zwischen den drei Wegen |
| [Schnellstart — Abgabe-Paket](#schnellstart--abgabe-paket) | Starten, wenn Daten und Zugang beiliegen |
| [Setup mit eigenen Daten](#setup-mit-eigenen-daten) | Vom frischen Clone zur befüllten Wissensbasis |
| [API](#api) | Endpunkte und Antwortformat |
| [Troubleshooting](#troubleshooting) | Häufige Fehlerbilder und ihre Ursache |
| [Start ohne Docker](#start-ohne-docker-für-die-entwicklung) | Hot-Reload, und auf macOS der einzige GPU-Weg |
| [Notebooks & Evaluation](#notebooks--evaluation) | Experimente und Kennzahlen der Thesis |

<br>

## Funktionen der Applikation
Vorlesungsfolien werden geparst und in Qdrant indexiert. Die Applikation beantwortet Fragen auf <br>
Grundlage dieser Wissensbasis und belegt jede Aussage mit einer Quelle. Die referenzierten <br>
Quellfolien können rechts neben dem Chat angezeigt werden. 

<br>

## Systemumgebung

Das System ist **hybrid** ausgelegt: ressourcenarme Komponenten 
werden lokal betrieben, die großen
generativen Modelle werden über das Gateway der HAW-Kiel angesprochen.

| Komponente | Modell / Dienst | Ort |
|---|---|---|
| Dense-Embeddings | `BAAI/bge-m3` | lokal (GPU oder CPU) |
| Sparse-Embeddings | `Qdrant/bm25` | lokal |
| Reranking | `BAAI/bge-reranker-v2-m3` | lokal (GPU oder CPU) |
| Vektor-Datenbank | `Qdrant v1.17.1` | lokal (Container) |
| Antwortgenerierung | `openai/gpt-oss-120b` | Gateway der Hochschule |
| Folien-Parsing (VLM) | `Qwen/Qwen3.5-122B-A10B-GPTQ-Int4` | Gateway der Hochschule |

### Ressourcen

- **RAM: 16 GB Minimum**, 32 GB komfortabel.
- **GPU: optional**, ab ca. 4 GB VRAM sinnvoll. Ohne GPU funktioniert alles, das Reranking von
  `top_k` Kandidaten ist auf der CPU jedoch der mit Abstand teuerste Schritt. Die
  CPU-Variante ist deshalb bereits auf `top_k=25` voreingestellt und spiegelt so nicht die volle Leistung 
  des Systems wider. Der Wert kann auch für die CPU-Variante erhöht werden. Siehe
  [Reranking-Tiefe anpassen](#3-reranking-tiefe-anpassen-optional).

Getestet wurde auf **Windows 11** mit einer GeForce RTX 3070 Ti (8 GB VRAM), 32 GB RAM und einem
Intel i5-12600KF sowie auf einem **MacBook mit Apple-Silicon (M1)**.

<br>

> ## Welcher Setup-Pfad ist der Richtige?
>
> **Das Abgabe-Paket der Thesis ist vorhanden** (Vorlesungsdaten, Vektordatenbank-Speicher
> und Gateway-API Key liegen bei)
> Dann muss nichts geparst oder indexiert werden.
> -> **[Schnellstart — Abgabe-Paket](#schnellstart--abgabe-paket)**, direkt im nächsten Abschnitt.
>
> **Keine Daten vorhanden** Dann fehlen Daten für die Wissensbasis und Zugangsdaten zum Gateway
> -> **[Setup mit eigenen Daten](#setup-mit-eigenen-daten)**
>
> **Nicht die Applikation, sondern die Evaluation der Thesis nachvollziehen**
> -> **[Notebooks & Evaluation](#notebooks--evaluation)**

<br>
<br>

---

<br>
<br>

## Schnellstart — Abgabe-Paket

Dieser Abschnitt genügt vollständig, um das System zu starten. 

**Voraussetzung:** 
- Docker mit Compose. Alle anderen Dependencies werden automatisch in die Container geladen.
- Zugang zum Netz der HAW Kiel (Vor Ort oder mittels VPN)

Der Prototyp kann so mittels CPU verwendet werden. 
Für die GPU-Variante (`docker-compose-gpu.yml`) kommt je nach
Betriebssystem hinzu:

| ||
|---|---|
| **Windows** | ein aktueller NVIDIA-Treiber |
| **Linux** | NVIDIA-Treiber und [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) |

<br>

### 1. Folgende Daten sollten bereits im Repository liegen

```
rag_thesis_app/
|
|-- backend/
│   └-- .env                  <- liegt bei (Gateway-URL und API-Key bereits eingetragen)
|
|-- data/                     
|   ├-- parsed_clean/         <- liegt bei (Parsingergebnisse in Json-Format)
│   └-- reference_slides/     <- liegt bei (Einzelne Folienbilder in PNG-Format)
|-- qdrant_storage/           <- liegt bei (Indexierte Chunks für Vorlesungsfolien und Notebooks)
|
|-- .env                      <- liegt bei (Gateway-URL und API-Key bereits eingetragen)
```


<br>
<br>


> ⚠️ **Das VPN blockiert das Herunterladen von Paketen.**
>
> Bei aktiver VPN-Verbindung schlagen die Downloads einiger Bibliotheken fehl.
> **Deshalb die Reihenfolge einhalten:**
>
> 1. VPN **trennen**
> 2. `docker compose up --build` vollständig durchlaufen lassen. Dabei werden Images,
>    Bibliotheken und Modelle geladen
> 3. VPN **verbinden**, sobald alles geladen ist
>
> Ab dem zweiten Start entfällt das: Es wird nichts mehr heruntergeladen, das VPN kann
> durchgehend verbunden bleiben.

<br>
<br>

### 2. Starten

```bash
docker compose up --build                            # ohne NVIDIA-GPU (Standard)
docker compose -f docker-compose-gpu.yml up --build  # mit NVIDIA-GPU (deutlich schneller)
```

Beide Varianten bauen dasselbe Backend, installieren aber unterschiedliche PyTorch-Builds. Das
kostet vor allem beim **ersten** Bauen sehr unterschiedlich viel Zeit:

| | Torch | Image | Bauen (1. Mal) (Sehr Netzwerkabhängig! Reiner Richtwert)| `resolve_device()` |
|---|---|---|---|---|
| `docker-compose.yml` | CPU | 2,25 GB | **ca. 2 Min.** | `cpu` |
| `docker-compose-gpu.yml` | CUDA 12.8 | 12,2 GB | **ca. 20 Min.** | `cuda` |

<br>
<br>

Das Frontend ist anschließend im Browser erreichbar: **<http://localhost:8501>**

<br>
<br>

**Der Modell-Download läd zusätzlich.** Beim ersten Start lädt das Backend `bge-m3` und
`bge-reranker-v2-m3` in das Volume `hf_cache` — rund **6,9 GB**, in beiden Varianten identisch.
Im Log erscheint `Loading RAG models on device: ...`. Ab dem zweiten Start entfallen Bauen und
Download, der Start dauert dann nur noch Sekunden.

<br>
<br>

---

<br>
<br>

### 3. Reranking-Tiefe anpassen (optional)

`top_k` bestimmt, wie viele Chunks an den Cross-Encoder weitergereicht werden. Der Aufwand des
Rerankings wächst linear. Beide Compose-Dateien setzen den Wert deshalb passend zur
Hardware:

| Datei | `top_k` |
|---|---|
| `docker-compose.yml` (CPU) | 25 |
| `docker-compose-gpu.yml` (GPU) | 100 |

Geändert wird dieser Wert im `environment:`-Block der jeweiligen Compose-Datei:

```yaml
    environment:
      - top_k=25        # <-- hier
```

Für die CPU-Variante direkt: [top_k in docker-compose.yml anpassen](docker-compose.yml)

> **Die Ergebnisse der Thesis wurden mit `top_k=100` unter GPU-Beschleunigung erzeugt.**

Der Wert 25 ist dient einem schnelleren Testen der Anwedung. Er liefert
schlechtere Ergebnisse und dient allein dem Ausprobieren auf einer CPU.

**Womit zu rechnen ist:** Auf der CPU dauert eine Antwort bei `top_k=25` etwa 30 Sekunden, bei
`top_k=100` rund drei Minuten. Auf der GPU sind es wenige Sekunden. 
Eine scheinbar hängende Oberfläche ist auf der CPU also normal
und kein Fehler.

**Nach einer Änderung genügt ein Neustart des Containers. Kein Neubau nötig:**

```bash
docker compose up backend                            # CPU
docker compose -f docker-compose-gpu.yml up backend  # GPU
```

<br>
<br>


Bei Problemen: [Troubleshooting](#troubleshooting). 

Das System ohne Docker zu starten, ist
ebenfalls möglich ([Start ohne Docker](#start-ohne-docker-für-die-entwicklung)).


> **Auf macOS ohne Docker starten, wenn die GPU genutzt werden soll.**
> Apples GPU-Backend **MPS funktioniert in keinem Container**
> ([Start ohne Docker](#start-ohne-docker-für-die-entwicklung)). Im Log steht dann `device: mps`.


<br>
<br>

---

<br>
<br>

## Setup mit eigenen Daten

Dieser Teil beschreibt den Weg vom frisch geklonten Repository zum lauffähigen System.

Ein frischer Clone bringt die Verzeichnisstruktur mit, aber **keine Vorlesungsdaten, keine
Chunks und keine befüllte Vektor-Datenbank**. Das System startet ohne diese Komponenten nicht
sinnvoll.


### 1. Konfiguration

Das Backend liest seine Einstellungen über pydantic-settings aus Umgebungsvariablen bzw. einer
`.env` ([config.py](backend/app/core/config.py)).

`gateway_url` und `bearer_token` sind **Pflicht**. Ohne sie wirft pydantic-settings schon beim
Start einen Validierungsfehler. 

Um die Experimente zu wiederholen, muss eine .env im Root erstellt und diese dort eingetragen werden.
Siehe ([.env.example](.env.example)).

Um die Applikation zu verwenden, muss eine .env im Backend erstellt werden.
Siehe ([.env.example](./backend/.env.example)).

```
rag_thesis_app/
|-- backend/
│   └-- .env                  <- nötig um den Prototypen zu Verwenden
|-- .env                      <- Nötig um die Evaluationen zu wiederholen
```

### 2. Wissensbasis herstellen

Ausgangspunkt sind PDFs. Sie werden Seite für Seite als PNG gerendert, in `data/reference_slides` persistiert und vom VLM in strukturierte
Chunks übersetzt.
Ziel des Blocks: **Qdrant läuft und die Collection `lecture_chunks` ist befüllt.**

<br>

**2.1 PDFs ablegen**

Alle PDFs müssen im folgenden Ordner abgelegt werden:

```
data/raw/pdfs/<vorlesung>.pdf
```

Der Dateiname ohne Endung wird zum `lecture`-Feld der Chunks und zum Ordnernamen unter
`reference_slides/`.

<br>

**2.2 Parsen**

Das Parsingscript liegt in `backend/scripts/parse.py`. Um es zu verwenden müssen alle Dependencies
mittels uv installiert werden: 

```bash
cd backend
uv sync --extra cpu     # CPU-Build von PyTorch, deutlich kleiner
uv sync --extra gpu     # CUDA 12.8 (Windows/Linux mit NVIDIA-Karte)
```

Das Extra entscheidet, worauf das Embedding-Modell im Ingest (Schritt 2.4) rechnet. `gpu` ist
deutlich schneller, bedarf aber ein deutlich größeres Torch-Build und muss entsprechend beim ersten mal lange laden. 

Anschließend können die PDFs über das VLM geparst werden. Die Argumente entscheiden,
ob alle PDFs oder nur ein einzelnes für Testzwecke überführt werden soll:

```bash
uv run python -m scripts.parse            # alle PDFs in data/raw/pdfs
uv run python -m scripts.parse ML_5_svm   # nur eine Vorlesung
uv run python -m scripts.parse -force     # vorhandene Chunks ignorieren und neu bauen
```

Das Skript fragt interaktiv nach dem **Modul**, unter dem die PDFs einsortiert werden, und
schreibt dann:

```
data/reference_slides/<modul>/<vorlesung>/page_<n>.png
data/parsed/<modul>/<vorlesung>/<vorlesung>_chunks.json
```

Der Lauf ist unterbrechbar: bereits gerenderte PNGs und bereits geparste Folien werden beim
nächsten Start übersprungen, die JSON wird nach jeder Folie fortgeschrieben. Der Parse benötigt,
je nach PDF-Größe, einige Zeit. Pro Folie geht ein VLM-Aufruf ans Gateway.

<br>

**2.3 Chunks nach `parsed_clean/` übernehmen**

Der Parser schreibt nach `data/parsed/`, der Ingest liest aber `data/parsed_clean/`
([ingest.py:14](backend/scripts/ingest.py#L14)). Der Zwischenschritt ist bewusst manuell. 
Die vom VLM erstellten Artefakte können gesichtet und korrigiert werden, bevor sie in 
die Wissensbasis übernommen werden. Anschließend kann entweder der Ordnername `data/parsed/` zu `data/parsed_clean` geändert, oder folgender Befehl verwendet werden:

```bash
cp -r data/parsed/. data/parsed_clean/
```

<br>

**2.4 Qdrant starten und Ingest ausführen**

Reihenfolge ist wichtig: **Qdrant muss laufen, bevor der Ingest startet.**

```bash
docker compose up -d qdrant     # legt ./qdrant_storage/ an, Port 6333 auf dem Host

cd backend
uv run python -m scripts.ingest
```

Der Ingest ist ein einmaliger Batch-Schritt und läuft **über den Host**, nicht im Container. Er
liest `data/parsed_clean/`, baut dense- und sparse-Embeddings und schreibt sie in die Collection
`lecture_chunks`. Beim ersten Lauf lädt sentence-transformers `bge-m3` und den Reranker in den
lokalen HuggingFace-Cache (mehrere GB). Dieser Download dauert einmalig mehrere Minuten.

<br>

### 3. System starten

Vorausgesetzt: `backend/.env` ist ausgefüllt, Qdrant
läuft im Container und die Collection ist befüllt.

<br>

#### Mit Docker (empfohlen)

```bash
docker compose up --build                            # CPU
docker compose -f docker-compose-gpu.yml up --build  # GPU
```

Dies startet Qdrant, Backend und Frontend gemeinsam. Ein bereits laufender Qdrant-Container wird
wiederverwendet. Alternativ lässt sich das System auch
[ohne Docker starten](#start-ohne-docker-für-die-entwicklung) — auf macOS der einzige Weg, die
GPU zu nutzen.

Danach:


- Frontend: <http://localhost:8501>
- API-Docs: <http://localhost:8000/docs>
- Vektordatenbank UI: <http://localhost:6333/dashboard> 

Der **erste Start des Backends dauert lange**: der Container lädt die Embedding- und Reranker-
Modelle in das `hf_cache`-Volume herunter (mehrere GB). Im Log siehst du `Loading RAG models on device: ...`. Ab dem zweiten Start ist das Volume gefüllt und der Start schnell.


<br>
<br>

---

<br>
<br>


## API

| Methode | Pfad | Beschreibung |
|---|---|---|
| `POST` | `/api/ask` | `{"question": "..."}` → Antwort mit Quellen |
| `GET` | `/api/health` | Status inkl. Qdrant-Erreichbarkeit |
| `GET` | `/slides/{pfad}` | Folien-PNG (statisch aus `slides_dir`) |
| `GET` | `/docs` | OpenAPI-UI |

Die Antwort von `/api/ask` enthält pro Quelle `cite_nr`, `title`, `modul`, `lecture`,
`page_numbers`, `slide_url`, `page_content`, `cited` und `rerank_score`. `cited` unterscheidet
Quellen, die das LLM tatsächlich zitiert hat, von zusätzlich abgerufenem Material. Das Frontend
zeigt Letztere eingeklappt unter „Zusätzliches Material" an.

<br>
<br>

---

<br>
<br>

## Troubleshooting

**`ModuleNotFoundError: No module named 'app'` beim Ingest**
`python -m scripts.ingest` statt `python scripts/ingest.py` verwenden, ausgeführt aus `backend/`.

**Backend startet nicht, `RuntimeError: Directory ... does not exist`**
`slides_dir` zeigt ins Leere — meist, weil uvicorn aus dem falschen Verzeichnis gestartet wurde.

**Validierungsfehler zu `gateway_url` / `bearer_token` beim Start**
`backend/.env` fehlt oder ist unvollständig.

**Frage wird gestellt, aber es kommt keine Antwort / Timeout beim Gateway**
Der Rechner ist nicht im Netz der HAW Kiel. Campus-Netz oder VPN herstellen. Das Gateway ist von
außen nicht erreichbar.
Typisches Bild: Frontend, Backend und Qdrant laufen normal, die Folienanzeige funktioniert, nur
die Antwort des Sprachmodells bleibt aus.

**Build bricht ab mit `Failed to download ... due to network timeout` (z. B. `nvidia-*-cu12`)**
`torch` zieht die NVIDIA-CUDA-Wheels nach. Einzelne Pakete sind mehrere hundert MB groß und
laufen auf langsamer Leitung in uvs Standard-Timeout. Erhöhung des Timeout-Limits:

```bash
UV_HTTP_TIMEOUT=1800 docker compose build backend
```

Der Fehler ist rein transient: Ein erneuter Aufruf setzt auf den bereits geladenen Paketen auf.

**Erster `docker compose up --build` hängt oder bricht beim Download ab**
Das VPN der HAW Kiel blockiert einen Teil der externen Downloads. Images, Python-Pakete und die
Embedding-/Reranker-Modelle müssen deshalb **ohne** aktives VPN geladen werden:

```bash
# VPN trennen, dann bauen und die Modelle einmalig herunterladen
docker compose up --build
```

Ab dem zweiten Start liegen Images und Modelle lokal bzw. im `hf_cache`-Volume — dann ist das VPN
nur noch für das Gateway nötig und stört nicht mehr.

**Nach dem Verbinden mit dem VPN antwortet das System weiterhin nicht**
Backend neu starten, damit die Verbindung neu aufgebaut wird: `docker compose restart backend`.

**Frontend meldet „Das Backend ist gerade nicht erreichbar"**
Backend lädt noch Modelle (erster Start) oder ist abgestürzt — `docker compose logs -f backend`.

**Antworten kommen, aber ohne Quellen / Collection leer**
Ingest wurde nicht ausgeführt oder schrieb in eine andere Collection als `collection` in der
Konfiguration. Prüfen: <http://localhost:6333/collections/lecture_chunks>

**`docker compose -f docker-compose-gpu.yml up` scheitert an `gpus: all`**
NVIDIA Container Toolkit fehlt oder die GPU wird nicht durchgereicht. Gegenprobe:
`docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi`


<br>
<br>

---

<br>
<br>


## Start ohne Docker für die Entwicklung

Praktisch für die Entwicklung, da Hot-Reload funktioniert.


```bash
# Terminal 1
docker compose up -d qdrant

# Terminal 2 — WICHTIG: aus backend/ heraus starten
cd backend
uv run uvicorn app.main:app --reload --port 8000

# Terminal 3
cd frontend
uv run streamlit run app.py
```

**PyTorch-Variante lokal wählen.** `torch` wird unterschiedlich groß installiert.
Mit den folgenden befehlen kann entschieden werden, welche verwerdet wird.

```bash
cd backend
uv sync --extra gpu     # CUDA 12.8  (Windows/Linux)
uv sync --extra cpu     # CPU-Build, deutlich kleiner
```



<br>
<br>

---

<br>
<br>

## Notebooks & Evaluation

In [notebooks/](notebooks/) sind die Experimente und die abschließende Evaluation der Thesis
entstanden. Die Notebooks laufen unabhängig von der Applikation, teilen sich mit ihr aber die
Wissensbasis in Qdrant.

### 1. Umgebung

Die Notebooks hängen am **Root-Projekt**, nicht an `backend/` — das sind zwei getrennte
`pyproject.toml` mit unterschiedlichen Dependencies:

```bash
uv sync          # im Repository-Root, NICHT in backend/
```

Als Kernel in Jupyter bzw. VS Code die `.venv` aus dem Repository-Root auswählen.

Zusätzlich nötig:

- **`.env` im Root** mit `GATEWAY_URL` und `BEARER_TOKEN` (siehe [.env.example](.env.example)).
  Jedes Notebook, das LLM oder VLM über das Gateway aufruft, liest diese .env. Nicht zu verwechseln mit
  `backend/.env`! Diese gilt nur für die Applikation.
- **Laufendes Qdrant**:

```bash
docker compose up -d qdrant
```

### 2. Welches Notebook für welchen Usecase


| Notebook | Was es macht und wofür es verwendet wurde |
|---|---|
| **Parsing** ||
| [parse.ipynb](notebooks/parse.ipynb) | Vollständiger Parse über den gesamten Korpus. Reproduzierbarer Testlauf eines gesamten Parses inklusiver der Latenz und des Tokenverbrauchs als Kostenbeleg. |
| [parsing_vlm_first_test.ipynb](notebooks/parsing_vlm_first_test.ipynb) | Vorexperiment reines VLM-Parsing. Das Folienbild wird **ohne** Ankertext direkt an das VLM gereicht. Parst eine Testvorlesung und zeigt Folie neben Parseartefakt zur Sichtprüfung. |
| [parsing_with_docling_test.ipynb](notebooks/parsing_with_docling_test.ipynb) | Vorexperiment mit Docling. Erzeugt pro Seite einen Anker-Markdown, welcher zusammen mit dem Bild an das VLM gesendet wird. |
| [parsing_docling_isolated_test.ipynb](notebooks/parsing_docling_isolated_test.ipynb) | Docling allein, ohne VLM. Eine Seite neben Docling-Markdown, dazu die Visualisierung der erkannten Bounding-Boxes als Bild. Erstellt, um zu evaluieren, was Docling extrahiert und wo Fehler entstehen. |
| [parsing_notebooks_test.ipynb](notebooks/parsing_notebooks_test.ipynb) | Iteratives Testen, wie Notebooks geparst werden sollten. |
| **Parsing-Evaluation** ||
| [evaluation_docling_vs_vlmonly.ipynb](notebooks/evaluation_docling_vs_vlmonly.ipynb) | Der Test beider Parsing-Varianten gegen den Goldstandard. Bewertet die Parsingqualität in einer Gegenüberstellung mittels String-Vergleich und LLM-as-a-Judge. |
| [evaluation_full_parse.ipynb](notebooks/evaluation_full_parse.ipynb) | Evaluation des finalen Parses. Ergibt die Zahlen fürs Parsing-Kapitel. |
| [evaluation_reasoning_onoff.ipynb](notebooks/evaluation_reasoning_onoff.ipynb) | Parst die Vorlesungen mit Reasoning im VLM aus und an. Stellt den Recall den Kosten gegenüber (Latenz und Tokens pro Folie). Zeigt die Auswirkungen des Reasonings auf die Parsingqualität. |
| [hallucination_check.ipynb](notebooks/hallucination_check.ipynb) | Nugget-Recall misst lediglich die Kontexttreue und keine Halluzinationen. In diesem Notebook erfolgt die manuelle Stichprobe. Die Folienbilder werden neben beiden Parse-Varianten dargestellt, um Halluzinationen zu suchen. |
| **Ingestion** ||
| [ingestion.ipynb](notebooks/ingestion.ipynb) | Baut iterativ die Wissensbasis auf und dient dem Test der einzelnen Implementationen. |
| **Retrieval** ||
| [retrieval.ipynb](notebooks/retrieval.ipynb) | Der Retrieval-Stack im Detail. Dense-only vs. Hybrid mit RRF, danach Cross-Encoder-Reranking. Dient dem iterativen Testen der Implementation des Retrievalservices, um diesen später in den Prototypen zu übernehmen. |
| **Generierung** ||
| [generation.ipynb](notebooks/generation.ipynb) | Die Inferenz. Kontext an `[n]`-Zitatmarker binden und iterativ den Output mit verschiedenen Systemprompts testen. Auflösen der Zitationsmarker implementieren. |
| [evaluation_rag.ipynb](notebooks/evaluation_rag.ipynb) | Die vollständige Evaluation. Erst Retrieval-Qualität mittels MRR und recall@k je Strategie, dann Antwortqualität per LLM-Judge. |
| [judge_validation.ipynb](notebooks/judge_validation.ipynb) | Validiert beide Judges gegen menschliches Urteil. Eigenständige Stichprobenbewertung, um die Judges zu validieren und ihre Aussagen belastbar zu machen. |

### 3. Datenstand der Evaluation

Die Evaluations-Notebooks lesen bewusst `data/parsed_NO_EDIT/` und nicht `data/parsed/`.
`data/parsed/` ist die aktive Ausgabe der Parsing-Pipeline und wird bei jedem Lauf neu
geschrieben. `data/parsed_NO_EDIT/` hingegen ist der eingefrorene Parse-Stand, auf dem sämtliche in
der Thesis berichteten Kennzahlen erhoben wurden. Er bleibt unangetastet.

Wer die Evaluation auf einem **eigenen** Parse wiederholen möchte, muss die Quellpfade in den
Notebooks entsprechend anpassen. Betroffen ist jeweils die Konstante `PARSED` im Setup-Block.

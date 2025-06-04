# Guide 2

Følgende vejledning guider jer gennem, hvordan I arbejder med det nye projekt. I skal implementere en række “stub”-services (som pt returnerer dummy data). I kan sammenligne med “\_example”-versionerne (der indeholder en fuldt funktionel løsning). Serveren kan køre fra start til slut allerede nu, men I skal selv udfylde logik for at få brugbare tags ud.

---

## 1. Projektstruktur

Når I har klonet repository’et, vil filstrukturen se omtrent sådan ud:

```
app/
├─ api/
│   └─ routes/
│       └─ events.py               # FastAPI‐endpoints (bruges til at kalde processering og submission)
├─ config.py                       # Indstillinger: data_mappe, dashboard_url, OPENAI_API_KEY, modelnavn osv.
├─ models/
│   ├─ requests.py                 # Pydantic‐modeller for API‐requests: EventTagRequest, BatchTagRequest, SendSubmissionRequest
│   └─ responses.py                # Pydantic‐modeller for API‐responses: EventTagResponse, TagTriple, BatchTagResponse, EvaluationResponse, DashboardResponse
├─ services/
│   ├─ event_processor.py          # Det centrale workflow (kald til alle services i rækkefølge)
│   ├─ helpers.py                  # Utility‐funktioner (f.eks. beregn_processing_time, estimate_cost)
│   ├─ initialization.py           # Indlæser CSV‐data i memory (tagsregler)
│   ├─ input_validator.py          # Stub: Validér og rengør input
│   ├─ prompt_generator.py         # Stub: Generér prompt til LLM
│   ├─ llm_client.py               # Stub: Send prompt til OpenAI og få svar (dummy‐udgave)
│   ├─ output_parser.py            # Stub: Parsér LLM’s JSON‐svar til TagTriple
│   ├─ confidence_evaluator.py     # Stub: Beregn tillids‐score eller kvalitet
│   ├─ human_review_checker.py     # Stub: Beslut om menneskelig review kræves
│   ├─ send_submission.py          # Læser CSV → proces → POST til dashboard
│   ├─ input_validator_example.py  # Eksempel på implementering af input_validator
│   ├─ prompt_generator_example.py # Eksempel på implementering af prompt_generator
│   ├─ llm_client_example.py       # Eksempel: Kald til OpenAI
│   ├─ output_parser_example.py    # Eksempel: Fungerende JSON‐parser
│   ├─ confidence_evaluator_example.py  # Eksempel på confidence eval
│   └─ human_review_checker_example.py  # Eksempel på menneskelig review‐logik
├─ run.py                           # Runs the server
├─ requirements.txt
├─ .env
├─ .gitignore
```

* **Alle filer uden `_example`** er lige nu “stub”-services, som returnerer dummy‐værdier.
* **Alle `_example`-filer** viser en fuldt fungerende version af samme service. Brug dem til inspiration, eller hvis i blot ikke gider implementere en service.
---

## 2. Overordnet arbejdsgang

1. **Klon repository og installer afhængigheder**

   ```bash
   git clone <repo‐URL>
   cd <projektmappe>
   python3.11 -m venv .venv
   source .venv/bin/activate   # (Windows: .\.venv\Scripts\Activate)
   pip install -r requirements.txt
   ```

Lav eventuelt egen branch.

2. **Sæt OPENAI nøgle og dashboard‐URL i en `.env`‐fil**

     ```env
      DEBUG=true
      HOST=0.0.0.0
      PORT=8000
      DASHBOARD_URL=https://v0-ida-tagging-dashboard.vercel.app
      OPENAI_API_KEY=api_nøgle_her
      OPENAI_MODEL=gpt-4o
      LLM_TEMPERATURE=0.3
      # LLM_MAX_TOKENS=500  # Optional - leave commented out to use default
      CONFIDENCE_THRESHOLD=0.7
      HUMAN_REVIEW_THRESHOLD=0.5
      BACKGROUND_PROCESSING_THRESHOLD=50
      DATA_DIR=data
      LOG_LEVEL=INFO
     ```

3. **Kør serveren**

   ```bash
   python run.py
   ```

4. **Test dummy‐endpoints**

   * `POST /api/v1/events/tag` med et JSON‐body, fx:

     ```json
        {
          "arrangement_nummer": "000001",
          "arrangement_titel": "Machine Learning Kursus",
          "arrangør": "string",
          "arrangor": "IDA IT",
          "arrangement_undertype": "fagteknisk gruppe",
          "nc_teaser": "Kom og lær grundlæggende ML og python",
          "nc_beskrivelse": "string",
          "beskrivelse_html_fri": "string",
          "include_reasoning": true,
          "require_confidence": true
        }
     ```

     Svar vil være et **dummy‐tag** (PROGRAMMERING_OG_UDVIKLING, confidence = –1, reasoning = “Bare fordi”).

---

* `GET /api/v1/events/evaluate`

  Brug dette endpoint til at få en evaluering af jeres nuværende model. Systemet loader valideringsdatasættet og kører jeres pipeline igennem det, præcis som hvis I lavede en rigtig submission – men uden at sende resultaterne til dashboardet, og på et andet dataset.

  **Responsen** indeholder både et samlet metrics‐overblik og en detaljeret sammenligning for hvert arrangement, f.eks.:

  * `accuracy_at_1`, `accuracy_at_2`, `accuracy_at_3`
  * `precision`, `recall`, `f1_score`
  * `average_confidence` og `correct_predictions`
  * Og for hvert arrangement: predicted tags vs. ground truth, om det var korrekt, samt evt. fejlbesked

  Dette gør det nemt at debugge og forstå, hvor jeres model rammer ved siden af – og hvilke tags der evt. forveksles oftest. I responsen får I desuden en liste over de mest forvekslede tags (`most_confused_tags`) og hvilke kategorier I klarer jer bedst og dårligst på.

  **Eksempel:**
  Hvis jeres model konsekvent vælger `PROGRAMMERING_OG_SOFTWAREUDVIKLING`, uanset indhold, vil det afspejles i både `accuracy` og `most_confused_tags`.

  Dette endpoint er altså jeres go-to værktøj til at iterere hurtigt og lokalt

---

Jeg har lavet et dashboard - bare fordi det kunne være sjovt :-) I kan submit jeres score til det med nedenstående endpoint. Prøv at holde det til et minimum, da man skal validerer op mod validerings sættet, og kun en sjælden gang i mellem afprøve test sættet. (Da man ellers kan risikere bias og derved overfitting)

   * `POST /api/v1/events/send_submission` med:

     ```json
     {
       "name": "dit-navn-som det vil vises på dashboardet"
     }
     ```

     Svar vil være **dummy‐payload** retur fra “dashboard”, f.eks.:

     ```json
     {
       "success": true,
       "participant": {
         "id": "uuid",
         "name": "navn",
         "submittedAt": "2025-xx-xxTxx:xx:xxZ",
         "metrics": {
            "accuracy_at_1": 0.15,
            "accuracy_at_2": 0.15,
            "accuracy_at_3": 0.15,
            "weighted_accuracy": 0.15,
            "exact_match_at_2": 0.1,
            "exact_match_at_3": 0.1,
            "precision": 0.15,
            "recall": 0.0967741935483871,
            "f1_score": 0.11764705882352941,
            "average_confidence": -1.0,
            "total_predictions": 20,
            "correct_predictions": 3,
            "model_used": "gpt-4o",
            "total_participant_processing_time_ms": 36.69452667236328,
            "average_participant_processing_time_ms": "None",
            "total_participant_cost_dkk": 0.02599999999999999,
            "total_participant_tokens_used": 620.0,
            "dashboard_evaluation_time_ms": 404.0
          }
       },
     }
     ```

   På den måde kan I se, at “alt kører” – men at logik og LLM‐kald stadig er dummy.

5. **Implementér “stub”-services**

   * Åbn `app/services/input_validator.py`, find `TODO: implementér mig`, skriv jeres egen validering (brug `input_validator_example.py` for inspiration eller for at springe over).
   * Gør det samme for `prompt_generator.py`, `llm_client.py`, `output_parser.py`, `confidence_evaluator.py`, `human_review_checker.py`.
   * I “\_example”‐filerne er alt “rigtigt” arbejde allerede beskrevet, men i stub‐filen må I selv teste og tilrette – eventuelt kopiere relevant kode fra example‐filen.

Mange af implementeringerne kan virke ligegyldige eller overdrevet - det er blot for at vise eksempel på workflow. Fx er det nok ikke nødvendigt at tjekke for følsom data med input_validator. Men det er her man normalt kan gøre det, og hvor vi bl.a. gjorde det med barselsbotten.

Confidence evaluation er også ret overflødig, men blot endnu et eksempel, for at give inspiration til fremtidige projekter.

#### OBS: Systemet forventer takes i all caps og _
Fx skal "Programmering og softwareudvkling" outputtes som "PROGRAMMERING_OG_SOFTWAREUDVIKLING"

6. **Submit til dashboard**

   * Når prompt_generator, llm_client og output_parser er korrekt udfyldt, kan I igen kalde med jeres implementer. De andre services er mere optional.:

     ```bash
     curl -X POST http://localhost:8000/api/v1/events/send_submission \
          -H "Content-Type: application/json" \
          -d '{"name":"MitTeamNavn"}'
     ```
   * Dermed vil `send_submission`:

     1. Load CSV‐filen i `data/arrangementer_til_tagging_test_set.csv`.
     2. Kalde `process_single_event(...)` for hvert arrangement.
     3. Bygge et stort `predictions`‐objekt og `POST` det til `DASHBOARD_URL/api/submit`.
     4. Returnere dashboardets faktiske svar.

     Herefter er jeres score live på dashboard.

     Dashboardet kan ses her: [Dashboard](https://v0-ida-tagging-dashboard.vercel.app/)

---

## 3. Detaljer om de enkelte services

### 3.1 `input_validator.py` (stub)

  ```python
  async def validate_and_clean(request: EventTagRequest) -> EventTagRequest:
      """
      Tjek at f.eks. arrangement_titel ikke er tom, strip HTML mv.
      Returnér cleanet request (eller kast fejl).
      """
  ```

---

### 3.2 `prompt_generator.py` (stub)

  ```python
  async def generate_tagging_prompt(request: EventTagRequest) -> PromptResponse:
      """
      Byg en tekst‐prompt med arrangementets felter og available_tags fra konfiguration.
      Returnér PromptResponse(prompt=<str>, available_tags=[…]).
      """
  ```

---

### 3.3 `llm_client.py` (stub)

  ```python
  async def get_tags(prompt: str, temperature: float, max_tokens: int) -> LLMResponse:
      """
      Send prompt til OpenAI og få et response objekt som svar. Returnér LLMResponse(content=<str_json>, tokens_used=<int>, …).
      """
  ```

---

### 3.4 `output_parser.py` (stub)

  ```python
  async def parse_tag_response(llm_output: str, available_tags: List[str]) -> ParsedTagResponse:
      """
      Parsér llm_output, træk tag1, tag2, tag3, confidence og reasoning ud, 
      og returnér ParsedTagResponse.
      Hvis ugyldig: returnér is_valid=False + fejlbesked.
      """
  ```

---

### 3.5 `confidence_evaluator.py` (stub)

  ```python
  def calculate_confidence(parsed_tags: ParsedTagResponse) -> float:
      """
      Udregn en endelig confidence‐score baseret på parsed_tags.confidence, måske LLM‐metadata, 
      eller kombiner med tidligere data. Returnér float (0.0–1.0).
      """
  ```

---

### 3.6 `human_review_checker.py` (stub)

  ```python
  def needs_human_review(parsed_tags: ParsedTagResponse, confidence: float) -> bool:
      """
      Afgør, om en menneskelig review behøves. F.eks. hvis confidence < 0.5 eller flere tags.
      Returnér True/False.
      """
  ```

---

---

## 4. Tl:dr

* **"Alle" stub‐filer** i `services/` skal udfyldes med reel logik.
* **\_example‐filerne** indeholder komplette eksempler, hvis i har behov inspiration eller vil springe en over.
* **event\_processor.py** og **FastAPI‐routerne** behøver ikke ændres.

God arbejdslyst!

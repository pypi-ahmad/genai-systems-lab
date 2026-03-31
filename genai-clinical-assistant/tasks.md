# Tasks

## Create Medical Knowledge Base

- Define a structured format for storing clinical guidelines and drug interactions.
- Add a loader in `app/knowledge_base.py` that reads knowledge entries from local files.
- Seed the `data/` directory with a small set of sample clinical guidelines.
- Add a lookup method that retrieves entries by condition or keyword.
- Verify that loaded entries are searchable after initialization.

## Build Input Extractor

- Create the extraction interface in `app/extractor.py`.
- Define the input format for raw patient data (symptoms, vitals, history).
- Add a method that parses raw input into a structured patient record.
- Normalize extracted fields into a consistent schema for downstream modules.
- Handle missing or incomplete fields gracefully with explicit defaults.

## Implement Retrieval Logic

- Create the retrieval interface in `app/retriever.py`.
- Accept a structured patient record as input.
- Query the knowledge base for guidelines matching the patient's conditions.
- Rank retrieved entries by relevance to the extracted symptoms and history.
- Return a list of candidate guidelines with source references.

## Build Reasoning Module

- Create the reasoning interface in `app/reasoner.py`.
- Accept the patient record and retrieved guidelines as input.
- Define the prompt template for clinical reasoning over patient context.
- Call the LLM to generate a differential diagnosis or recommended actions.
- Parse the LLM response into a structured reasoning output.

## Add Risk Scoring

- Create the risk evaluation interface in `app/risk_evaluator.py`.
- Accept the structured reasoning output as input.
- Define scoring criteria based on severity, comorbidities, and contraindications.
- Compute a risk score and categorize as low, moderate, or high.
- Attach the risk category and contributing factors to the output.

## Format Output

- Create the formatting interface in `app/formatter.py`.
- Accept the reasoning output and risk evaluation as input.
- Produce a human-readable clinical summary with diagnosis, recommendations, and risk level.
- Include source references from retrieved guidelines.
- Add a structured output option for downstream consumption.


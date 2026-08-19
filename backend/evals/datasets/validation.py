import json
from pydantic import ValidationError
from pathlib import Path
from .schema import DataSetSchema
from app.core.logging import logger

def validate_dataset(json_path: str):
    file_path = Path(json_path)
    print(f"file_path:{file_path}")
    if not file_path.exists():
        logger.bind(
            json_path=str(json_path),
            error_reason = "Dataset file not found"
        ).error("dataset.validation.error")
        return

    valid_inputs = []
    valid_outputs = []
    invalid_rows = 0

    logger.bind(
        json_path = str(json_path)
    ).info("dataset.validation.started")

    with open(file_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start = 1):

            line = line.strip()
            
            if not line:
                continue

            try:
                data = json.loads(line)
                validated_data = DataSetSchema.model_validate(data)

                inputs = {
                    "question" : validated_data.question
                }

                outputs = {
                    "expected_route": validated_data.expected_route.value,
                    "reference_answer": validated_data.reference_answer,
                    "reference_evidence": validated_data.reference_evidence.model_dump() if validated_data.reference_evidence else None
                }

                valid_inputs.append(inputs)
                valid_outputs.append(outputs)

            except json.JSONDecodeError:
                invalid_rows+=1
                logger.bind(
                    json_path=str(json_path),
                    error_reason = f"invalid json string formatting | row number {line_number}"
                ).error("dataset.validation.error")

            except ValidationError:
                invalid_rows+=1

                logger.bind(
                    json_path=str(json_path),
                    error_reason = f"dataset validation error | row number {line_number}"
                ).error("dataset.validation.error")

    logger.bind(
        json_path = str(json_path),
        details = f"valid inputs = {len(valid_inputs)} | invlid input : {invalid_rows}"
    ).info("dataset.validation.complete")

    return valid_inputs, valid_outputs

# if __name__ == "__main__":
#     validated_inputs, validated_outputs = validate_dataset("evals/datasets/golden.jsonl")
#     print(f"Validated input: \n  {validated_inputs}\n")
#     print(f"Validated outputs: \n  {validated_outputs}")
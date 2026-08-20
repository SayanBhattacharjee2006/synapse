import asyncio
import json
import pprint
from datetime import datetime
from pathlib import Path
from .datasets.upload_dataset import upload_dataset
from .datasets.validation import validate_dataset
from .runner.eval_runner import evaluation_runner
from app.core.config import settings
from .result import result_aggregator


def make_json_serializable(data):
    if isinstance(data, dict):
        return {
            key: make_json_serializable(value)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [
            make_json_serializable(item)
            for item in data
        ]

    if hasattr(data, "model_dump"):
        return make_json_serializable(data.model_dump())

    return data


def save_evaluation_result(result, output_dir="evals/results"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    file_path = output_path / f"evaluation_{timestamp}.json"

    serializable_result = make_json_serializable(result)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            serializable_result,
            file,
            indent=2,
            ensure_ascii=False,
        )

    return file_path


async def orchestrator(json_path: str):

    valid_inputs, valid_outputs = validate_dataset(json_path)

    _, generated_outputs = await asyncio.gather(
        asyncio.to_thread(
            upload_dataset,
            "synapse-golden-v3",
            valid_inputs,
            valid_outputs,
        ),
        evaluation_runner(
            valid_inputs,
            settings.EVAL_CONVO_ID,
            True,
            valid_outputs,
        ),
    )

    print("------------------------------------------------\n")

    for res in generated_outputs:
        if res["router_evaluation"] == 0:
            print(res)

    print("------------------------------------------------\n")

    aggregated_results = result_aggregator(generated_outputs)

    return aggregated_results


if __name__ == "__main__":

    aggregate = asyncio.run(
        orchestrator("evals/datasets/golden.jsonl")
    )

    file_path = save_evaluation_result(aggregate)

    print(f"\nEvaluation result saved to: {file_path}\n")

    pprint.pprint(aggregate)
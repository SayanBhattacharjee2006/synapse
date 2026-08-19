import asyncio
import pprint
from .datasets.upload_dataset import upload_dataset
from .datasets.validation import validate_dataset
from .runner.eval_runner import evaluation_runner
from app.core.config import settings
from .result import result_aggregator

async def orchestrator(json_path: str):
    valid_inputs, valid_outputs = validate_dataset(json_path)

    _, generated_outputs = await asyncio.gather(
        asyncio.to_thread(
            upload_dataset,
            "synapse-golden-v2",
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

    # print("------------------------------------------------\n")
    # for res in generated_outputs:
    #     print(res["answer_evaluation"].groundedness)
    #     print(res["answer_evaluation"].reason)
    #     print("\n---------------------\n")
    # print("------------------------------------------------\n")

    aggregated_results = result_aggregator(generated_outputs)

    return aggregated_results



if __name__ == "__main__":
    aggregate = asyncio.run(orchestrator("evals/datasets/golden.jsonl"))

    
    pprint.pprint(aggregate)

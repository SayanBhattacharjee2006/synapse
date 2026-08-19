import asyncio
from .datasets.upload_dataset import upload_dataset
from .datasets.validation import validate_dataset
from .runner.eval_runner import evaluation_runner
from app.core.config import settings

async def orchestrator(json_path: str):
    valid_inputs, valid_outputs = validate_dataset(json_path)

    _, generated_outputs = await asyncio.gather(
        asyncio.to_thread(
            upload_dataset,
            "synapse-golden-v1",
            valid_inputs,
            valid_outputs,
        ),
        evaluation_runner(
            valid_inputs,
            settings.EVAL_CONVO_ID,
            True,
        ),
    )

    return generated_outputs

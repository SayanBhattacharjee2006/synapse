from .validation import validate_dataset
from app.core.logging import logger
from langsmith import Client


def validate_and_upload_dataset(json_path: str, dataset_name: str):

    valid_inputs, valid_outputs = validate_dataset(json_path)
                    
    if not valid_inputs:
        logger.bind(
            json_path=str(json_path),
            details = "No valid inputs found"
        ).warning("dataset.upload.incomplete")
        return

    try:
        logger.bind(
            json_path=str(json_path)
        ).info("dataset.upload.started")

        client = Client()

        if client.has_dataset(dataset_name=dataset_name):
            logger.bind(
                json_path=str(json_path),
                error_details = f"Dataset with name {dataset_name} already exists"
            ).warning("dataset.upload.error")
            return 
        else:
            dataset = client.create_dataset(
                dataset_name=dataset_name,             
            )

        client.create_examples(
            inputs=valid_inputs,
            outputs=valid_outputs,
            dataset_id=dataset.id
        )

        logger.bind(
            json_path=str(json_path),
        ).info("dataset.upload.complete")
    except Exception as e:
        logger.bind(
            json_path=str(json_path),
        ).error("dataset.upload.error")
        print("error",e)
    return 



if __name__ == "__main__":
    validate_and_upload_dataset(
        "evals/datasets/golden.jsonl",
        "synapse-golden-v1"
    )
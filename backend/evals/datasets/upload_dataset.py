from app.core.logging import logger
from langsmith import Client


def upload_dataset(
    dataset_name: str,
    validated_inputs,
    validated_outputs,
):
    try:
        logger.bind(
            dataset_name=dataset_name,
        ).info("dataset.upload.started")

        client = Client()

        if client.has_dataset(dataset_name=dataset_name):
            logger.bind(
                dataset_name=dataset_name,
                error_details=f"Dataset with name {dataset_name} already exists",
            ).warning("dataset.upload.error")
            return

        dataset = client.create_dataset(
            dataset_name=dataset_name,
        )

        client.create_examples(
            inputs=validated_inputs,
            outputs=validated_outputs,
            dataset_id=dataset.id,
        )

        logger.bind(
            dataset_name=dataset_name,
        ).info("dataset.upload.complete")

    except Exception as e:
        logger.bind(
            dataset_name=dataset_name,
            error_reason=str(e),
        ).exception("dataset.upload.error")

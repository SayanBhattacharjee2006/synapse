def result_aggregator(results):
    count_correct_routers = 0
    total_tests = 0
    aggregated_correctness = 0
    aggregated_relevance = 0
    aggregated_groundedness = 0
    aggregated_overall_score = 0
    groundedness_tests_count = 0

    for result in results:
        total_tests += 1
        if result["router_evaluation"]:
            count_correct_routers += 1
        aggregated_correctness += result["answer_evaluation"].correctness
        aggregated_relevance += result["answer_evaluation"].relevance
        if result["answer_evaluation"].groundedness is not None:
            groundedness_tests_count += 1
            aggregated_groundedness += result["answer_evaluation"].groundedness
        aggregated_overall_score += result["answer_evaluation"].overall

    aggregated_result = {
        "router_accuracy": (count_correct_routers / total_tests) * 100,
        "average_correctness": aggregated_correctness / total_tests,
        "average_relevance": aggregated_relevance / total_tests,
        "average_groundedness": aggregated_groundedness / groundedness_tests_count,
        "average_overall_score": aggregated_overall_score / total_tests,
    }

    return aggregated_result

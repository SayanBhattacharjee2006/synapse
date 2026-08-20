def result_aggregator(results):

    routes = ["none", "rag", "web", "both"]

    # Global aggregation

    total_tests = len(results)

    correct_router_count = 0

    total_correctness = 0
    total_relevance = 0
    total_overall = 0

    total_groundedness = 0
    groundedness_count = 0

    total_retrieval_relevance = 0
    total_retrieval_completeness = 0
    retrieval_count = 0

    # Route aggregation

    route_stats = {
        route: {
            "tests": 0,
            "correct_router": 0,

            "correctness": 0,
            "relevance": 0,
            "overall": 0,

            "groundedness": 0,
            "groundedness_count": 0,

            "retrieval_relevance": 0,
            "retrieval_completeness": 0,
            "retrieval_count": 0,
        }
        for route in routes
    }

    # Failure reporting

    router_failures = []
    answer_failures = []
    low_groundedness = []
    low_relevance = []

    low_retrieval_relevance = []
    low_retrieval_completeness = []

    # Process results

    for result in results:

        expected_route = result["expected_route"]
        route_stat = route_stats[expected_route]

        route_stat["tests"] += 1

        # Router evaluation

        router_score = result["router_evaluation"]

        if router_score:
            correct_router_count += 1
            route_stat["correct_router"] += 1
        else:
            router_failures.append(result)

        # Answer evaluation

        answer_eval = result["answer_evaluation"]

        total_correctness += answer_eval.correctness
        total_relevance += answer_eval.relevance
        total_overall += answer_eval.overall

        route_stat["correctness"] += answer_eval.correctness
        route_stat["relevance"] += answer_eval.relevance
        route_stat["overall"] += answer_eval.overall

        # Groundedness

        if answer_eval.groundedness is not None:

            total_groundedness += answer_eval.groundedness
            groundedness_count += 1

            route_stat["groundedness"] += answer_eval.groundedness
            route_stat["groundedness_count"] += 1

        # Answer failures

        if answer_eval.correctness < 3 or answer_eval.overall < 3:
            answer_failures.append(result)

        if (
            answer_eval.groundedness is not None
            and answer_eval.groundedness < 3
        ):
            low_groundedness.append(result)

        if answer_eval.relevance < 3:
            low_relevance.append(result)

        # Retrieval evaluation

        retrieval_eval = result.get("retrieval_evaluation")

        if retrieval_eval is not None:

            total_retrieval_relevance += retrieval_eval.relevance
            total_retrieval_completeness += retrieval_eval.completeness
            retrieval_count += 1

            route_stat["retrieval_relevance"] += retrieval_eval.relevance
            route_stat["retrieval_completeness"] += retrieval_eval.completeness
            route_stat["retrieval_count"] += 1

            if retrieval_eval.relevance < 3:
                low_retrieval_relevance.append(result)

            if retrieval_eval.completeness < 3:
                low_retrieval_completeness.append(result)

    # Per-route metrics

    route_results = {}

    for route, stats in route_stats.items():

        tests = stats["tests"]

        if tests == 0:
            continue

        route_results[route] = {
            "tests": tests,

            "router_accuracy": (
                stats["correct_router"] / tests * 100
            ),

            "average_correctness": (
                stats["correctness"] / tests
            ),

            "average_relevance": (
                stats["relevance"] / tests
            ),

            "average_groundedness": (
                stats["groundedness"] / stats["groundedness_count"]
                if stats["groundedness_count"]
                else None
            ),

            "average_overall": (
                stats["overall"] / tests
            ),

            "average_retrieval_relevance": (
                stats["retrieval_relevance"] / stats["retrieval_count"]
                if stats["retrieval_count"]
                else None
            ),

            "average_retrieval_completeness": (
                stats["retrieval_completeness"] / stats["retrieval_count"]
                if stats["retrieval_count"]
                else None
            ),
        }

    # Final evaluation report

    aggregated_result = {
        "total_tests": total_tests,

        "metrics": {
            "router_accuracy": (
                correct_router_count / total_tests * 100
                if total_tests
                else 0
            ),

            "average_correctness": (
                total_correctness / total_tests
                if total_tests
                else 0
            ),

            "average_relevance": (
                total_relevance / total_tests
                if total_tests
                else 0
            ),

            "average_groundedness": (
                total_groundedness / groundedness_count
                if groundedness_count
                else None
            ),

            "average_overall": (
                total_overall / total_tests
                if total_tests
                else 0
            ),

            "average_retrieval_relevance": (
                total_retrieval_relevance / retrieval_count
                if retrieval_count
                else None
            ),

            "average_retrieval_completeness": (
                total_retrieval_completeness / retrieval_count
                if retrieval_count
                else None
            ),
        },

        "by_route": route_results,

        "failures": {
            "router": router_failures,
            "answer": answer_failures,
            "low_groundedness": low_groundedness,
            "low_relevance": low_relevance,
            "low_retrieval_relevance": low_retrieval_relevance,
            "low_retrieval_completeness": low_retrieval_completeness,
        },

        # Preserve every individual evaluation result.
        # This is useful for debugging and later persistence.
        "results": results,
    }

    return aggregated_result
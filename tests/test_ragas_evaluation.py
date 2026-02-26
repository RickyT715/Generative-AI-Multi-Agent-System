"""RAGAS evaluation tests for the RAG pipeline.

Measures retrieval and answer quality using the RAGAS framework.
Requires a populated ChromaDB vector store and LLM API keys.

Run modes:
    pytest tests/test_ragas_evaluation.py -v -m integration -s
    python tests/test_ragas_evaluation.py --mode both|retrieval|answer
"""

import argparse
import math

import pytest

ragas = pytest.importorskip("ragas", reason="ragas package not installed")

import warnings  # noqa: E402

from ragas import EvaluationDataset, SingleTurnSample, evaluate  # noqa: E402
from ragas.embeddings import LangchainEmbeddingsWrapper  # noqa: E402
from ragas.llms import LangchainLLMWrapper  # noqa: E402

# Use legacy ragas.metrics (still functional) because ragas.metrics.collections
# requires InstructorLLM and is incompatible with LangchainLLMWrapper.
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from ragas.metrics import (  # noqa: E402
        FactualCorrectness,
        Faithfulness,
        LLMContextPrecisionWithReference,
        LLMContextRecall,
        ResponseRelevancy,
        SemanticSimilarity,
    )

from src.config.settings import get_embedding_model, get_llm  # noqa: E402
from src.db.vector_store import get_retriever  # noqa: E402

# ---------------------------------------------------------------------------
# Test dataset: 15 questions (5 per PDF) with ground truth from PDF content
# ---------------------------------------------------------------------------

EVAL_QUESTIONS = [
    # --- Refund Policy (5) ---
    {
        "question": "What is the refund window for monthly subscription plans?",
        "ground_truth": (
            "Customers may request a full refund within 30 days of the initial "
            "purchase date for monthly plans. After the 30-day period, no refund "
            "is issued."
        ),
    },
    {
        "question": "What is the refund policy for annual subscription plans?",
        "ground_truth": (
            "Annual subscriptions are eligible for a prorated refund up to 90 days "
            "after purchase."
        ),
    },
    {
        "question": "Which items are non-refundable according to the refund policy?",
        "ground_truth": (
            "Non-refundable items include setup and configuration fees for enterprise "
            "deployments, custom development or integration work, training sessions "
            "that have already been delivered, domain registration fees, and "
            "third-party add-ons purchased through the marketplace."
        ),
    },
    {
        "question": "How long does it take to process a refund?",
        "ground_truth": (
            "Refunds are processed within 5-10 business days to the original "
            "payment method."
        ),
    },
    {
        "question": "How can a customer escalate a denied refund request?",
        "ground_truth": (
            "Customers may escalate by contacting the Customer Advocacy team at "
            "advocacy@techcorp.com. Disputes are typically resolved within 15 "
            "business days. For unresolved disputes, customers may seek resolution "
            "through binding arbitration as outlined in the Terms of Service."
        ),
    },
    # --- Privacy Policy (5) ---
    {
        "question": "How long does TechCorp retain transaction records?",
        "ground_truth": (
            "Transaction records are retained for 7 years for legal and tax "
            "compliance."
        ),
    },
    {
        "question": "What encryption standards does TechCorp use to protect data?",
        "ground_truth": (
            "TechCorp uses AES-256 encryption at rest and TLS 1.3 for data in "
            "transit."
        ),
    },
    {
        "question": "What rights do users have under GDPR according to TechCorp's privacy policy?",
        "ground_truth": (
            "Users have the Right to Access, Right to Rectification, Right to "
            "Erasure, Right to Portability, Right to Object, Right to Restrict "
            "processing, and Right to Withdraw Consent."
        ),
    },
    {
        "question": "How can users contact TechCorp's Data Protection Officer?",
        "ground_truth": (
            "Users can contact the Data Protection Officer at dpo@techcorp.com. "
            "TechCorp will respond to requests within 30 days."
        ),
    },
    {
        "question": "How long is account data retained after the account becomes inactive?",
        "ground_truth": (
            "Account data is retained for the duration of account activity plus "
            "2 years."
        ),
    },
    # --- Terms of Service (5) ---
    {
        "question": "What are the subscription tiers and their prices offered by TechCorp?",
        "ground_truth": (
            "TechCorp offers Free Tier (limited features, 1 user, 1GB storage), "
            "Basic Plan at $9.99/month (core features, 5 users, 50GB storage), "
            "Premium Plan at $29.99/month (all features, 25 users, 500GB storage), "
            "and Enterprise Plan with custom pricing (unlimited features and users)."
        ),
    },
    {
        "question": "What is TechCorp's uptime guarantee for paid plans?",
        "ground_truth": (
            "TechCorp commits to 99.9% monthly uptime guarantee, excluding "
            "scheduled maintenance, for paid plans."
        ),
    },
    {
        "question": "What are the support response times for critical issues across different plans?",
        "ground_truth": (
            "Critical issue response times are 1 hour for Enterprise, 4 hours "
            "for Premium, and 24 hours for Basic plans."
        ),
    },
    {
        "question": "What happens to user data when an account is terminated?",
        "ground_truth": (
            "Upon termination, the right to access services ceases immediately. "
            "Data is retained for 30 days during which the user may export it. "
            "After 30 days, all data is permanently deleted. Outstanding fees "
            "remain payable."
        ),
    },
    {
        "question": "What is the minimum age requirement to create a TechCorp account?",
        "ground_truth": "You must be at least 18 years old to create an account.",
    },
]

# Recommended thresholds (informational, not hard-gated)
THRESHOLDS = {
    "faithfulness": 0.7,
    "context_recall": 0.7,
    "context_precision": 0.7,
    "factual_correctness": 0.5,
    "answer_relevancy": 0.7,
    "semantic_similarity": 0.7,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_retrieval_dataset():
    """Retrieve contexts for each question and build a RAGAS dataset."""
    retriever = get_retriever()
    samples = []
    for item in EVAL_QUESTIONS:
        docs = retriever.invoke(item["question"])
        contexts = [doc.page_content for doc in docs]
        samples.append(
            SingleTurnSample(
                user_input=item["question"],
                retrieved_contexts=contexts,
                response="",  # not needed for retrieval-only metrics
                reference=item["ground_truth"],
            )
        )
    return EvaluationDataset(samples=samples)


def _build_answer_dataset():
    """Retrieve contexts, generate answers, and build a RAGAS dataset."""
    retriever = get_retriever()
    llm = get_llm()
    samples = []
    for item in EVAL_QUESTIONS:
        docs = retriever.invoke(item["question"])
        contexts = [doc.page_content for doc in docs]

        context_block = "\n\n".join(contexts)
        prompt = (
            "Answer the following question based only on the provided context.\n\n"
            f"Context:\n{context_block}\n\n"
            f"Question: {item['question']}\n\n"
            "Answer:"
        )
        response = llm.invoke(prompt)
        answer = response.content if hasattr(response, "content") else str(response)

        samples.append(
            SingleTurnSample(
                user_input=item["question"],
                retrieved_contexts=contexts,
                response=answer,
                reference=item["ground_truth"],
            )
        )
    return EvaluationDataset(samples=samples)


def _get_evaluator_llm():
    return LangchainLLMWrapper(get_llm())


def _get_evaluator_embeddings():
    return LangchainEmbeddingsWrapper(get_embedding_model())


def _get_scores(result):
    """Extract {metric_name: avg_score} dict from EvaluationResult."""
    return dict(result._repr_dict)


def _print_results(result, title):
    """Print a formatted results table."""
    scores = _get_scores(result)
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    for metric_name, score in scores.items():
        threshold = THRESHOLDS.get(metric_name)
        status = ""
        if threshold is not None:
            status = "PASS" if score >= threshold else "WARN"
        print(f"  {metric_name:<35} {score:.4f}  {status}")
    print(f"{'=' * 60}\n")


# ---------------------------------------------------------------------------
# Pytest tests
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.slow
def test_retrieval_quality():
    """Evaluate retrieval quality: did the retriever fetch relevant chunks?"""
    dataset = _build_retrieval_dataset()
    evaluator_llm = _get_evaluator_llm()

    metrics = [
        LLMContextRecall(),
        LLMContextPrecisionWithReference(),
    ]

    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=evaluator_llm,
    )

    _print_results(result, "Retrieval Quality")

    for metric_name, score in _get_scores(result).items():
        assert math.isnan(score) or score >= 0.0, (
            f"{metric_name} returned a negative score: {score}"
        )


@pytest.mark.integration
@pytest.mark.slow
def test_answer_quality():
    """Evaluate answer quality: did the LLM produce correct answers?"""
    dataset = _build_answer_dataset()
    evaluator_llm = _get_evaluator_llm()
    evaluator_embeddings = _get_evaluator_embeddings()

    metrics = [
        Faithfulness(),
        FactualCorrectness(),
        ResponseRelevancy(),
        SemanticSimilarity(),
    ]

    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
    )

    _print_results(result, "Answer Quality")

    for metric_name, score in _get_scores(result).items():
        assert math.isnan(score) or score >= 0.0, (
            f"{metric_name} returned a negative score: {score}"
        )


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Run RAGAS evaluation")
    parser.add_argument(
        "--mode",
        choices=["retrieval", "answer", "both"],
        default="both",
        help="Which evaluation to run (default: both)",
    )
    args = parser.parse_args()

    if args.mode in ("retrieval", "both"):
        print("\n>>> Building retrieval dataset ...")
        dataset = _build_retrieval_dataset()
        evaluator_llm = _get_evaluator_llm()
        metrics = [
            LLMContextRecall(),
            LLMContextPrecisionWithReference(),
        ]
        result = evaluate(dataset=dataset, metrics=metrics, llm=evaluator_llm)
        _print_results(result, "Retrieval Quality")

    if args.mode in ("answer", "both"):
        print("\n>>> Building answer dataset (generating LLM responses) ...")
        dataset = _build_answer_dataset()
        evaluator_llm = _get_evaluator_llm()
        evaluator_embeddings = _get_evaluator_embeddings()
        metrics = [
            Faithfulness(),
            FactualCorrectness(),
            ResponseRelevancy(),
            SemanticSimilarity(),
        ]
        result = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=evaluator_llm,
            embeddings=evaluator_embeddings,
        )
        _print_results(result, "Answer Quality")

    print("Done.")


if __name__ == "__main__":
    main()

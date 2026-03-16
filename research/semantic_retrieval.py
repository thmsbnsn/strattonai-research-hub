from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from .local_ai_config import LocalAIConfig
from .local_ai_context import format_win_rate
from .local_ai_models import ContextCitation, LocalAIContext


LOGGER = logging.getLogger("research.semantic_retrieval")


@dataclass(frozen=True, slots=True)
class SemanticCandidate:
    kind: str
    title: str
    detail: str
    text: str
    ticker: str | None
    ordinal: int

    def to_citation(self) -> ContextCitation:
        return ContextCitation(
            kind=self.kind,
            title=self.title,
            detail=self.detail,
            ticker=self.ticker,
        )


@dataclass(frozen=True, slots=True)
class SemanticGroundingResult:
    prompt: str
    citations: list[ContextCitation]
    notes: list[str]


def build_semantic_candidates(context: LocalAIContext) -> list[SemanticCandidate]:
    candidates: list[SemanticCandidate] = []

    def append_candidate(*, kind: str, title: str, detail: str, text: str, ticker: str | None) -> None:
        candidates.append(
            SemanticCandidate(
                kind=kind,
                title=title,
                detail=detail,
                text=text,
                ticker=ticker,
                ordinal=len(candidates),
            )
        )

    if context.profile:
        profile_parts = [
            f"sector {context.profile['sector']}" if context.profile.get("sector") else None,
            f"industry {context.profile['industry']}" if context.profile.get("industry") else None,
            f"market cap {context.profile['market_cap']}" if context.profile.get("market_cap") else None,
            f"employees {context.profile['employees']}" if context.profile.get("employees") else None,
        ]
        profile_detail = ", ".join(part for part in profile_parts if part) or "Stored company profile data"
        append_candidate(
            kind="profile",
            title=f"{context.company_name or context.ticker or 'Company'} profile",
            detail=profile_detail,
            text=f"Company profile for {context.company_name or context.ticker}: {profile_detail}",
            ticker=context.ticker,
        )

    if context.latest_price:
        append_candidate(
            kind="price",
            title=f"{context.latest_price['ticker']} latest close",
            detail=(
                f"close {float(context.latest_price['close']):.2f} on {context.latest_price['trade_date']}"
            ),
            text=(
                f"Latest stored price for {context.latest_price['ticker']} is close "
                f"{float(context.latest_price['close']):.2f} on {context.latest_price['trade_date']} "
                f"with volume {context.latest_price.get('volume') or 'n/a'}."
            ),
            ticker=context.latest_price.get("ticker"),
        )

    for signal in context.signals:
        target_ticker = signal.get("target_ticker") or signal.get("primary_ticker")
        detail = (
            f"score {float(signal['score']):.1f}, {signal['confidence_band']} confidence, "
            f"sample n={int(signal['sample_size'])}"
        )
        text = (
            f"Signal for {target_ticker or 'market'} from {signal['event_category']} over {signal['horizon']}. "
            f"Score {float(signal['score']):.1f}. Confidence {signal['confidence_band']}. "
            f"Sample size {int(signal['sample_size'])}. Avg return {float(signal['avg_return']):.2f}%. "
            f"Median return {float(signal['median_return']):.2f}%. Win rate {format_win_rate(signal['win_rate'])}. "
            f"Evidence summary: {signal.get('evidence_summary') or 'n/a'}."
        )
        append_candidate(
            kind="signal",
            title=f"{signal['event_category']} · {signal['horizon']}",
            detail=detail,
            text=text,
            ticker=target_ticker,
        )

    for event in context.events:
        detail = str(event["headline"])
        text = (
            f"Recent event for {event['ticker']}: {event['category']} with sentiment {event.get('sentiment') or 'unknown'} "
            f"at {event.get('timestamp')}. Headline: {event['headline']}."
        )
        append_candidate(
            kind="event",
            title=f"{event['ticker']} · {event['category']}",
            detail=detail,
            text=text,
            ticker=event.get("ticker"),
        )

    for relationship in context.relationships:
        detail = (
            f"{relationship['relationship_type']} | strength {float(relationship['strength']):.2f}"
        )
        text = (
            f"Company relationship: {relationship['source_ticker']} {relationship.get('source_name') or ''} "
            f"to {relationship['target_ticker']} {relationship.get('target_name') or ''}. "
            f"Type {relationship['relationship_type']}. Strength {float(relationship['strength']):.2f}."
        )
        append_candidate(
            kind="relationship",
            title=f"{relationship['source_ticker']} → {relationship['target_ticker']}",
            detail=detail,
            text=text,
            ticker=relationship.get("target_ticker"),
        )

    for study in context.studies:
        related_label = study.get("related_ticker") or study.get("primary_ticker")
        detail = (
            f"{study['study_target_type']} study, avg {float(study['avg_return']):.2f}%, "
            f"win rate {format_win_rate(study['win_rate'])}, n={int(study['sample_size'])}"
        )
        text = (
            f"Event study for {study['event_category']} over {study['horizon']} using "
            f"{study['study_target_type']} target type. Primary ticker {study.get('primary_ticker') or 'n/a'}. "
            f"Related ticker {study.get('related_ticker') or 'n/a'}. Relationship type {study.get('relationship_type') or 'n/a'}. "
            f"Average return {float(study['avg_return']):.2f}%. Median return {float(study['median_return']):.2f}%. "
            f"Win rate {format_win_rate(study['win_rate'])}. Sample size {int(study['sample_size'])}."
        )
        append_candidate(
            kind="study",
            title=f"{study['event_category']} · {study['horizon']}",
            detail=detail,
            text=text,
            ticker=related_label,
        )

    for insight in context.insights:
        detail = (
            f"{insight['confidence']} confidence, n={int(insight['event_count'])}"
        )
        append_candidate(
            kind="insight",
            title=str(insight["title"]),
            detail=detail,
            text=(
                f"Research insight {insight['title']}. Summary: {insight['summary']}. "
                f"Confidence {insight['confidence']}. Event count {int(insight['event_count'])}."
            ),
            ticker=context.ticker,
        )

    return candidates


def build_semantic_prompt(
    *,
    context: LocalAIContext,
    query: str,
    selected_candidates: list[SemanticCandidate],
) -> str:
    sections: list[str] = []

    if context.ticker:
        sections.append(f"Focus ticker: {context.ticker}")
    if context.company_name:
        sections.append(f"Company name: {context.company_name}")

    sections.append(f"User request: {query}")

    if selected_candidates:
        sections.append(
            "Most relevant structured context:\n"
            + "\n".join(
                f"- [{candidate.kind}] {candidate.text}"
                for candidate in selected_candidates
            )
        )

    if context.notes:
        sections.append("Context notes:\n" + "\n".join(f"- {note}" for note in context.notes))

    return "\n\n".join(section for section in sections if section.strip())


class SemanticRetriever:
    def __init__(self, config: LocalAIConfig):
        self.config = config
        self._embed_tokenizer = None
        self._embed_model = None
        self._rerank_tokenizer = None
        self._rerank_model = None
        self._torch = None

    def ground(self, query: str, context: LocalAIContext) -> SemanticGroundingResult:
        candidates = build_semantic_candidates(context)
        if not candidates:
            return SemanticGroundingResult(
                prompt=build_semantic_prompt(context=context, query=query, selected_candidates=[]),
                citations=[],
                notes=["Semantic retrieval found no structured candidate documents."],
            )

        ranked = self._rank_candidates(query, candidates)
        selected_candidates = [candidate for candidate, _, _ in ranked[: self.config.semantic_top_k]]
        prompt = build_semantic_prompt(
            context=context,
            query=query,
            selected_candidates=selected_candidates,
        )
        citations = [candidate.to_citation() for candidate in selected_candidates]
        notes = [
            f"Semantic retrieval evaluated {len(candidates)} structured candidates and selected {len(selected_candidates)} for grounding.",
            f"Semantic device: {self.config.semantic_device}.",
        ]
        return SemanticGroundingResult(prompt=prompt, citations=citations, notes=notes)

    def _rank_candidates(
        self,
        query: str,
        candidates: list[SemanticCandidate],
    ) -> list[tuple[SemanticCandidate, float, float]]:
        embedding_scores = self._embedding_scores(query, candidates)
        rerank_limit = min(self.config.semantic_rerank_limit, len(candidates))
        top_embedding = sorted(
            zip(candidates, embedding_scores),
            key=lambda item: (-item[1], item[0].ordinal),
        )[:rerank_limit]

        rerank_scores = self._rerank_scores(query, [candidate for candidate, _ in top_embedding])
        ranked = [
            (candidate, embedding_score, rerank_score)
            for (candidate, embedding_score), rerank_score in zip(top_embedding, rerank_scores)
        ]
        ranked.sort(key=lambda item: (-item[2], -item[1], item[0].ordinal))
        return ranked

    def _embedding_scores(self, query: str, candidates: list[SemanticCandidate]) -> list[float]:
        torch = self._get_torch()
        tokenizer, model = self._load_embedder()

        query_embedding = self._encode_texts(tokenizer, model, [f"Query: {query}"])[0]
        document_embeddings = self._encode_texts(
            tokenizer,
            model,
            [f"Document: {candidate.text}" for candidate in candidates],
        )
        query_vector = query_embedding.unsqueeze(1)
        scores = torch.matmul(document_embeddings, query_vector).squeeze(1)
        return [float(score) for score in scores.cpu().tolist()]

    def _rerank_scores(self, query: str, candidates: list[SemanticCandidate]) -> list[float]:
        if not candidates:
            return []

        torch = self._get_torch()
        tokenizer, model = self._load_reranker()
        encoded = tokenizer(
            [query] * len(candidates),
            [candidate.text for candidate in candidates],
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        encoded = {key: value.to(self.config.semantic_device) for key, value in encoded.items()}

        with torch.inference_mode():
            logits = model(**encoded).logits.squeeze(-1)

        if logits.ndim == 0:
            return [float(logits.item())]
        return [float(score) for score in logits.detach().cpu().tolist()]

    def _encode_texts(self, tokenizer, model, texts: list[str]):
        torch = self._get_torch()
        encoded = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        encoded = {key: value.to(self.config.semantic_device) for key, value in encoded.items()}

        with torch.inference_mode():
            outputs = model(**encoded)
            hidden_state = outputs.last_hidden_state
            attention_mask = encoded["attention_mask"].unsqueeze(-1)
            pooled = (hidden_state * attention_mask).sum(dim=1) / attention_mask.sum(dim=1).clamp(min=1)
            normalized = torch.nn.functional.normalize(pooled, p=2, dim=1)
        return normalized.detach().cpu()

    def _load_embedder(self):
        if self._embed_tokenizer is None or self._embed_model is None:
            from transformers import AutoModel, AutoTokenizer

            LOGGER.info("Loading semantic embedder from %s", self.config.bge_model_dir)
            self._embed_tokenizer = AutoTokenizer.from_pretrained(str(self.config.bge_model_dir))
            self._embed_model = AutoModel.from_pretrained(str(self.config.bge_model_dir))
            self._embed_model.to(self.config.semantic_device)
            self._embed_model.eval()
        return self._embed_tokenizer, self._embed_model

    def _load_reranker(self):
        if self._rerank_tokenizer is None or self._rerank_model is None:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            LOGGER.info("Loading semantic reranker from %s", self.config.reranker_model_dir)
            self._rerank_tokenizer = AutoTokenizer.from_pretrained(str(self.config.reranker_model_dir))
            self._rerank_model = AutoModelForSequenceClassification.from_pretrained(
                str(self.config.reranker_model_dir)
            )
            self._rerank_model.to(self.config.semantic_device)
            self._rerank_model.eval()
        return self._rerank_tokenizer, self._rerank_model

    def _get_torch(self):
        if self._torch is None:
            import torch

            if self.config.semantic_device.startswith("cuda") and not torch.cuda.is_available():
                LOGGER.warning(
                    "Semantic device %s requested but CUDA is unavailable. Falling back to cpu.",
                    self.config.semantic_device,
                )
                self.config = LocalAIConfig(
                    host=self.config.host,
                    port=self.config.port,
                    ollama_url=self.config.ollama_url,
                    ollama_model=self.config.ollama_model,
                    ollama_timeout_seconds=self.config.ollama_timeout_seconds,
                    semantic_device="cpu",
                    semantic_top_k=self.config.semantic_top_k,
                    semantic_rerank_limit=self.config.semantic_rerank_limit,
                    models_dir=self.config.models_dir,
                    bge_model_dir=self.config.bge_model_dir,
                    reranker_model_dir=self.config.reranker_model_dir,
                )
            self._torch = torch
        return self._torch

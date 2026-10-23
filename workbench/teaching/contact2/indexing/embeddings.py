"""Create document and question vectors with the OpenAI SDK and record actual usage."""

import math

from ...observability_reference import stage
from ...provider_connection import provider_name
from ..config import RagFailure


class EmbeddingModel:
    def __init__(self, client, config):
        self.client = client
        self.config = config
        self.embedding_calls = 0
        self.embedding_tokens = 0
        self.usage_complete = True

    def embed(self, inputs):
        tokens = self.embedding_tokens
        with stage("query_or_document_embedding", "embedding", self.config.model) as measurement:
            result = self.embed_request(inputs)
            if self.usage_complete:
                measurement.update(input_tokens=self.embedding_tokens - tokens, output_tokens=0)
            return result

    def embed_request(self, inputs):
        self.embedding_calls += 1  # Attempts, including failures; SDK retries are disabled.
        try:
            response = self.client.embeddings.create(
                model=self.config.model,
                dimensions=self.config.dimensions,
                input=inputs,
                encoding_format="float",
            )
        except Exception:
            self.usage_complete = False
            raise
        usage = getattr(response, "usage", None)
        if usage is not None:
            self.embedding_tokens += usage.prompt_tokens
        else:
            self.usage_complete = False
        rows = sorted(response.data, key=lambda r: r.index)
        if [r.index for r in rows] != list(range(len(inputs))):
            raise RagFailure("invalid_embedding_indices")
        vectors = [r.embedding for r in rows]
        if any(
            len(v) != self.config.dimensions
            or any(not math.isfinite(x) for x in v)
            or not any(x != 0 for x in v)
            for v in vectors
        ):
            raise RagFailure("invalid_embedding_vector")
        accepted_models = {self.config.model}
        if provider_name(self.client) == "openrouter" and self.config.model.startswith("openai/"):
            # Live OpenRouter returns the upstream bare ID for its namespaced route.
            # Accept only the exact same model; never match an arbitrary suffix/provider.
            accepted_models.add(self.config.model.removeprefix("openai/"))
        if response.model not in accepted_models:
            raise RagFailure("embedding_model_mismatch")
        return vectors

    def embed_passages(self, passages, cached, *, allow_embeddings=True):
        """Embed only missing passages, in bounded batches. Removal never spends tokens."""
        vectors = dict(cached)
        missing = [p for p in passages if p["chunk_id"] not in vectors]
        if missing and not allow_embeddings:
            raise RagFailure("cached_vectors_missing")
        for offset in range(0, len(missing), 32):
            batch = missing[offset : offset + 32]
            embeddings = self.embed([p["excerpt"] for p in batch])
            vectors.update(zip([p["chunk_id"] for p in batch], embeddings, strict=True))
        return vectors

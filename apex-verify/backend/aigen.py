from __future__ import annotations

from typing import Dict

import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class AIImageDetector:
    """
    Wrapper around an open-source HuggingFace model for AI-generated image detection.

    We use `capcheck/ai-image-detection`, a ViT-based classifier trained on CIFAKE.
    The model outputs logits for two classes: [real, fake]. We interpret the
    softmax probability of the 'fake' class as the ai_gen_score in [0, 1].
    """

    def __init__(self, model_id: str = "capcheck/ai-image-detection") -> None:
        self.processor = AutoImageProcessor.from_pretrained(model_id)
        self.model = AutoModelForImageClassification.from_pretrained(model_id).to(DEVICE)
        self.model.eval()

    def predict(self, image: Image.Image) -> Dict:
        inputs = self.processor(images=image, return_tensors="pt").to(DEVICE)

        with torch.no_grad():
            outputs = self.model(**inputs)

        logits = outputs.logits.detach().cpu().numpy()[0]
        probs = np.exp(logits) / np.exp(logits).sum()

        # Assume index 1 is "fake" (AI-generated) as per CIFAKE models
        if len(probs) == 2:
            ai_prob = float(probs[1])
        else:
            # Fallback: use 1 - prob of the class named "real" if available
            id2label = getattr(self.model.config, "id2label", {})
            real_idx = None
            for idx, label in id2label.items():
                if str(label).lower() in {"real", "human", "authentic"}:
                    real_idx = int(idx)
                    break
            if real_idx is not None:
                ai_prob = float(1.0 - probs[real_idx])
            else:
                # Otherwise, take max probability as a proxy
                ai_prob = float(probs.max())

        ai_prob = max(0.0, min(1.0, ai_prob))

        return {
            "ai_gen_score": ai_prob,
            "raw_logits": logits.tolist(),
        }


_AI_DETECTOR: AIImageDetector | None = None


def get_ai_detector() -> AIImageDetector:
    global _AI_DETECTOR
    if _AI_DETECTOR is None:
        _AI_DETECTOR = AIImageDetector()
    return _AI_DETECTOR


__all__ = ["AIImageDetector", "get_ai_detector"]


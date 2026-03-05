from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import torch
from PIL import Image
from transformers import RTDetrForObjectDetection, RTDetrImageProcessor

from sam2.sam2_image_predictor import SAM2ImagePredictor


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


@dataclass
class DetectedObject:
    label: str
    score: float
    bbox: Tuple[float, float, float, float]  # x_min, y_min, x_max, y_max
    mask: np.ndarray | None


class DetectionPipeline:
    """
    Wraps RT-DETR object detection and SAM2 segmentation.
    All models are loaded on CPU and reused across requests.
    """

    def __init__(
        self,
        rtdetr_model_id: str = "PekingU/rtdetr_r50vd",
        sam2_model_id: str = "facebook/sam2-hiera-tiny",
    ) -> None:
        self.rtdetr_processor = RTDetrImageProcessor.from_pretrained(rtdetr_model_id)
        self.rtdetr_model = RTDetrForObjectDetection.from_pretrained(rtdetr_model_id).to(DEVICE)
        # SAM2 image predictor with HF weights
        # NOTE: SAM2ImagePredictor internally handles the device; when using CUDA
        # it will leverage the available GPU for faster mask prediction.
        self.sam2_predictor = SAM2ImagePredictor.from_pretrained(sam2_model_id, device=DEVICE.type)

    def detect_objects(self, image: Image.Image, score_threshold: float = 0.4) -> List[DetectedObject]:
        """
        Run RT-DETR to obtain object detections.
        """
        self.rtdetr_model.eval()
        inputs = self.rtdetr_processor(images=image, return_tensors="pt").to(DEVICE)

        with torch.no_grad():
            outputs = self.rtdetr_model(**inputs)

        target_sizes = torch.tensor([(image.height, image.width)], device=DEVICE)
        results = self.rtdetr_processor.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=score_threshold
        )[0]

        detections: List[DetectedObject] = []
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            detections.append(
                DetectedObject(
                    label=self.rtdetr_model.config.id2label[int(label)],
                    score=float(score),
                    bbox=tuple(map(float, box.tolist())),
                    mask=None,
                )
            )
        return detections

    def segment_with_sam2(self, image: Image.Image, detections: List[DetectedObject]) -> Tuple[List[DetectedObject], float, np.ndarray | None]:
        """
        Use SAM2 to refine object regions into segmentation masks.

        Strategy:
        - For each detection, create a bounding box prompt.
        - Run predictor and attach mask to each DetectedObject.
        - Compute a global SAM2 confidence as the max mask score.
        """
        # SAM2 expects numpy RGB image (H, W, 3)
        np_img = np.array(image)
        self.sam2_predictor.set_image(np_img)

        global_mask: np.ndarray | None = None
        sam2_confidence = 0.0

        for det in detections:
            x_min, y_min, x_max, y_max = det.bbox
            box = np.array([[x_min, y_min, x_max, y_max]], dtype=np.float32)
            masks, scores, _ = self.sam2_predictor.predict(box=box, multimask_output=True)

            if masks is None or len(masks) == 0:
                continue

            # Choose the mask with highest score
            best_idx = int(np.argmax(scores))
            best_mask = masks[best_idx]
            best_score = float(scores[best_idx])

            det.mask = best_mask.astype(bool)
            sam2_confidence = max(sam2_confidence, best_score)

            if global_mask is None:
                global_mask = det.mask.copy()
            else:
                global_mask = np.logical_or(global_mask, det.mask)

        return detections, float(sam2_confidence), global_mask

    def run(self, image: Image.Image) -> Dict:
        """
        End-to-end: RT-DETR + SAM2.

        Returns a dict:
        {
          "detections": [...],
          "sam2_confidence": float,
          "combined_mask": np.ndarray | None
        }
        """
        detections = self.detect_objects(image)
        detections, sam2_confidence, combined_mask = self.segment_with_sam2(image, detections)

        serializable_dets = []
        for det in detections:
            serializable_dets.append(
                {
                    "label": det.label,
                    "score": det.score,
                    "bbox": det.bbox,
                }
            )

        return {
            "detections": serializable_dets,
            "sam2_confidence": sam2_confidence,
            "combined_mask": combined_mask,
        }


# Singleton detector to reuse models across requests
_DETECTION_PIPELINE: DetectionPipeline | None = None


def get_detection_pipeline() -> DetectionPipeline:
    global _DETECTION_PIPELINE
    if _DETECTION_PIPELINE is None:
        _DETECTION_PIPELINE = DetectionPipeline()
    return _DETECTION_PIPELINE


__all__ = ["DetectedObject", "DetectionPipeline", "get_detection_pipeline"]


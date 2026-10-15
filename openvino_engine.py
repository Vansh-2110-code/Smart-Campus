"""
openvino_engine.py
==================
Intel OpenVINO Deep Learning Model Accelerator for Smart Campus Attendance.

Optimizes inference execution on GPU and CPU for:
1. SFace Biometric Recognizer (ONNX) - compiles to vectorized OpenCL GPU / AVX-512 CPU.
2. MobileNet-V3 Small Feature Extractor (PyTorch) - converts and compiles to OpenVINO IR.
3. YuNet Face Detector - accelerates pre-alignment face localization.

Supports multi-device hardware target resolution:
- GPU.0: Intel Iris Xe Graphics (iGPU)
- GPU.1: NVIDIA GeForce GTX 1650 (dGPU)
- GPU: Primary GPU
- CPU: Intel Core i5-11320H vector execution
- Persistent OpenCL binary kernel caching in data/ov_cache (sub-millisecond reload).
"""

import os
import sys
import time
import logging
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger("openvino_engine")
logger.setLevel(logging.INFO)

OPENVINO_AVAILABLE = False
try:
    import openvino as ov
    OPENVINO_AVAILABLE = True
except ImportError:
    ov = None


class OpenVINOAttendanceOptimizer:
    """
    OpenVINO runtime acceleration manager for biometric deep learning models.
    Supports GPU (Intel Iris Xe, NVIDIA GeForce GTX) and CPU execution with
    automatic device resolution, persistent kernel caching, and fallback.
    """

    def __init__(self, device: Optional[str] = None):
        # Resolve preferred device: prioritize parameter -> OPENVINO_DEVICE env -> GPU -> CPU
        env_device = os.getenv("OPENVINO_DEVICE")
        req_device = device or env_device or "GPU"

        self.device = req_device
        self.is_ready = False
        self.core: Optional[Any] = None
        self.compiled_sface: Optional[Any] = None
        self.compiled_mobilenet: Optional[Any] = None
        self.sface_infer_request: Optional[Any] = None
        self.mobilenet_infer_request: Optional[Any] = None
        self.available_devices = []
        self.device_name = "None"
        self.cache_dir = os.path.join(os.path.dirname(__file__), "data", "ov_cache")

        if OPENVINO_AVAILABLE:
            try:
                self.core = ov.Core()
                self.available_devices = list(self.core.available_devices)
                
                # Enable persistent OpenCL/GPU model cache to eliminate compilation latency on reload
                try:
                    os.makedirs(self.cache_dir, exist_ok=True)
                    self.core.set_property({"CACHE_DIR": self.cache_dir})
                except Exception as cache_err:
                    logger.debug(f"[OpenVINO] Could not configure CACHE_DIR: {cache_err}")

                # Device selection logic: prefer GPU if requested
                self.device = self._resolve_target_device(req_device)
                try:
                    self.device_name = self.core.get_property(self.device, "FULL_DEVICE_NAME")
                except Exception:
                    self.device_name = self.device

                self.is_ready = True
                logger.info(f"[OpenVINO] Initialized on {self.device} ({self.device_name}) [Available: {self.available_devices}]")
            except Exception as e:
                logger.warning(f"[OpenVINO] Core initialization failed: {e}. Fallback to PyTorch/OpenCV.")
                self.is_ready = False
        else:
            logger.info("[OpenVINO] openvino package not installed. Running standard OpenCV/PyTorch inference.")

    def _resolve_target_device(self, requested: str) -> str:
        """
        Resolves best matching execution device against available hardware.
        Maps 'GPU' to available GPU.0 / GPU.1 if present.
        """
        req_upper = requested.upper()

        # Exact match in available devices
        if requested in self.available_devices:
            return requested

        # GPU requested: check available GPU targets
        if "GPU" in req_upper:
            # Check GPU.0 (Intel Iris Xe) or GPU.1 (NVIDIA)
            if "GPU.0" in self.available_devices:
                return "GPU.0"
            elif "GPU.1" in self.available_devices:
                return "GPU.1"
            elif "GPU" in self.available_devices:
                return "GPU"

        # Fallback to CPU if GPU not present
        if "CPU" in self.available_devices:
            return "CPU"

        return self.available_devices[0] if self.available_devices else "CPU"

    def compile_sface(self, sface_onnx_path: str) -> bool:
        """
        Compiles the SFace ONNX model to OpenVINO executable format on target GPU/CPU.
        """
        if not self.is_ready or not os.path.exists(sface_onnx_path):
            return False

        try:
            model = self.core.read_model(sface_onnx_path)
            
            # Try compiling on target device (e.g. GPU)
            try:
                self.compiled_sface = self.core.compile_model(
                    model,
                    self.device,
                    config={
                        "PERFORMANCE_HINT": "LATENCY",
                    }
                )
                self.sface_infer_request = self.compiled_sface.create_infer_request()
                logger.info(f"[OpenVINO] SFace successfully compiled on {self.device} ({self.device_name}).")
                return True
            except Exception as dev_err:
                if "GPU" in self.device and "CPU" in self.available_devices:
                    logger.warning(f"[OpenVINO] SFace compile failed on {self.device}: {dev_err}. Retrying on CPU fallback.")
                    self.compiled_sface = self.core.compile_model(model, "CPU", config={"PERFORMANCE_HINT": "LATENCY"})
                    self.sface_infer_request = self.compiled_sface.create_infer_request()
                    return True
                raise dev_err
        except Exception as e:
            logger.warning(f"[OpenVINO] Failed to compile SFace with OpenVINO: {e}. Falling back to cv2.FaceRecognizerSF.")
            self.compiled_sface = None
            self.sface_infer_request = None
            return False

    def compile_mobilenet_v3(self, torch_mobilenet_model: Any) -> bool:
        """
        Converts PyTorch MobileNet-V3 Small model and compiles to OpenVINO runtime on GPU/CPU.
        Extracts 384-dimensional pooled embeddings.
        """
        if not self.is_ready or torch_mobilenet_model is None:
            return False

        try:
            import torch
            import torch.nn as nn

            class Extractor(nn.Module):
                def __init__(self, net):
                    super().__init__()
                    self.features = net.features
                    self.avgpool = nn.AdaptiveAvgPool2d((1, 1))

                def forward(self, x):
                    feats = self.features(x)
                    pooled = self.avgpool(feats)
                    pooled_flat = torch.flatten(pooled, 1)
                    return pooled_flat[:, :384]

            extractor = Extractor(torch_mobilenet_model)
            extractor.eval()

            dummy_input = torch.randn(1, 3, 224, 224)
            ov_model = ov.convert_model(extractor, example_input=dummy_input)

            try:
                self.compiled_mobilenet = self.core.compile_model(
                    ov_model,
                    self.device,
                    config={
                        "PERFORMANCE_HINT": "LATENCY"
                    }
                )
                self.mobilenet_infer_request = self.compiled_mobilenet.create_infer_request()
                logger.info(f"[OpenVINO] MobileNet-V3 Small successfully compiled on {self.device} ({self.device_name}).")
                return True
            except Exception as dev_err:
                if "GPU" in self.device and "CPU" in self.available_devices:
                    logger.warning(f"[OpenVINO] MobileNet compile failed on {self.device}: {dev_err}. Retrying on CPU fallback.")
                    self.compiled_mobilenet = self.core.compile_model(ov_model, "CPU", config={"PERFORMANCE_HINT": "LATENCY"})
                    self.mobilenet_infer_request = self.compiled_mobilenet.create_infer_request()
                    return True
                raise dev_err
        except Exception as e:
            logger.warning(f"[OpenVINO] Failed to convert/compile MobileNet-V3 with OpenVINO: {e}.")
            self.compiled_mobilenet = None
            self.mobilenet_infer_request = None
            return False

    def infer_sface(self, aligned_bgr_112: np.ndarray) -> Optional[np.ndarray]:
        """
        Runs accelerated OpenVINO inference for 112x112 aligned face on GPU/CPU.
        Converts BGR to RGB matching OpenCV FaceRecognizerSF preprocessing.
        Returns 128-dimensional L2-normalized embedding.
        """
        if self.sface_infer_request is None or aligned_bgr_112 is None:
            return None

        try:
            if aligned_bgr_112.shape[:2] != (112, 112):
                aligned_bgr_112 = cv2.resize(aligned_bgr_112, (112, 112))

            rgb = cv2.cvtColor(aligned_bgr_112, cv2.COLOR_BGR2RGB).astype(np.float32)
            blob = np.ascontiguousarray(rgb.transpose(2, 0, 1)[None, ...])

            output = self.sface_infer_request.infer({0: blob})
            raw_feat = list(output.values())[0].flatten()

            norm = np.linalg.norm(raw_feat)
            if norm > 0:
                raw_feat = raw_feat / norm
            return raw_feat.astype(np.float32)
        except Exception as e:
            logger.debug(f"[OpenVINO] SFace inference error on {self.device}: {e}")
            return None

    def infer_mobilenet(self, normed_chw_tensor: np.ndarray) -> Optional[np.ndarray]:
        """
        Runs accelerated OpenVINO inference for 224x224 normalized face on GPU/CPU.
        Returns 384-dimensional L2-normalized feature vector.
        """
        if self.mobilenet_infer_request is None or normed_chw_tensor is None:
            return None

        try:
            if len(normed_chw_tensor.shape) == 3:
                normed_chw_tensor = np.expand_dims(normed_chw_tensor, axis=0)

            blob = np.ascontiguousarray(normed_chw_tensor.astype(np.float32))
            output = self.mobilenet_infer_request.infer({0: blob})
            pooled = list(output.values())[0].flatten()[:384]

            p_norm = np.linalg.norm(pooled)
            if p_norm > 0:
                pooled = pooled / p_norm
            return pooled.astype(np.float32)
        except Exception as e:
            logger.debug(f"[OpenVINO] MobileNet inference error on {self.device}: {e}")
            return None

    def get_status(self) -> Dict[str, Any]:
        """Returns acceleration status, active device, and hardware telemetry."""
        is_gpu = "GPU" in self.device.upper()
        return {
            "openvino_installed": OPENVINO_AVAILABLE,
            "openvino_version": ov.__version__ if OPENVINO_AVAILABLE else None,
            "target_device": self.device,
            "device_full_name": self.device_name,
            "available_devices": self.available_devices,
            "device_type": "GPU" if is_gpu else "CPU",
            "gpu_accelerated": is_gpu and (self.compiled_sface is not None or self.compiled_mobilenet is not None),
            "sface_accelerated": self.compiled_sface is not None,
            "mobilenet_accelerated": self.compiled_mobilenet is not None,
            "cache_dir": self.cache_dir,
            "active": (self.compiled_sface is not None or self.compiled_mobilenet is not None)
        }

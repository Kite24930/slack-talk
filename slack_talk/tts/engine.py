"""TADA TTS engine with MPS acceleration.

TADA (Text-Aligned Diffusion Audio) 3B-ML モデルを使用したテキスト音声合成エンジン。
macOS の Metal Performance Shaders (MPS) によるGPUアクセラレーションに対応。
"""

from __future__ import annotations

import asyncio
import logging
import os
from functools import partial
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# MPS未対応オペレーション発生時のCPUフォールバック
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

# TADA model identifier on HuggingFace Hub
_DEFAULT_MODEL_ID = "HumeAI/TADA"


class TTSEngine:
    """TADA TTS エンジン。

    テキストを音声に変換する。TADA 3B-ML モデルを使用し、
    MPS (Metal Performance Shaders) による GPU アクセラレーションに対応。

    Parameters
    ----------
    reference_audio_path : str | None
        リファレンス音声ファイルのパス。音声クローニングに使用。
        None の場合、日本語のビルトインサンプルを使用。
    reference_text : str | None
        リファレンス音声のトランスクリプト。
        None の場合、日本語サンプルのデフォルトテキストを使用。
    model_id : str
        HuggingFace Hub 上のモデル ID。
    flow_matching_steps : int
        フローマッチングのステップ数。大きいほど品質が上がるが遅くなる。
    volume : float
        出力音量の倍率 (0.0 - 1.0)。
    language : str
        エンコーダーのアライナー言語。日本語は "ja"。
    """

    def __init__(
        self,
        reference_audio_path: str | None = None,
        reference_text: str | None = None,
        model_id: str = _DEFAULT_MODEL_ID,
        flow_matching_steps: int = 10,
        volume: float = 0.8,
        language: str = "ja",
    ) -> None:
        self._reference_audio_path = reference_audio_path
        self._reference_text = reference_text
        self._model_id = model_id
        self._flow_matching_steps = flow_matching_steps
        self._volume = volume
        self._language = language
        self._model = None
        self._encoder = None
        self._prompt = None
        self._sample_rate = 24000
        self._device: str = "cpu"

    @property
    def name(self) -> str:
        """エンジン名。"""
        return "TTSEngine"

    @property
    def sample_rate(self) -> int:
        """出力音声のサンプリングレート (Hz)。"""
        return self._sample_rate

    async def start(self) -> None:
        """モデルをロードしてエンジンを起動する。

        初回呼び出し時に HuggingFace Hub からモデルをダウンロードするため、
        時間がかかる場合がある。
        """
        logger.info("Loading TADA model (this may take a moment)...")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model)
        logger.info("TADA model loaded successfully on device: %s", self._device)

    def _load_model(self) -> None:
        """モデルとエンコーダーをロードする (同期処理)。"""
        import torch
        import torchaudio
        from tada.modules.encoder import Encoder
        from tada.modules.tada import TadaForCausalLM

        # デバイス選択: MPS > CUDA > CPU
        if torch.backends.mps.is_available():
            self._device = "mps"
        elif torch.cuda.is_available():
            self._device = "cuda"
        else:
            self._device = "cpu"
        logger.info("Using device: %s", self._device)

        # モデルのロード
        model = TadaForCausalLM.from_pretrained(
            self._model_id, subfolder="llm"
        )
        model = model.to(self._device)
        # 推論モードに設定
        model.train(False)
        self._model = model

        # エンコーダーのロード (言語指定でアライナーを選択)
        encoder = Encoder.from_pretrained(
            self._model_id,
            subfolder="encoder",
            language=self._language,
        )
        encoder = encoder.to(self._device)
        encoder.train(False)
        self._encoder = encoder

        # リファレンス音声からプロンプトを生成
        self._prompt = self._build_prompt(torchaudio, torch)

    def _build_prompt(self, torchaudio, torch):
        """リファレンス音声からエンコーダープロンプトを構築する。"""
        if self._reference_audio_path:
            audio_path = self._reference_audio_path
            prompt_text = self._reference_text or ""
        else:
            # ビルトイン日本語サンプルを使用
            audio_path = self._get_builtin_sample_path()
            prompt_text = self._get_builtin_sample_text()

        if audio_path is None:
            logger.warning(
                "No reference audio available. "
                "Synthesis will proceed without voice prompt."
            )
            return None

        logger.info("Loading reference audio: %s", audio_path)
        audio, sr = torchaudio.load(audio_path)
        audio = audio.to(self._device)

        with torch.no_grad():
            prompt = self._encoder(
                audio,
                text=[prompt_text],
                audio_length=torch.tensor(
                    [audio.shape[1]], device=self._device
                ),
                sample_rate=sr,
            )
        return prompt

    @staticmethod
    def _get_builtin_sample_path() -> str | None:
        """TADA パッケージに同梱されている日本語サンプル音声のパスを取得する。"""
        try:
            import tada
            package_dir = Path(tada.__file__).parent
            sample_path = package_dir / "samples" / "ja_prompt.wav"
            if sample_path.exists():
                return str(sample_path)
        except (ImportError, AttributeError):
            pass
        return None

    @staticmethod
    def _get_builtin_sample_text() -> str:
        """TADA パッケージに同梱されている日本語サンプルのトランスクリプトを取得する。"""
        try:
            import json
            import tada
            package_dir = Path(tada.__file__).parent
            transcript_path = package_dir / "samples" / "prompt_transcripts.json"
            if transcript_path.exists():
                with open(transcript_path) as f:
                    transcripts = json.load(f)
                return transcripts.get("ja_prompt.wav", "")
        except (ImportError, json.JSONDecodeError):
            pass
        return ""

    async def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        """テキストを音声に変換する。

        Parameters
        ----------
        text : str
            合成するテキスト。

        Returns
        -------
        tuple[np.ndarray, int]
            (音声データ (float32 numpy配列), サンプリングレート)

        Raises
        ------
        RuntimeError
            モデルが未ロードの場合。
        """
        if self._model is None:
            raise RuntimeError(
                "Model not loaded. Call start() first."
            )
        loop = asyncio.get_event_loop()
        audio = await loop.run_in_executor(
            None, partial(self._synthesize_sync, text)
        )
        return audio, self._sample_rate

    def _synthesize_sync(self, text: str) -> np.ndarray:
        """テキストから音声を合成する (同期処理)。"""
        import torch
        from tada.modules.tada import InferenceOptions

        assert self._model is not None, "Model not loaded."

        inference_opts = InferenceOptions(
            num_flow_matching_steps=self._flow_matching_steps,
        )

        with torch.no_grad():
            output = self._model.generate(
                prompt=self._prompt,
                text=text,
                inference_options=inference_opts,
            )

        # output.audio は list[torch.Tensor] — 最初の要素を取得
        audio_tensor = output.audio[0].detach().cpu()
        audio_np = audio_tensor.numpy().flatten().astype(np.float32)

        # 音量調整
        audio_np = audio_np * self._volume

        return audio_np

    def update_settings(
        self,
        reference_audio_path: str | None = None,
        reference_text: str | None = None,
        flow_matching_steps: int | None = None,
        volume: float | None = None,
    ) -> None:
        """エンジン設定を更新する。

        reference_audio_path を変更した場合は、再起動 (stop -> start) が必要。

        Parameters
        ----------
        reference_audio_path : str | None
            新しいリファレンス音声パス。
        reference_text : str | None
            新しいリファレンステキスト。
        flow_matching_steps : int | None
            フローマッチングステップ数。
        volume : float | None
            音量倍率。
        """
        if flow_matching_steps is not None:
            self._flow_matching_steps = flow_matching_steps
        if volume is not None:
            self._volume = volume
        if reference_audio_path is not None:
            self._reference_audio_path = reference_audio_path
            logger.info(
                "Reference audio path updated. "
                "Restart the engine (stop -> start) to apply."
            )
        if reference_text is not None:
            self._reference_text = reference_text

    async def stop(self) -> None:
        """エンジンを停止し、モデルリソースを解放する。"""
        self._model = None
        self._encoder = None
        self._prompt = None
        logger.info("TTSEngine stopped and resources released.")

from __future__ import annotations

from terminalfx.audio.features import SilentAudioAnalyzer
from terminalfx.config.schema import ProjectConfig
from terminalfx.core.types import FramePacket, PreviewMode
from terminalfx.effects.base import EffectContext
from terminalfx.effects.stack import EffectStack
from terminalfx.media.frames import normalize_frame
from terminalfx.sources.base import SourceProvider


class RenderPipeline:
    def __init__(
        self,
        source: SourceProvider,
        effect_stack: EffectStack,
        config: ProjectConfig,
        audio: SilentAudioAnalyzer | None = None,
    ) -> None:
        self.source = source
        self.effect_stack = effect_stack
        self.config = config
        self.audio = audio or SilentAudioAnalyzer()

    def render_next(self, preview_mode: PreviewMode | None = None) -> FramePacket | None:
        packet = self.source.read()
        if packet is None:
            return None
        resolution = self.config.resolution
        frame = normalize_frame(packet.frame, resolution.width, resolution.height)
        context = EffectContext(
            resolution=resolution,
            time=packet.time,
            preview_mode=preview_mode or self.config.preview.mode,
            audio=self.audio.analyze_window(packet.time.seconds),
        )
        processed = self.effect_stack.apply(frame, context)
        return FramePacket(
            frame=processed,
            time=packet.time,
            source_name=packet.source_name,
            metadata=packet.metadata,
        )

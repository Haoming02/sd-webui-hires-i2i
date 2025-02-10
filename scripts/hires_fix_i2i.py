from modules.ui_components import InputAccordion
from modules import scripts, shared
from PIL import Image
import gradio as gr
import numpy as np
import re


class HiresI2I(scripts.Script):

    def __init__(self):
        self.key: int = None
        self.upscaled: Image.Image = None

    def title(self):
        return "Hires. Fix img2img"

    def show(self, is_img2img):
        return scripts.AlwaysVisible if is_img2img else None

    def ui(self, is_img2img):
        if not is_img2img:
            return

        with InputAccordion(value=False, label=self.title()) as enable:
            with gr.Row():
                upscaler = gr.Dropdown(
                    label="Upscaler",
                    choices=[x.name for x in shared.sd_upscalers],
                    value=shared.sd_upscalers[0].name,
                    scale=3,
                )
                ratio = gr.Slider(
                    minimum=1.0,
                    maximum=8.0,
                    step=0.5,
                    label="Resize by.",
                    value=2,
                    scale=1,
                )

            def auto_scale(upscaler: str):
                if not (match := re.search(r"(\d)[xX]|[xX](\d)", upscaler)):
                    return gr.skip()

                return gr.update(value=int(match.group(1) or match.group(2)))

            upscaler.change(
                fn=auto_scale,
                inputs=[upscaler],
                outputs=[ratio],
                show_progress="hidden",
            )

        self.paste_field_names = []
        self.infotext_fields = [
            (enable, "i2i Hires. fix"),
            (upscaler, "i2i Hr. Upscaler"),
            (ratio, "i2i Hr. Scale"),
        ]

        for _, name in self.infotext_fields:
            self.paste_field_names.append(name)

        return [enable, upscaler, ratio]

    @staticmethod
    def get_upscaler(name: str):
        for x in shared.sd_upscalers:
            if x.name == name:
                return x

        raise gr.Error(f'Could not find Upscaler "{name}"')

    def setup(
        self,
        p,
        enable: bool,
        upscaler_name: str,
        ratio: float,
        *args,
        **kwargs,
    ):
        if (not enable) or (upscaler_name == "None"):
            return

        init_image = p.init_images[0]
        key = (hash(np.asarray(init_image.getdata()).tobytes()), upscaler_name, ratio)

        if key != self.key:
            upscaler = self.get_upscaler(upscaler_name)
            self.upscaled = upscaler.scaler.upscale(
                init_image, ratio, upscaler.data_path
            )
            self.key = key

        p.init_images[0] = self.upscaled
        p.extra_generation_params.update(
            {
                "i2i Hires. fix": True,
                "i2i Hr. Upscaler": upscaler_name,
                "i2i Hr. Scale": ratio,
            }
        )

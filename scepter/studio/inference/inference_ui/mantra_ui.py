# -*- coding: utf-8 -*-
import os

import gradio as gr
from tqdm import tqdm

from scepter.modules.utils.file_system import FS
from scepter.studio.inference.inference_ui.component_names import MantraUIName
from scepter.studio.utils.uibase import UIBase

refresh_symbol = '\U0001f504'  # 🔄


class MantraUI(UIBase):
    def __init__(self, cfg, pipe_manager, is_debug=False, language='en'):
        self.cfg = cfg
        self.language = language
        self.pipe_manager = pipe_manager
        default_choices = pipe_manager.module_level_choices
        default_diffusion_model = default_choices['diffusion_model']['default']
        self.default_pipeline = pipe_manager.model_level_info[
            default_diffusion_model]['pipeline'][0]
        self.cfg_mantra = cfg.MANTRAS
        self.name_level_style, self.all_styles = self.load_all_styles()
        self.component_names = MantraUIName(language)

    def load_all_styles(self):
        all_styles = {}
        name_level_style = {}
        for one_style in tqdm(self.cfg_mantra):
            if one_style.BASE_MODEL not in name_level_style:
                name_level_style[one_style.BASE_MODEL] = {}
            if one_style.BASE_MODEL not in all_styles:
                all_styles[one_style.BASE_MODEL] = []
            if self.language == 'zh':
                name_level_style[one_style.BASE_MODEL][
                    one_style.NAME_ZH] = one_style
                all_styles[one_style.BASE_MODEL].append(one_style.NAME_ZH)
            else:
                name_level_style[one_style.BASE_MODEL][
                    one_style.NAME] = one_style
                all_styles[one_style.BASE_MODEL].append(one_style.NAME)
            # if one_style.get('IMAGE_PATH', None):
            #     one_style.IMAGE_PATH = FS.get_from(one_style.IMAGE_PATH)
        return name_level_style, all_styles

    def create_ui(self, *args, **kwargs):
        with gr.Row(equal_height=True):
            with gr.Column(scale=1):
                with gr.Group(visible=True):
                    with gr.Row(equal_height=True):
                        self.style = gr.Dropdown(
                            label=self.component_names.mantra_styles,
                            choices=self.all_styles[self.default_pipeline],
                            value=None,
                            multiselect=True,
                            interactive=True)
                    with gr.Row(equal_height=True):
                        with gr.Column(scale=1):
                            self.style_name = gr.Text(
                                value='',
                                label=self.component_names.style_name)
                        with gr.Column(scale=1):
                            self.style_source = gr.Text(
                                value='',
                                label=self.component_names.style_source)
                        with gr.Column(scale=1):
                            self.style_desc = gr.Text(
                                value='',
                                label=self.component_names.style_desc)
                    with gr.Row(equal_height=True):
                        self.style_prompt = gr.Text(
                            value='',
                            label=self.component_names.style_prompt,
                            lines=4)
                    with gr.Row(equal_height=True):
                        self.style_negative_prompt = gr.Text(
                            value='',
                            label=self.component_names.style_negative_prompt,
                            lines=4)
            with gr.Column(scale=1):
                with gr.Group(visible=True):
                    with gr.Row(equal_height=True):
                        self.style_template = gr.Text(
                            value='',
                            label=self.component_names.style_template,
                            lines=2)
                    with gr.Row(equal_height=True):
                        self.style_negative_template = gr.Text(
                            value='',
                            label=self.component_names.style_negative_template,
                            lines=2)
                    with gr.Row(equal_height=True):
                        self.style_example = gr.Image(
                            label=self.component_names.style_example,
                            source='upload',
                            value=None,
                            interactive=False)
                    with gr.Row(equal_height=True):
                        self.style_example_prompt = gr.Text(
                            value='',
                            label=self.component_names.style_example_prompt,
                            lines=2)

    def set_callbacks(self, model_manage_ui):
        def change_style(style, diffusion_model):
            style_template = ''
            style_negative_template = []
            if len(style) > 0:
                style_name = style[-1]
                diffusion_model_info = self.pipe_manager.model_level_info[
                    diffusion_model]
                now_pipeline = diffusion_model_info['pipeline'][0]
                style_info = self.name_level_style[now_pipeline].get(
                    style_name, {})
                for st in style:
                    c_style_info = self.name_level_style[now_pipeline].get(
                        st, {})
                    c_prompt = c_style_info.get('PROMPT', '')
                    c_negative_prompt = c_style_info.get('NEGATIVE_PROMPT', '')
                    if style_template == '':
                        style_template = c_prompt
                    elif '{prompt}' in style_template:
                        if '{prompt}' in c_prompt:
                            style_template = style_template.replace(
                                '{prompt}', c_prompt)
                    else:
                        style_template += c_prompt
                    style_negative_template.append(c_negative_prompt)
            else:
                style_name = ''
                style_info = {}
            style_negative_template = ','.join(style_negative_template)
            if style_info.get(
                    'IMAGE_PATH',
                    None) and not os.path.exists(style_info.IMAGE_PATH):
                style_info.IMAGE_PATH = FS.get_from(style_info.IMAGE_PATH)
            return (gr.Text(value=style_name),
                    gr.Text(value=style_info.get('SOURCE', '')),
                    gr.Text(value=style_info.get('PROMPT', '')),
                    gr.Text(value=style_info.get('NEGATIVE_PROMPT', '')),
                    gr.Text(value=style_template),
                    gr.Text(value=style_negative_template),
                    gr.Image(value=style_info.get('IMAGE_PATH', None)),
                    gr.Text(value=style_info.get('PROMPT_EXAMPLE', '')))

        self.style.change(change_style,
                          inputs=[self.style, model_manage_ui.diffusion_model],
                          outputs=[
                              self.style_name, self.style_source,
                              self.style_prompt, self.style_negative_prompt,
                              self.style_template,
                              self.style_negative_template, self.style_example,
                              self.style_example_prompt
                          ],
                          queue=False)

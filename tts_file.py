import os
import tomli
from f5_tts.infer.utils_infer import (
    infer_process,
    load_model,
    load_vocoder,
    preprocess_ref_audio_text,
    remove_silence_for_generated_wav 
)
from f5_tts.model import DiT, UNetT
from importlib.resources import files
import soundfile as sf
import numpy as np
from omegaconf import OmegaConf
from cached_path import cached_path

def load_config(config_path='config.toml'):
    with open(config_path, 'rb') as config_file:
        return tomli.load(config_file)

def prepare_model_and_vocoder(config):
    vocoder_name = "vocos"
    vocoder_local_path = "../checkpoints/vocos-mel-24khz"
    vocoder = load_vocoder(
        vocoder_name=vocoder_name, 
        is_local=False, 
        local_path=vocoder_local_path
    )

    if config['model'] == "F5-TTS":
        model_cls = DiT
        model_cfg_path = str(files("f5_tts").joinpath("configs/F5TTS_Base_train.yaml"))
        model_cfg = OmegaConf.load(model_cfg_path).model.arch
        
        ckpt_file = str(cached_path(
            f"hf://SWivid/F5-TTS/F5TTS_Base/model_1200000.safetensors"
        ))
    elif config['model'] == "E2-TTS":
        model_cls = UNetT
        model_cfg = dict(dim=1024, depth=24, heads=16, ff_mult=4)
        ckpt_file = str(cached_path(
            f"hf://SWivid/E2-TTS/E2TTS_Base/model_1200000.safetensors"
        ))
    else:
        raise ValueError(f"Unsupported model: {config['model']}")

    ema_model = load_model(
        model_cls, 
        model_cfg, 
        ckpt_file, 
        mel_spec_type=vocoder_name
    )

    return ema_model, vocoder

def generate_tts_audio(config):
    print("Initializing TTS model...")
    ema_model, vocoder = prepare_model_and_vocoder(config)

    ref_audio, ref_text = preprocess_ref_audio_text(
        config['ref_audio'], 
        config['ref_text']
    )

    gen_text = config['gen_file'] if config['gen_file'] else config['gen_text']

    print(f"Generating audio for text: {gen_text}")
    audio_segment, final_sample_rate, _ = infer_process(
        ref_audio,
        ref_text,
        gen_text,
        ema_model,
        vocoder
    )

    os.makedirs(config.get('output_dir', 'output'), exist_ok=True)

    output_path = os.path.join(
        config.get('output_dir', 'output'), 
        config.get('output_file', 'output.wav')
    )
    
    print(f"Saving audio to: {output_path}")
    sf.write(output_path, audio_segment, final_sample_rate)

    if config.get('remove_silence', False):
        print("Removing silence from generated audio...")
        remove_silence_for_generated_wav(output_path)
        print("Silence removed successfully.")

    print("Audio generation completed successfully!")

def main():
    try:
        config = load_config()
        
        generate_tts_audio(config)
    
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
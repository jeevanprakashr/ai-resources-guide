from typing import Any
import time
# import streamlit as st
from yt_dlp import YoutubeDL
from haystack.components.audio import LocalWhisperTranscriber
from haystack.components.builders import PromptBuilder
from haystack_integrations.components.generators.llama_cpp import LlamaCppGenerator
from haystack_integrations.components.generators.ollama import OllamaGenerator
from haystack import Pipeline

def download_video(url):
    ydl_opts: dict[str, Any] = {
        "format": "bestvideo+bestaudio/best",
        "outtmpl": "video.%(ext)s",
        "merge_output_format": "mp4",
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp4"
    return filename

def init_prompt_builder():
    prompt_template = """
    You are a helpful assistant that summarizes YouTube videos. 
    Please provide a concise summary of the following transcript:
    
    {% for doc in transcript %}
        {{ doc.content }}
    {% endfor %}
    
    Summary:
    """
    return PromptBuilder(prompt_template, required_variables=["transcript"], variables=["transcript"])

def init_generator():
    generator = LlamaCppGenerator(
        model = "./llama-2-7b-32k-instruct-Q4_K_S.gguf",
        n_ctx = 2500,              # your model supports 32k context — set it explicitly
        n_batch = 512,              # tokens processed in parallel; higher = faster but more RAM
        model_kwargs = {
            "n_gpu_layers": -1,     # -1 = offload all layers to GPU (Metal on Mac); 0 = CPU only
            "n_threads": 8,         # CPU threads; match your core count
            "verbose": False        # suppress llama.cpp logs
        },
        generation_kwargs = {
            "max_tokens": 512,                  # max length of the summary
            "temperature": 0.3,                 # lower = more focused/deterministic
            "top_p": 0.9,                       # nucleus sampling: consider only the top_p probability mass for next token
            "top_k": 40,                        # top-k sampling: consider only the top_k most likely next tokens
            "repeat_penalty": 1.1,              # penalize repeated tokens to encourage diversity
            "stop": ["\n\n", "User:", "###"]    # stop generation when any of these tokens are encountered
        }
    )
    # generator = OllamaGenerator(
    #     model = "qwen2.5:1.5b",
    #     generation_kwargs = {
    #         "num_ctx": 2500,
    #         "temperature": 0.3,                 # lower = more focused/deterministic
    #         "top_p": 0.9,                       # nucleus sampling: consider only the top_p probability mass for next token
    #         "top_k": 40,                        # top-k sampling: consider only the top_k most likely next tokens
    #         "repeat_penalty": 1.1,              # penalize repeated tokens to encourage diversity
    #         "stop": ["User:", "###"]    # stop generation when any of these tokens are encountered
    #     }
    # )
    return generator

def transcribe_audio(file_path):
    whisper = LocalWhisperTranscriber()
    pipeline = Pipeline()
    pipeline.add_component(name = "whisper", instance = whisper)
    pipeline.add_component(name = "prompt", instance = init_prompt_builder())
    pipeline.add_component(name = "generator", instance = init_generator())
    pipeline.connect("whisper.documents", "prompt.transcript")
    pipeline.connect("prompt.prompt", "generator.prompt")
    output = pipeline.run(
        {
            "whisper": {"sources": [file_path]},
        }
    )
    # return output["generator"]["replies"][0]
    return output

def main():
    start = time.time()
    file_path = download_video("https://youtu.be/SxAwyeCkguc?si=Mm-7nO30MCCi75v3")
    output = transcribe_audio(file_path)
    print(output)
    elapsed = time.time() - start
    print(f"\nTime taken: {elapsed:.2f}s")

if __name__ == "__main__":
    main()
    # pb = init_prompt_builder()
    # print(pb.__haystack_input__)
    # print(pb.__haystack_output__)
    # gen = init_generator()
    # print(gen.__haystack_input__)
    # print(gen.__haystack_output__)
    # whisper = LocalWhisperTranscriber()
    # print(whisper.__haystack_input__)
    # print(whisper.__haystack_output__)
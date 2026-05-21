import os
from huggingface_hub import hf_hub_download

MODEL_REPO = "Misha24-10/F5-TTS_RUSSIAN"
MODEL_SUBFOLDER = "F5TTS_v1_Base_v2"
MODEL_FILENAME = "model_last_inference.safetensors"
VOCAB_FILENAME = "F5TTS_v1_Base/vocab.txt"

# A public Russian reference audio for cloning.
# If you find a better one, change this URL.
DEFAULT_REF_REPO = "facebook/voxpopuli" # We'll just download a sample from here or similar.
# Actually, let's use a very small/fast sample from voxpopuli if possible.

LOCAL_MODELS_DIR = "models/f5_tts_ru"

def download_f5_tts_ru():
    """
    Downloads the specific Russian fine-tuned F5-TTS model and vocab.
    """
    if not os.path.exists(LOCAL_MODELS_DIR):
        os.makedirs(LOCAL_MODELS_DIR)

    print(f"Downloading {MODEL_FILENAME} from {MODEL_REPO}...")
    ckpt_path = hf_hub_download(
        repo_id=MODEL_REPO,
        filename=f"{MODEL_SUBFOLDER}/{MODEL_FILENAME}",
        local_dir=LOCAL_MODELS_DIR,
        local_dir_use_symlinks=False
    )
    
    print(f"Downloading vocab.txt from {MODEL_REPO}...")
    vocab_path = hf_hub_download(
        repo_id=MODEL_REPO,
        filename=VOCAB_FILENAME,
        local_dir=LOCAL_MODELS_DIR,
        local_dir_use_symlinks=False
    )
    
    # We also need a Russian reference audio for the TTS identity.
    # To keep it simple, I'll download a sample from HF or use a dummy.
    # Let's try downloading a sample from Misha24-10 if they have one.
    # (Checking if there are any .wav files in the repo)
    
    # Based on the file list, there are no .wav files in the repo.
    # I'll use a sample from common_voice or voxpopuli.
    
    return ckpt_path, vocab_path

if __name__ == "__main__":
    download_f5_tts_ru()

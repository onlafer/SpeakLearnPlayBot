import os
import io
import asyncio
import torch
import soundfile as sf
import numpy as np
import re
from f5_tts.api import F5TTS

try:
    from ruaccent import RUAccent
except ImportError:
    RUAccent = None

# Paths to local model files
MODEL_DIR = os.path.abspath("models/f5_tts_ru")
CKPT_FILE = os.path.join(MODEL_DIR, "F5TTS_v1_Base_v2", "model_last_inference.safetensors")
VOCAB_FILE = os.path.join(MODEL_DIR, "F5TTS_v1_Base", "vocab.txt")

# Reference voices
VOICES = {
    "male": {
        "audio": os.path.abspath("models/ref_audio/russian_sample.wav"),
        "text": "С фронта Была осень тысяча девятьсот семнадцатого года. Мы стояли в Бессарабии..."
    },
    "female": {
        "audio": os.path.abspath("models/ref_audio/russian_female.wav"),
        "text": "С фронта Была осень тысяча девятьсот семнадцатого года. Мы стояли в Бессарабии..."
    }
}

# Singleton instances
_f5tts_instance = None
_accentizer_instance = None

# Apply a global patch to f5_tts to fix duration calculation when stress marks are present.
# The library uses len(text.encode("utf-8")) which counts '+' and accents, 
# but these don't add to audio duration, causing tensor size mismatches.
import f5_tts.infer.utils_infer as utils_infer
_original_len = len

def _patched_len(obj):
    if isinstance(obj, bytes):
        try:
            # Try to decode and remove stress marks for length calculation
            s = obj.decode('utf-8')
            if '+' in s or '\u0301' in s or '\u0300' in s:
                # Remove common stress marks used in Russian TTS
                s_clean = s.replace('+', '').replace('\u0301', '').replace('\u0300', '')
                return _original_len(s_clean.encode('utf-8'))
        except Exception:
            pass
    return _original_len(obj)

# Inject the patched len into the library's namespace
utils_infer.len = _patched_len


def _patch_ruaccent_onnx(accentizer):
    """
    Monkey-patch RUAccent internal models to provide 'token_type_ids' if required by ONNX.
    This fixes the 'Required inputs (['token_type_ids']) are missing' error.
    """
    import numpy as np
    
    # Patch AccentModel
    if hasattr(accentizer, 'accent_model'):
        old_put_accent = accentizer.accent_model.put_accent
        def patched_put_accent(word):
            lower_word = word.lower()
            inputs = accentizer.accent_model.tokenizer(lower_word, return_tensors="np")
            inputs = {k: v.astype(np.int64) for k, v in inputs.items()}
            
            # Check what the model expects
            expected = [o.name for o in accentizer.accent_model.session.get_inputs()]
            if 'token_type_ids' in expected and 'token_type_ids' not in inputs:
                inputs['token_type_ids'] = np.zeros_like(inputs['input_ids'])
            
            # Re-implement the rest of put_accent
            outputs = accentizer.accent_model.session.run(None, inputs)
            from ruaccent.accent_model import softmax
            output_names = {output_key.name: idx for idx, output_key in enumerate(accentizer.accent_model.session.get_outputs())}
            logits = outputs[output_names["logits"]]
            probabilities = softmax(logits)
            scores = np.max(probabilities, axis=-1)[0]
            labels = np.argmax(logits, axis=-1)[0]
            pred_with_scores = [{'label': accentizer.accent_model.id2label[str(label)], 'score': float(score)} 
                                for label, score in zip(labels, scores)]
            return accentizer.accent_model.render_stress(word, pred_with_scores)
        
        accentizer.accent_model.put_accent = patched_put_accent

    # Patch OmographModel
    if hasattr(accentizer, 'omograph_model'):
        old_classify = accentizer.omograph_model.classify
        def patched_classify(texts, hypotheses, num_hypotheses):
            # We can't easily re-implement the whole classify, but we can patch session.run
            old_run = accentizer.omograph_model.session.run
            def patched_run(output_names, input_feed, run_options=None):
                expected = [o.name for o in accentizer.omograph_model.session.get_inputs()]
                if 'token_type_ids' in expected and 'token_type_ids' not in input_feed:
                    input_feed['token_type_ids'] = np.zeros_like(input_feed['input_ids'])
                return old_run(output_names, input_feed, run_options)
            
            accentizer.omograph_model.session.run = patched_run
            try:
                return old_classify(texts, hypotheses, num_hypotheses)
            finally:
                accentizer.omograph_model.session.run = old_run
        
        accentizer.omograph_model.classify = patched_classify

    # Patch StressUsagePredictorModel
    if hasattr(accentizer, 'stress_usage_predictor'):
        old_predict = accentizer.stress_usage_predictor.predict_stress_usage
        def patched_predict(text):
            old_run = accentizer.stress_usage_predictor.session.run
            def patched_run(output_names, input_feed, run_options=None):
                expected = [o.name for o in accentizer.stress_usage_predictor.session.get_inputs()]
                if 'token_type_ids' in expected and 'token_type_ids' not in input_feed:
                    input_feed['token_type_ids'] = np.zeros_like(input_feed['input_ids'])
                return old_run(output_names, input_feed, run_options)
            
            accentizer.stress_usage_predictor.session.run = patched_run
            try:
                return old_predict(text)
            finally:
                accentizer.stress_usage_predictor.session.run = old_run
        
        accentizer.stress_usage_predictor.predict_stress_usage = patched_predict


def get_accentizer():
    """Returns singleton instance of RUAccent."""
    global _accentizer_instance
    if _accentizer_instance is None and RUAccent is not None:
        try:
            print("Loading RUAccent model...")
            _accentizer_instance = RUAccent()
            # Use turbo3.1 for best balance of speed/accuracy
            _accentizer_instance.load(omograph_model_size='turbo3.1', use_dictionary=True, tiny_mode=False)
            
            # Apply patches for ONNX compatibility
            _patch_ruaccent_onnx(_accentizer_instance)
        except Exception as e:
            print(f"Error loading RUAccent: {e}")
            _accentizer_instance = None
    return _accentizer_instance


def get_f5tts():
    """
    Returns a singleton instance of the F5TTS model.
    Loads the model on the first call.
    """
    global _f5tts_instance
    if _f5tts_instance is None:
        print("Loading local F5-TTS Russian model...")
        # Check if files exist
        if not os.path.exists(CKPT_FILE) or not os.path.exists(VOCAB_FILE):
             raise FileNotFoundError(f"Model files not found. Run model_downloader.py first. (Looking for {CKPT_FILE})")
        
        # Now using CUDA because we have sm_120 support in torch 2.11+cu128
        _f5tts_instance = F5TTS(
            model="F5TTS_v1_Base",
            ckpt_file=CKPT_FILE,
            vocab_file=VOCAB_FILE,
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
    return _f5tts_instance


def _normalize_text_for_f5(text: str, use_accent: bool = True) -> str:
    """
    Adds stress marks to Russian text and converts them from '\u0301' 
    (Unicode combining acute accent) to '+' prefix (e.g., 'молоко́' -> 'м+олоко').
    """
    accentizer = get_accentizer() if use_accent else None
    
    if not use_accent:
        return text

    try:
        # 1. If text already has many '+' marks (e.g. from LLM), skip RUAccent to avoid conflicts
        # but still convert any potential unicode accents if present.
        if text.count('+') > len(text.split()) * 0.5:
            accented_text = text
        elif accentizer:
            # Get accented text from RUAccent (outputs vowels with \u0301)
            accented_text = accentizer.process_all(text)
        else:
            accented_text = text
        
        # 2. Convert 'vowel\u0301' to '+vowel'
        vowels = "аеёиоуыэюяАЕЁИОУЫЭЮЯ"
        for v in vowels:
            accented_text = accented_text.replace(f"{v}\u0301", f"+{v.lower()}")
            
        # 3. Clean up double stresses
        import re
        accented_text = re.sub(r'\++', '+', accented_text)
        
        # 4. Ensure '+' is BEFORE the vowel (for the model)
        vowels_chars = "аеёиоуыэюяАЕЁИОУЫЭЮЯ"
        accented_text = re.sub(r'([' + vowels_chars + r'])\+', r'+\1', accented_text)
        
        return accented_text
    except Exception as e:
        print(f"Text normalization error: {e}. Returning original.")
        return text


async def async_text_to_speech_f5(text: str, voice: str = "male", use_accent: bool = True) -> io.BytesIO | None:
    """
    Asynchronously generates Russian speech from text using the local F5-TTS model.
    Supported voices: 'male', 'female'.
    Handles long texts by splitting them into chunks.
    """
    def _generate() -> io.BytesIO | None:
        try:
            # 0. Select voice config
            voice_config = VOICES.get(voice, VOICES["male"])
            ref_audio = voice_config["audio"]
            ref_text = voice_config["text"]

            # 1. Preprocess text: split into chunks at sentence boundaries if too long
            # F5-TTS works best with chunks under ~150-200 characters. 
            # We use 100 to stay well within the library's internal batching limits
            # which are calculated based on reference audio length.
            max_chunk_len = 100
            
            # Simple sentence splitting: . ! ? followed by space or end of string
            sentences = re.split(r'(?<=[.!?])\s+', text)
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) < max_chunk_len:
                    current_chunk += " " + sentence if current_chunk else sentence
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
            if current_chunk:
                chunks.append(current_chunk.strip())

            f5 = get_f5tts()
            all_wavs = []
            sr = 24000 # Default SR for F5-TTS

            for i, chunk in enumerate(chunks):
                # Preprocess text to add stress marks
                normalized_text = _normalize_text_for_f5(chunk, use_accent=use_accent)
                print(f"Synthesizing [{voice}] chunk {i+1}/{len(chunks)}: {normalized_text}")

                # 2. Run inference
                wav, chunk_sr, _ = f5.infer(
                    ref_file=ref_audio,
                    ref_text=ref_text,
                    gen_text=normalized_text,
                    remove_silence=True,
                    speed=1.0
                )
                all_wavs.append(wav)
                sr = chunk_sr

            if not all_wavs:
                return None
            
            # Combine all chunks
            final_wav = np.concatenate(all_wavs)
            
            # Save to BytesIO in OGG/OPUS format for Telegram
            buffer = io.BytesIO()
            try:
                sf.write(buffer, final_wav, sr, format='OGG', subtype='OPUS')
            except Exception:
                sf.write(buffer, final_wav, sr, format='WAV')
                
            buffer.seek(0)
            return buffer
        except Exception as e:
            print(f"Local F5-TTS error: {e}")
            import traceback
            traceback.print_exc()
            return None

    return await asyncio.to_thread(_generate)

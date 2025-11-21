import yaml
from pathlib import Path
from django.conf import settings

# Cache della configurazione per evitare letture ripetute del file
_config_cache = None

def get_config_path():
    if hasattr(settings, 'BASE_DIR'):
        config_path = Path(settings.BASE_DIR) / 'rag_config.yaml'
        if config_path.exists():
            return config_path

def load_config(force_reload=False):
    global _config_cache
    
    # Restituisci dalla cache se disponibile e non è richiesto reload
    if _config_cache is not None and not force_reload:
        return _config_cache
    
    config_path = get_config_path()
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Salva in cache
        _config_cache = config
        return config
        
    except yaml.YAMLError as e:
        raise yaml.YAMLError(
            f"Errore nel parsing del file YAML '{config_path}': {e}"
        )


def get_config():
    return load_config(force_reload=False)


def get_param(section, param, default=None):
    config = get_config()
    return config.get(section, {}).get(param, default)
 

def reload_config():
    return load_config(force_reload=True)


def get_chunk_size():
    return get_param('chunking', 'max_text_chunk_size', 500)


def get_chunk_overlap():
    return get_param('chunking', 'chunk_overlap_size', 50)


def get_n_results():
    return get_param('search', 'n_results', 5)


def get_collection_name():
    return get_param('embedding', 'collection_name', 'docseek_collection')


def get_embedding_model():
    return get_param('embedding', 'model_name', 'paraphrase-multilingual-MiniLM-L12-v2')
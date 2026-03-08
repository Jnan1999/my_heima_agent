'''
yaml格式配置文件
k: v
'''
import yaml
from utils.path_tool import get_abs_path


def load_config(config_path: str, encoding: str="utf-8"):
    with open(config_path, "r", encoding=encoding) as f:
        return yaml.load(f, Loader=yaml.FullLoader)

rag_conf = load_config(config_path=get_abs_path("config/rag.yml"))
chroma_conf = load_config(config_path=get_abs_path("config/chroma.yml"))
prompts_conf = load_config(config_path=get_abs_path("config/prompts.yml"))
agent_conf = load_config(config_path=get_abs_path("config/agent.yml"))

if __name__ == '__main__':
    print(rag_conf["embedding_model_name"])

from acronym import get_yaml_config
from acronym.utils.cordis import CONFIG_PATH, fetch_xml_projects

if __name__ == "__main__":
    fps = get_yaml_config(CONFIG_PATH)["framework_programmes"]

    for fp in fps:
        fetch_xml_projects(fp)

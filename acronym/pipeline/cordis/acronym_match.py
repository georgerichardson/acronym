import logging
from pandas import DataFrame

from acronym import PROJECT_DIR
from acronym.utils.cordis import CONFIG, cordis_output_path
from acronym.getters.cordis import projects
from acronym.utils.acronyms import acronymity
from acronym.utils.io import make_path_if_not_exist


if __name__ == "__main__":

    logger = logging.getLogger(__name__)

    for fp in CONFIG["framework_programmes"]:

        logger.info(f"Finding acronynm matches for CORDIS {fp.upper()}")

        projects_fp = projects(fp)
        acronyms = projects_fp["acronym"].fillna("X").tolist()
        titles = projects_fp["title"].tolist()
        with open(PROJECT_DIR / CONFIG["acronym_match"]["title_stops_path"], "r") as f:
            title_stops = f.readlines()

        acronymity_records = list(
            map(
                lambda a, t: acronymity(
                    a,
                    t,
                    min_term_len=CONFIG["acronym_match"]["min_term_len"],
                    min_order=CONFIG["acronym_match"]["min_order"],
                    max_order=CONFIG["acronym_match"]["max_order"],
                    stops=title_stops,
                ),
                acronyms,
                titles,
            ),
        )

        out_path = cordis_output_path(fp)
        make_path_if_not_exist(out_path)

        acronymity_df = DataFrame(acronymity_records)
        acronymity_df["rcn"] = projects_fp["rcn"]
        acronymity_df.to_csv(
            out_path / f"acronyms.csv",
            index=False,
        )

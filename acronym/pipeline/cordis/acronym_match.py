import logging
from pandas import DataFrame

from acronym.utils.cordis import CONFIG, cordis_output_path
from acronym.getters.cordis import projects
from acronym.utils.acronyms import (
    acronymity,
    remove_acronym_from_title,
    remove_long_numbers,
)
from acronym.utils.io import make_path_if_not_exist


if __name__ == "__main__":

    logger = logging.getLogger(__name__)

    for fp in CONFIG["framework_programmes"]:

        logger.info(f"Finding acronynm matches for CORDIS {fp.upper()}")

        projects_fp = projects(fp)

        acronyms = projects_fp["acronym"].fillna("X").tolist()
        acronyms = list(map(lambda a: remove_long_numbers(a), acronyms))

        titles = projects_fp["title"].tolist()
        titles = list(
            map(
                lambda a, t: remove_acronym_from_title(a, t),
                acronyms,
                titles,
            )
        )

        acronymity_records = list(
            map(
                lambda a, t: acronymity(
                    a,
                    t,
                    min_term_len=CONFIG["acronym"]["min_term_len"],
                    order_range=(
                        CONFIG["acronym"]["min_order"],
                        CONFIG["acronym"]["max_order"],
                    ),
                ),
                acronyms,
                titles,
            )
        )

        out_path = cordis_output_path(fp)
        make_path_if_not_exist(out_path)

        acronymity_df = DataFrame(acronymity_records)
        acronymity_df["rcn"] = projects_fp["rcn"]
        acronymity_df.to_csv(
            out_path / f"acronyms.csv",
            index=False,
        )

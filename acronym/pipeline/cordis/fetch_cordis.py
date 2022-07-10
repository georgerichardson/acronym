""""Fetch CORDIS project and organization data, including individual project
XML files (optional).

Project and organization csvs are reformatted to conventional csv format, made
pandas friendly and formatting errors are removed.
"""

import click

from acronym.utils.cordis import (
    CONFIG,
    fetch_projects,
    fetch_xml_projects,
    fetch_organizations,
    reformat_organization_csv,
    reformat_project_csv,
)


@click.command()
@click.option("--no-xml", is_flag=True)
def run(no_xml: bool):
    """Runs the pipeline."""

    for fp in CONFIG["framework_programmes"]:
        fetch_projects(fp)

        if CONFIG["csv_organization_urls"][fp]:
            fetch_organizations(fp)

        reformat_project_csv(fp)
        reformat_organization_csv(fp)

        if not no_xml:
            fetch_xml_projects(fp)


if __name__ == "__main__":
    run()

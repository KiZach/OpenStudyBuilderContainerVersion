import json
import os
import sys
import uuid
from neo4j import GraphDatabase, Driver

DATABASE = os.environ.get("NEO4J_MDR_DATABASE")
HOST = os.environ.get("NEO4J_MDR_HOST")
PORT = os.environ.get("NEO4J_MDR_BOLT_PORT")
USER = os.environ.get("NEO4J_MDR_AUTH_USER")
PASS = os.environ.get("NEO4J_MDR_AUTH_PASSWORD")

uri = f"neo4j://{HOST}:{PORT}"


def load_reports(driver: Driver, directory: str):
    # Loop over all.json files in the given relative directory
    counter = 0
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as file:
                # Parse json content
                report = json.load(file)

                # Extract title, uuid and version from json
                title = report["title"]
                date = report["date"]
                _uuid = report["uuid"]
                version = report["version"]

                # Create report node
                with driver.session(database=DATABASE) as session:
                    results = session.run(
                        """
                        MERGE (d:_Neodash_Dashboard{
                            uuid: $uuid
                        })
                        ON CREATE
                         SET 
                          d.uuid = $uuid
                        SET      
                          d.content = $json,
                          d.date = $date,
                          d.title = $title,
                          d.user = $user,
                          d.version= $version
                        """,
                        json=json.dumps(report['content'][0]),
                        title=title,
                        user=USER,
                        uuid=_uuid,
                        date=date,
                        version=version,
                    )

                    # If success, increment counter
                    stats = results.consume().counters
                    if stats.nodes_created == 1:
                        counter += 1
                    else:
                        print(f"Report {title} could not be created")

    return counter


if __name__ == "__main__":
    # Extract directory from command line arguments
    try:
        directory = sys.argv[1]
    except IndexError:
        print("Error: no directory given!")
        sys.exit(1)
    with GraphDatabase.driver(uri, auth=(USER, PASS)) as driver:
        created_reports = load_reports(driver, directory)
        print(f"Created {created_reports} reports")

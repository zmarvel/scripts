import os
import argparse
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

import pokedex.db
import pokemap.models as m
import pokedex.db.tables as t

def add(row, session, query):
    q = query.filter(t.Location.identifier == row['location_identifier'])
    row['location_id'] = q.first().id
    route = m.Route(int(row['generation_id']),
                    int(row['region_id']),
                    int(row['location_id']),
                    int(row['x1']),
                    int(row['y1']),
                    int(row['x2']),
                    int(row['y2']))
    session.add(route)

def main():
    parser = argparse.ArgumentParser(
                description=u'Map rectangles on the world map to routes.')
    parser.add_argument(u'map_path', metavar='path', nargs=1)
    parser.add_argument(u'--commit', action='store', nargs=1)
    args = parser.parse_args()

    map_path = os.path.abspath(args.map_path[0])
    db_path = os.path.abspath(args.commit[0])

    try:
        engine = create_engine('sqlite:///{}'.format(db_path))
        m.Base.metadata.bind = engine
        Session = sessionmaker(bind=engine)
        session = Session()
    except:
        print(u'Unable to connect to Pokemap database.')
        raise

    try:
        PDSession = pokedex.db.connect()
    except:
        print(u'Unable to connect to Pokedex database.')
        raise

   
    try:
        q = PDSession.query(t.Location)
        with open(map_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                add(row, session, q)
                print(u'Added {}.'.format(row['location_identifier']))
        session.commit()
    except:
        print(u'Unable to commit changes. Rolling back...')
        session.rollback()
        raise
    finally:
        print(u'Closing the session')
        session.close()

if  __name__ == '__main__':
    main()

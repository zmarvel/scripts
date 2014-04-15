import os, sys, argparse
from PIL import Image, ImageChops, ImageMath

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from pokemap.models import Patch, Base
import pokedex
import pokedex.db.tables as pdt


SPRITE_SIZE = 16

# A rectangular patch of grass with height 16px

class GrassPatch(Patch):
    def __init__(self, generation_id, location_id, x1, x2, y):
        self.generation_id = generation_id
        self.location_id = location_id
        self.patch_type_id = 1
        self.x1 = x1
        self.y1 = y
        self.x2 = x2
        self.y2 = y + SPRITE_SIZE
    def add_grass(self):
        self.x2 += SPRITE_SIZE

class WaterPatch(Patch):
    def __init__(self, generation_id, location_id, x1, x2, y):
        self.generation_id = generation_id
        self.location_id = location_id
        self.patch_type_id = 2
        self.x1 = x1
        self.y1 = y
        self.x2 = x2
        self.y2 = y + SPRITE_SIZE
    def add_water(self):
        self.x2 += SPRITE_SIZE


# Takes a path to an image of a route and a Pokedex Location object, as well as
# an optional SQLAlchemy session in order to commit the patches belonging to the
# route.
class Route:
    def __init__(self, generation_id, route_path, location, session=None):
        self.generation_id = generation_id
        self.route_path = route_path
        self.route = Image.open(route_path)
        self.location = location
        self.session = session

        if self.route.mode != 'RGB':
            self.route = self.route.convert('RGB')
            self.route.save(self.route_path)

        self.width, self.height = self.route.size

        self.grass_colors =  [(48, (56, 88, 16)),
                                (18, (160, 224, 192)),
                                (64, (112, 200, 160)),
                                (52, (64, 176, 136)),
                                (68, (56, 144, 48)),
                                (6, (24, 160, 104))]

        self.water_colors = set([(96, 160, 216),\
                                 (72, 120, 216),\
                                 (48, 96, 160),\
                                 (48, 96, 176),\
                                 (72, 144, 216)])
        
        self.xstart, self.ystart = self.find_grass_start()
        if self.xstart is None:
            self.xoffset = 0
            self.yoffset = 0
        else:
            self.xoffset = self.xstart % SPRITE_SIZE
            self.yoffset = self.ystart % SPRITE_SIZE
        self.grass_patches = self.find_grass_patches()
        self.water_patches = self.find_water_patches()

    # Returns true if the two images are the same.
    # This isn't necessary anymore, but I'm leaving it here for reference
    # for the moment.
    def sprite_same(self, image1, image2):
        diff = ImageChops.difference(image1, image2)
        if sum(ImageMath.eval('int(diff)', diff=diff).histogram()) == 0:
            return True
        else:
            return False

    # Checks an image for the colors found in the two different types of water
    # in FRLG.
    def has_water(self, image):
        image_colors = sorted(image.getcolors(), key=lambda x: -x[0])
        image_colors = filter(lambda x: x[1] in self.water_colors, image_colors[:2])
        if len(image_colors) == 2\
            or (image_colors and image_colors[0][0] >= 224):
            return True
        return False

    # We can be more specific with grass. There are always the same amounts of
    # the same colors, and this is faster than actually comparing the sprite.
    def has_grass(self, image):
        image_colors = image.getcolors()
        if image_colors == self.grass_colors:
            return True
        return False

    # Find the first patch of grass to determine if there is an offset to the
    # grid
    def find_grass_start(self):
        for y1 in range(0, self.height - SPRITE_SIZE + 1):
            y2 = y1 + SPRITE_SIZE
            for x1 in range(0, self.width - SPRITE_SIZE + 1):
                x2 = x1 + SPRITE_SIZE

                square = self.route.crop((x1, y1, x2, y2))
                if self.has_grass(square):
                    return x1, y1
        return None, None 

    # Search for tall grass, beginning where find_grass_start() foudn the first
    # patch
    def find_grass_patches(self):
        grass_patches = []
        if self.xstart is None:
            return grass_patches
        x1, y1 = self.xstart, self.ystart

        while y1 <= self.height - SPRITE_SIZE:
            y2 = y1 + SPRITE_SIZE
            x1 = self.xoffset
            while x1 <= self.width - SPRITE_SIZE:
                x2 = x1 + SPRITE_SIZE

                square = self.route.crop((x1, y1, x2, y2))

                if self.has_grass(square):
                    if grass_patches and\
                        grass_patches[-1].y1 == y1 and\
                        grass_patches[-1].x2 == x1:
                        grass_patches[-1].add_grass()
                    else:
                        grass_patches.append(
                            GrassPatch(
                                self.generation_id,
                                self.location.id,
                                x1,
                                x2,
                                y1)
                            )
                x1 += SPRITE_SIZE
            y1 += SPRITE_SIZE

        return grass_patches

    def find_water_patches(self):
        water_patches = []
        x1, y1 = self.xoffset, self.yoffset

        while y1 <= self.height - SPRITE_SIZE:
            y2 = y1 + SPRITE_SIZE
            x1 = self.xoffset
            while x1 <= self.width - SPRITE_SIZE:
                x2 = x1 + SPRITE_SIZE

                square = self.route.crop((x1, y1, x2, y2))
                
                if self.has_water(square):
                    if water_patches and\
                        water_patches[-1].y1 == y1 and\
                        water_patches[-1].x2 == x1:
                        water_patches[-1].add_water()
                    else:
                        water_patches.append(
                            WaterPatch(
                                self.generation_id,
                                self.location.id,
                                x1,
                                x2,
                                y1))
                x1 += SPRITE_SIZE
            y1 += SPRITE_SIZE

        return water_patches

    def __str__(self):
        output = u'Grass patches:\n'
        for patch in self.grass_patches:
            output += repr(patch) + u'\n'
        output += u'\n'
        output += u'Water patches:\n'
        for patch in self.water_patches:
            output += repr(patch) + u'\n'
        return output

    def __repr__(self):
        return u'<Route(generation={0.generation_id}, name={0.location.name}>'\
                .format(self)

    def add_patches(self):
        print(u'Adding patches for {}:'.format(self.location.name))
        print(u'Adding grass patches...')
        self.session.add_all(self.grass_patches)

        print(u'Adding water patches...')
        self.session.add_all(self.water_patches)
        

def main():
    parser = argparse.ArgumentParser(description=u'Find tall grass and water in Pokemon routes.')
    parser.add_argument(u'gen_id', metavar=u'generation', nargs=1)
    parser.add_argument(u'route_dir', metavar=u'routes_dir', nargs=1)
    parser.add_argument(u'--one', action=u'store', nargs=1)
    parser.add_argument(u'--commit', action=u'store', nargs=1)
    args = parser.parse_args()
    
    PDSession = pokedex.db.connect()


    gen_id = args.gen_id[0]
    if args.route_dir:
        route_dir = os.path.abspath(args.route_dir[0])
        route_paths = [os.path.join(route_dir, x) for x in os.listdir(route_dir)]
    elif args.one:
        route_paths = list(os.path.abspath(args.one[0]))
    
    
    routes = []

    for route_path in route_paths:
        route_identifier = os.path.splitext(os.path.split(route_path)[1])[0]
        try:
            location = PDSession.query(pdt.Location)\
                        .filter(pdt.Location.identifier == route_identifier)\
                        .one()
        except NoResultFound as e:
            print(u'{} does not match a route identifier in the Pokedex'\
                    .format(route_identifier))
            raise e
        print(u'Processing {}...'.format(location.name))
        routes.append(Route(gen_id, route_path, location))
        grass_total = len(routes[-1].grass_patches)
        water_total = len(routes[-1].water_patches)
        print(u'...found {} grass patches'.format(grass_total))
        print(u'...found {} water patches'.format(water_total))

    if args.commit:
        db_path = os.path.abspath(args.commit[0])
        engine = create_engine(u'sqlite:///{}'.format(db_path))
        Base.metadata.bind = engine
        Session = sessionmaker(bind=engine)
        session = Session()

        for route in routes:
            route.session = session
            try:
                route.add_patches()
                session.commit()
            except:
                print(u'Error: Rolling back changes...')
                session.rollback()
                raise
            finally:
                print(u'Closing the session...')
                session.close()
            print(u'All routes were added.')
    else:
        for route in routes:
            print(repr(route))
            print(route)
            

if __name__ == '__main__':
    main()    

import os, sys, argparse
from PIL import Image, ImageChops, ImageMath

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pokemap.models import Patch, Base


SPRITE_SIZE = 16

# A rectangular patch of grass with height 16px

class GrassPatch:
    def __init__(self, x1, x2, y):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y
        self.y2 = y + SPRITE_SIZE
    def add_grass(self):
        self.x2 += SPRITE_SIZE

class WaterPatch:
    def __init__(self, x1, x2, y):
        self.x1 = x1
        # Water has a border on the right side that doesn't have to be checked--
        # it can be assumed, so we add an extra 16px to allow for that.
        self.x2 = x2 + SPRITE_SIZE
        self.y1 = y
        self.y2 = y + SPRITE_SIZE
    def add_water(self):
        self.x2 += SPRITE_SIZE

class Route:
    def __init__(self, route_path, grass_path, water_paths):
        self.route_path = route_path
        self.route = Image.open(route_path)
        self.width, self.height = self.route.size

        self.grass = Image.open(grass_path)

        self.waters = [Image.open(x) for x in water_paths]
        
        self.xstart, self.ystart = self.find_grass_start()
        self.xoffset = self.xstart % SPRITE_SIZE
        self.yoffset = self.ystart % SPRITE_SIZE

        self.grass_patches = self.find_grass_patches()

        self.water_patches = self.find_water_patches()

    # Returns true if the two images are the same.
    def sprite_same(self, image1, image2):
        diff = ImageChops.difference(image1, image2)
        if sum(ImageMath.eval('int(diff)', diff=diff).histogram()) == 0:
            return True
        else:
            return False

    # Find the first patch of grass to determine if there is an offset to the
    # grid
    def find_grass_start(self):
        for y1 in range(0, self.height - SPRITE_SIZE + 1):
            y2 = y1 + SPRITE_SIZE
            for x1 in range(0, self.width - SPRITE_SIZE + 1):
                x2 = x1 + SPRITE_SIZE

                square = self.route.crop((x1, y1, x2, y2))
                if self.sprite_same(square, self.grass):
                    return x1, y1

    # Search for tall grass, beginning where find_grass_start() foudn the first
    # patch
    def find_grass_patches(self):
        grass_patches = []
        x1, y1 = self.xstart, self.ystart

        while y1 <= self.height - SPRITE_SIZE:
            y2 = y1 + SPRITE_SIZE
            x1 = self.xoffset
            while x1 <= self.width - SPRITE_SIZE:
                x2 = x1 + SPRITE_SIZE

                square = self.route.crop((x1, y1, x2, y2))

                if self.sprite_same(square, self.grass):
                    if grass_patches and\
                        grass_patches[-1].y1 == y1 and\
                        grass_patches[-1].x2 == x1:
                        grass_patches[-1].add_grass()
                    else:
                        grass_patches.append(GrassPatch(x1, x2, y1))
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
                
                for water in self.waters:
                    if self.sprite_same(water, square):
                        if water_patches and\
                            water_patches[-1].y1 == y1 and\
                            water_patches[-1].x2 == x1:
                            water_patches[-1].add_water()
                        else:
                            water_patches.append(WaterPatch(x1, x2, y1))
                x1 += SPRITE_SIZE
            y1 += SPRITE_SIZE

        return water_patches
        

def main(route_path, grass_path, water_paths, db_path=None):
    route = Route(route_path, grass_path, water_paths)

    if db_path:
        engine = create_engine('sqlite:///{}'.format(db_path))

        Base.metadata.bind = engine
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        route_id = route_path.split('/')[-1][1]

        for patch in route.grass_patches:
            session.add(Patch(3, route_id, 0, patch.x1, patch.y1, patch.x2, patch.y2))
        for patch in route.water_patches:
            session.add(Patch(3, route_id, 0, patch.x1, patch.y1, patch.x2, patch.y2))

        session.commit()

    return route.grass_patches, route.water_patches

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find tall grass and water in\
                                    Pokemon routes.')
    parser.add_argument('route_path', metavar='route', nargs=1,\
                        help='the path to the image of the route.')
    parser.add_argument('sprite_dir', metavar='sprites', nargs=1,\
                        help='the directory in which the grass and water images\
                                are stored. Grass should be called grass.png,\
                                and the five water sprites should be called\
                                water1.png, water2.png, water3.png.... ')
    parser.add_argument('--commit', action='store', help='this argument should\
                        be followed by the database URI', nargs=1)

    args = parser.parse_args()
    route_path = os.path.abspath(args.route_path[0])
    sprite_dir = os.path.abspath(args.sprite_dir[0])
    grass_path = os.path.join(sprite_dir, "grass.png")
    water_paths = [os.path.join(sprite_dir, "water{}.png".format(x)) for x in\
                    range(1, 6)]

    if args.commit:
        db_path = os.path.abspath(args.commit[0])
        patches = main(route_path, grass_path, water_paths, db_path)
    else:
        patches = main(route_path, grass_path, water_paths)

    
    print("GRASS PATCHES:")
    for patch in patches[0]:
        print("{},{},{},{}".format(patch.x1, patch.y1, patch.x2, patch.y2))
    
    print("WATER PATCHES:")
    for patch in patches[1]:
        print("{},{},{},{}".format(patch.x1, patch.y1, patch.x2, patch.y2))

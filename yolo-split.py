# Hi guys :), up top are all the helper functions, on the bottom is the script
# u rly don't need to read the helper functions to get what's going on in the script
# the script is well commented, you'll understand what everything does.
# there r a few todos, def lmk in slack if u start to work on one of them :)

# -------------------- Helper functions ---------------------------- #

def translate_to_px(box):
    # get all the information from the input list
    object_id = box[0]
    center_x = box[1]
    center_y = box[2]
    width = box[3]
    height = box[4]
    # perform some pixel translation arthimatic
    center_x *= full_width
    center_y *= full_height
    width *= full_width
    height *= full_width
    # use pixel translations to calculate border walls
    left = center_x - .5 * width
    top = center_y - .5 * height
    right = center_x + .5 * width
    bottom = center_y + .5 * width
    # return the new style, easy for checking tile containment :)
    return [left, top, right, bottom, object_id]

def box_within_tile(box, tile):
    # index guide:
    # 0 represents the left boarder
    # 1 represents the top boarder
    # 2 represents the right boarder
    # 3 represents the bottom boarder
    
    # check all borders to see if any overlap exists
    if box[0] >= tile[2]: # if bb's left is further right than tile's right
        return False
    if box[1] >= tile[3]: # if bb's top is further down than tile's bottom
        return False
    if box[2] <= tile[0]: # if bb's right is further left than tile's left
        return False
    if box[3] <= tile[1]: # if bb's top is further down than tile's bottom
        return False

    for i in (0,1): # this adjusts bb's left and top edges to match tile
        if box[i] < tile[i]: # (if bb is entirely contained it goes unaltered)
            box[i] = tile[i]
    
    for i in (2,3): # this adjusts bb's right and bottom edges to match tile
        if box[i] > tile[i]: # (if bb is entirely contained it goes unaltered)
            box[i] = tile[i]

    return box

def px_to_relative(box, tile):
    return ""
# ---------------------------------------------------------------------#

# HELLO YES HI THE SCRIPT PORTION STARTS HERE

# TODO: decide how the script is gonna take input
# everything is just dummy vars from my old example rn

# CONCEPT: This script can also do the tiling, that way we can ensure that
# the filenames are consistent for tiles and their new labels

# In that case, the only input we'll need to give to this will be the
# image and it's label, and then it will output the tiles and all their labels
# it seems like a small headache to adapt this script to be able to take in multiple
# annotations and multiple images, but i'm sure we can just write a bash script to call
# this script on all the images/lables in a folder

# TODO: are we gonna programmatically come up with our tiles or are we
# just gonna hard-code border tuples like this? it's not too painful to come up
# with tiles by hand, but granted i only did four
# These numbers reprsent the boarders of the tile (left, top, right, bottom)

tiles = [(0,0,416,416),(334,0,750,416),     #top left, top right
         (0,334,416,750),(334,334,750,750)] # bottom left, bottom right

# obvi this will change
full_height = 750
full_width = 750

# bounding boxes come in as: object_id center_x center_y width height
# they're space seperated in labelIMG's yolo output, gonna have to convert
# it to a list like this
boxes = [[0, 0.054087, 0.711538, 0.103365, 0.052885],
        [0, 0.162260, 0.073317, 0.112981, 0.108173]]

translated_boxes = []
# so this list will contain all the boxes in the same form as the tiles:
# [left, top, right, bottom, object_id]
for box in boxes:
    translated_boxes.append(translate_to_px(box))

big_list = []
# big_list's elements will be lists that represent 
# the bounding boxes that exist within each tile (empty tile -> empty list)

for tile in tiles:
    tile_bbs = []
    for box in translated_boxes: 
        
        # The box_within_tile function takes in the box and tile borders and does this:
            # If any clip of the box is within the tile:
            #   Then the box is shrunk to fit within the tile and returned
            # If the whole box is within the tile:
            #   Then the box is returned unaltered
            # If the whole box misses the tile
            #   Then false is returned
        # CONCERN: parts of box may be within a tile even if the cell it bounds is not
        # perhaps we should return false unless the bounding box is entirely contained
        # within the tile... we should test a bunch and see for ourselves how problamtic this is
       
        box_in_tile = box_within_tile(box, tile)
        if box_in_tile:
            # TODO: write px_to_relative haha
            tile_bbs.append(px_to_relative(box_in_tile, tile))
        # otherwise, the box is not in the tile so we don't add it
    big_list.append(tile_bbs)




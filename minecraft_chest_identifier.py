import cv2
import numpy as np
import imutils
from imutils.perspective import four_point_transform
import os
import sys

import constants

ITEM_SIMILARITY_THRESHOLD = 0.6
CHEST_GUI_SIMILARITY_THRESHOLD = 0.4

MINECRAFT_ITEMS_IMG_FOLDER = "images/minecraftitems_1_19_organized/64x64"
SUBFOLDER_BUILDING_BLOCKS = "building_blocks"
SUBFOLDER_FOODS = "foods"
SUBFOLDER_MINERALS = "minerals"
SUBFOLDER_OTHER = "other"
SUBFOLDER_REDSTONE_COMPONENTS = "redstone_components"
SUBFOLDER_WEAPONS_ARMORS_TOOLS = "weapons_armors_tools"

# Image files that might cause problems.
IMAGE_FILES_TO_SKIP = ["air.png"]
MINECRAFT_ITEM_AIR = cv2.imread(os.path.join(MINECRAFT_ITEMS_IMG_FOLDER, SUBFOLDER_OTHER, "air.png"))

ITEMS_IMG = []
ITEMS_IMG_HEIGHT = 64
ITEMS_IMG_WIDTH = 64

def crop_chest_gui(image, debug=False):
    # Apply grayscale, and gaussian blur
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Threshold and morph close
    thresh = cv2.threshold(gray, 75, 255, cv2.THRESH_BINARY)[1]
    if debug:
        cv2.imshow("thresh", thresh)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # Find Canny edges
    edged = cv2.Canny(thresh, 100, 200)
    if debug:
        cv2.imshow('edged', edged)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    ## Find contours in the thresholded image and sort them by size in descending order
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    chest_gui_contour = None
    for c in cnts:
        # Approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        # If our approximated contour has four points, then we can assume we have found the outline of the chest GUI
        if len(approx) == 4:
            chest_gui_contour = approx
            break
    # If the chest GUI contour is empty then our script could not find the outline of the chest GUI so raise an error
    if chest_gui_contour is None:
        raise Exception(constants.EXCEPTION_CHEST_NOT_DETECTED)

    if debug:
        # Draw the contour of the chest GUI on the image and then display it to our screen for visualization/debugging purposes.
        output = image.copy()
        cv2.drawContours(image=output, contours=[chest_gui_contour], contourIdx=-1, color=(0, 0, 255), thickness=2)
        cv2.imshow("Iventory Outline", output)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    ## Adjust contour to the very corner of the chest GUI.
    chest_gui_contour_reshaped = chest_gui_contour.reshape(4, 2)
    min_x = sys.maxsize
    min_y = sys.maxsize
    max_x = -sys.maxsize
    max_y = -sys.maxsize
    for i in chest_gui_contour_reshaped:
        x = i[0]
        y = i[1]
        if x < min_x:
            min_x = x
        if x > max_x:
            max_x = x
        if y < min_y:
            min_y = y
        if y > max_y:
            max_y = y

    corners_of_chest_gui_list = [
        (min_x, min_y),
        (min_x, max_y),
        (max_x, max_y),
        (max_x, min_y)
    ]

    if debug:
        output = image.copy()

        chest_gui_contour_adjusted = np.array([[min_x, min_y], [min_x, max_y], [max_x, max_y], [max_x, min_y]])
        cv2.drawContours(image=output, contours=[chest_gui_contour_adjusted], contourIdx=-1, color=(0, 0, 255), thickness=2)
        
        output = cv2.rectangle(img=output, pt1=(min_x, min_y), pt2=(min_x + 1, min_y + 1), color=(255, 255, 0), thickness=3)
        output = cv2.rectangle(img=output, pt1=(min_x, max_y), pt2=(min_x + 1, max_y + 1), color=(0, 255, 0), thickness=3)
        output = cv2.rectangle(img=output, pt1=(max_x, max_y), pt2=(max_x + 1, max_y + 1), color=(0, 255, 255), thickness=3)
        output = cv2.rectangle(img=output, pt1=(max_x, min_y), pt2=(max_x + 1, min_y + 1), color=(255, 0, 255), thickness=3)
        cv2.imshow("Very corner of the Chest GUI", output)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    ## Crop the chest GUI from the whole image.

    chest_gui_img = image[min_y:max_y, min_x:max_x]

    if debug:
        cv2.imshow("chest_gui_img", chest_gui_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return chest_gui_img, corners_of_chest_gui_list


# Check if the cropped image is a chest GUI.
def is_image_a_chest_gui(chest_gui_img, debug=False):
    chest_gui_img_height = chest_gui_img.shape[0]
    chest_gui_img_width = chest_gui_img.shape[1]

    # Check if it is large chest or small chest
    is_chest_large = False
    if chest_gui_img_height > chest_gui_img_width:
        is_chest_large = True

    empty_chest_img = None
    if is_chest_large:
        empty_chest_img = cv2.imread("images/_large_chest.png")
    else:
        empty_chest_img = cv2.imread("images/_small_chest.png")

    resized_empty_chest_img = cv2.resize(src=empty_chest_img, dsize=(chest_gui_img_width, chest_gui_img_height), interpolation=cv2.INTER_AREA)
    resized_empty_chest_img_height = resized_empty_chest_img.shape[0]
    resized_empty_chest_img_width = resized_empty_chest_img.shape[1]

    if debug:
        print("chest_gui_img_height", chest_gui_img_height)
        print("chest_gui_img_width", chest_gui_img_width)
        print("chest_img_img_height", resized_empty_chest_img_height)
        print("chest_img_img_width", resized_empty_chest_img_width)
        cv2.imshow("chest_gui_img", chest_gui_img)
        cv2.imshow("resized_empty_chest_img", resized_empty_chest_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    all_pixels_count = chest_gui_img_height * chest_gui_img_width * chest_gui_img.shape[2]

    # Numpy absolute difference
    diff = np.abs(chest_gui_img - resized_empty_chest_img)
    diff_nonzero_pixels = np.count_nonzero(diff)
    similarity = 1 - (diff_nonzero_pixels / all_pixels_count)

    if debug:
        print("similarity:", similarity)

    if similarity > CHEST_GUI_SIMILARITY_THRESHOLD:
        return True
    else:
        return False


def crop_chest_gui_chest_part(chest_gui_img, debug=False):
    chest_gui_img_height = chest_gui_img.shape[0]
    chest_gui_img_width = chest_gui_img.shape[1]

    # Check if it is large chest or small chest
    is_chest_large = False
    if chest_gui_img_height > chest_gui_img_width:
        is_chest_large = True

    if is_chest_large:
        chest_part_y_top = round(chest_gui_img_height / 13.47692)
        chest_part_height = round(chest_gui_img_height / 2.03248)
    else:
        chest_part_y_top = round(chest_gui_img_height / 10.15385)
        chest_part_height = round(chest_gui_img_height / 3.06977)

    chest_part_x_start = round(chest_gui_img_width / 27.84)
    chest_part_width = round(chest_gui_img_width / 1.07573)
        
    chest_part_y_bottom = chest_part_y_top + chest_part_height
    chest_part_x_end = chest_part_x_start + chest_part_width

    if debug:
        output = chest_gui_img.copy()

        chest_part_contour = np.array([
            [chest_part_x_start, chest_part_y_top], 
            [chest_part_x_start, chest_part_y_bottom], 
            [chest_part_x_end, chest_part_y_bottom], 
            [chest_part_x_end, chest_part_y_top]
        ])
        cv2.drawContours(image=output, contours=[chest_part_contour], contourIdx=-1, color=(0, 0, 255), thickness=1)
        cv2.imshow("Very corner of the chest GUI", output)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    chest_part_img = chest_gui_img[chest_part_y_top:chest_part_y_bottom, chest_part_x_start:chest_part_x_end]

    if debug:
        cv2.imshow("chest_part_img", chest_part_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return (chest_part_img, is_chest_large)


# Crop each cell in the chest GUI by dividing the chest GUI chest part image into a 6x9 grid
# The chest part of chest GUI is composed of 6x9 (54 individual cells, 6 rows, 9 columns)
def crop_chest_cells(chest_gui_chest_part, is_chest_large, debug=False):
    col_count = 9
    row_count = 3
    if is_chest_large:
        row_count = 6

    step_x = round(chest_gui_chest_part.shape[1] / col_count)
    step_y = round(chest_gui_chest_part.shape[0] / row_count)
    if debug:
        print("height:", chest_gui_chest_part.shape[0])
        print("width:", chest_gui_chest_part.shape[1])
        print("step_x", step_x)
        print("step_y", step_y)

    # Variable to store the (x, y) coordinates of each cell.
    cells_coords = []

    # Loop over the grid locations.
    for y in range(0, row_count):
        row_cells_coords = []
        for x in range(0, col_count):
            # Compute the starting and ending (x, y) coordinates of the current cell.
            start_x = x * step_x
            start_y = y * step_y
            end_x = (x + 1) * step_x
            end_y = (y + 1) * step_y
            row_cells_coords.append((start_x, start_y, end_x, end_y))
        cells_coords.append(row_cells_coords)

    cell_width = cells_coords[0][0][2]
    cell_height = cells_coords[0][0][3]
    if debug:
        print("cell_width:", cell_width)
        print("cell_height:", cell_height)

    # Left side and top side of the cell is thinner than the right side and bottom side.
    cell_top_border_size = round(cell_height / 24)
    cell_start_border_size = round(cell_width / 24)
    # Right side and bottom side of the cell is thicker than the left side and top side.
    cell_bottom_border_size = round(cell_height / 14.4)
    cell_end_border_size = round(cell_width / 14.4)

    if debug:
        print("cell_top_border_size:", cell_top_border_size)
        print("cell_start_border_size:", cell_start_border_size)
        print("cell_bottom_border_size:", cell_bottom_border_size)
        print("cell_end_border_size:", cell_end_border_size)

    cells_img_list = []
    output = chest_gui_chest_part.copy()

    for row_cells_coords in cells_coords:
        for cell_coord in row_cells_coords:
            cell_coord_x_start = cell_coord[0]
            cell_coord_x_end = cell_coord[2]
            cell_coord_y_top = cell_coord[1]
            cell_coord_y_bottom = cell_coord[3]

            # Exclude the border of the cell.
            cell_inside_coord_x_start = cell_coord_x_start + cell_start_border_size
            cell_inside_coord_x_end = cell_coord_x_end - cell_end_border_size
            cell_inside_coord_y_top = cell_coord_y_top + cell_top_border_size
            cell_inside_coord_y_bottom = cell_coord_y_bottom - cell_bottom_border_size

            cell_contour = np.array([
                [cell_inside_coord_x_start, cell_inside_coord_y_top], 
                [cell_inside_coord_x_start, cell_inside_coord_y_bottom], 
                [cell_inside_coord_x_end, cell_inside_coord_y_bottom], 
                [cell_inside_coord_x_end, cell_inside_coord_y_top]
            ])
            # cv2.drawContours(image=output, contours=[cell_contour], contourIdx=-1, color=tuple(np.random.random(size=3) * 256), thickness=2)
            cv2.drawContours(image=output, contours=[cell_contour], contourIdx=-1, color=(0, 0, 255), thickness=1)

            cell_img = chest_gui_chest_part[
                cell_inside_coord_y_top:cell_inside_coord_y_bottom, 
                cell_inside_coord_x_start:cell_inside_coord_x_end
            ]

            cells_img_list.append(cell_img)

            if debug:
                cv2.imshow("cell_img", cell_img)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

    if debug:
        cv2.imshow("Cells contour", output)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return cells_img_list


def get_empty_cell_numbers(chest_gui_cell_parts_imgs):
    blank_cell_number_list = []
    cell_number = 0
    for cell_img in chest_gui_cell_parts_imgs:
        resized_cell_img = cv2.resize(src=cell_img, dsize=(64, 64), interpolation=cv2.INTER_AREA)
        diff = np.abs(MINECRAFT_ITEM_AIR - resized_cell_img)
        nonzero_pixels = np.count_nonzero(diff)
        diff_height = diff.shape[0]
        diff_width = diff.shape[1]
        diff_channel = diff.shape[2]
        all_pixels_count = diff_height * diff_width * diff_channel
        similarity = 1 - (nonzero_pixels / all_pixels_count)

        if similarity > 0.9:
            # print("cell_number", cell_number)
            # print("nonzero_pixels", nonzero_pixels)
            # print("all_pixels_count", all_pixels_count)
            # print("similarity", similarity)
            blank_cell_number_list.append(cell_number)

        cell_number = cell_number + 1

    return blank_cell_number_list


def compare_image_similarity(image1, image2, debug=False):
    # image2 should be the one cropped from the chest GUI image.

    img1_height = image1.shape[0]
    img1_width = image1.shape[1]
    img2_height = image2.shape[0]
    img2_width = image2.shape[1]

    if img1_height != img2_height:
        print("height is not same.", "img1_height:", img1_height, ",img2_height", img2_height)
        return
    if img1_width != img2_width:
        print("width is not same.", "img1_width:", img1_width, ",img2_width", img2_width)
        return

    if debug:
        cv2.imshow("image1", image1)
        cv2.imshow("image2", image2)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    img_height = image1.shape[0]
    img_width = image1.shape[1]
    img_channel = image1.shape[2]
    all_pixels_count = img_height * img_width * img_channel

    # Numpy absolute difference
    diff = np.abs(image1 - image2)
    diff_nonzero_pixels = np.count_nonzero(diff)
    similarity = 1 - (diff_nonzero_pixels / all_pixels_count)
    
    # if debug:
    # if similarity > ITEM_SIMILARITY_THRESHOLD:
        # cv2.namedWindow("image1")
        # cv2.imshow("image1", image1)
        # cv2.moveWindow("image1", 100, 200)

        # cv2.namedWindow("image2")
        # cv2.imshow("image2", image2)
        # cv2.moveWindow("image2", 200, 200)

        # cv2.namedWindow("diff")
        # cv2.imshow("diff", diff)
        # cv2.moveWindow("diff", 300, 200)
        
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        # print("all_pixels_count:", all_pixels_count)
        # print("diff_nonzero_pixels:", diff_nonzero_pixels)
        # print("similarity:", similarity)

    return similarity


def load_items_img_from_folder(folder, item_category):
    files_to_skip_msg = ""
    for i in IMAGE_FILES_TO_SKIP:
        files_to_skip_msg = files_to_skip_msg + i + ", "

    items = []
    for filename in os.listdir(folder):
        # Skip other items that might cause problems.
        if filename in IMAGE_FILES_TO_SKIP:
            continue

        # if filename != "allium.png":
        #     continue

        img = cv2.imread(os.path.join(folder, filename))
        if img is not None:
            items.append((img, filename, item_category))
    return items


def identify_item_in_cell_img(cell_img):
    max_similarity = 0

    for item_img in ITEMS_IMG:
        item_img_img = item_img[0]
        item_img_name = item_img[1]
        item_category = item_img[2]

        similarity = compare_image_similarity(image1=item_img_img, image2=cell_img, debug=False)
        
        if similarity > max_similarity:
            max_similarity = similarity
            max_similarity_img_name = item_img_name
            max_similarity_item_category = item_category
    
    return (max_similarity_img_name, max_similarity, max_similarity_item_category)


def get_cell_coords(
        inventory_img_width, 
        inventory_img_height, 
        corners_of_chest_gui_list,
        chest_gui_chest_part_width, 
        chest_gui_chest_part_height, 
        is_chest_large):

    if is_chest_large:
        chest_part_y_top = round(inventory_img_height / 13.47692)
    else:
        chest_part_y_top = round(inventory_img_height / 10.15385)
    chest_part_x_start = round(inventory_img_width / 27.84)

    col_count = 9
    row_count = 3
    if is_chest_large:
        row_count = 6

    step_x = round(chest_gui_chest_part_width / col_count)
    step_y = round(chest_gui_chest_part_height / row_count)

    # The center coord of each cell.
    cell_coord_list = []

    # Loop over the grid locations.
    for y in range(0, row_count):
        for x in range(0, col_count):
            # Compute the starting and ending (x, y) coordinates of the current cell.
            start_x = x * step_x
            start_y = y * step_y
            end_x = (x + 1) * step_x
            end_y = (y + 1) * step_y

            chest_top_left_corner_coord = corners_of_chest_gui_list[0]
            cell_center_x = round((start_x + end_x) / 2)
            cell_center_y = round((start_y + end_y) / 2)
            cell_center = (
                cell_center_x + chest_top_left_corner_coord[0] + chest_part_x_start, 
                cell_center_y + chest_top_left_corner_coord[1] + chest_part_y_top)
            cell_coord_list.append(cell_center)
    
    return cell_coord_list


# Load minecraft item images.
if len(ITEMS_IMG) == 0:
    ITEMS_IMG.extend(load_items_img_from_folder(os.path.join(MINECRAFT_ITEMS_IMG_FOLDER, SUBFOLDER_BUILDING_BLOCKS), constants.ITEM_CATEGORY["building_blocks"]))
    ITEMS_IMG.extend(load_items_img_from_folder(os.path.join(MINECRAFT_ITEMS_IMG_FOLDER, SUBFOLDER_FOODS), constants.ITEM_CATEGORY["foods"]))
    ITEMS_IMG.extend(load_items_img_from_folder(os.path.join(MINECRAFT_ITEMS_IMG_FOLDER, SUBFOLDER_MINERALS), constants.ITEM_CATEGORY["minerals"]))
    ITEMS_IMG.extend(load_items_img_from_folder(os.path.join(MINECRAFT_ITEMS_IMG_FOLDER, SUBFOLDER_OTHER), constants.ITEM_CATEGORY["other"]))
    ITEMS_IMG.extend(load_items_img_from_folder(os.path.join(MINECRAFT_ITEMS_IMG_FOLDER, SUBFOLDER_REDSTONE_COMPONENTS), constants.ITEM_CATEGORY["redstone_components"]))
    ITEMS_IMG.extend(load_items_img_from_folder(os.path.join(MINECRAFT_ITEMS_IMG_FOLDER, SUBFOLDER_WEAPONS_ARMORS_TOOLS), constants.ITEM_CATEGORY["weapons_armors_tools"]))
    

def identify_chest_item(image, debug=False):
    if debug:
        print("minecraft items in folder:", len(ITEMS_IMG))

    try:
        chest_gui_img, corners_of_chest_gui_list = crop_chest_gui(image=image, debug=debug)
    except Exception as err:
        raise err
    
    is_chest_gui = is_image_a_chest_gui(chest_gui_img, debug=debug)
    if not is_chest_gui:
        raise Exception(constants.EXCEPTION_CHEST_NOT_DETECTED)

    chest_gui_chest_part_img, is_chest_large = crop_chest_gui_chest_part(chest_gui_img, debug=debug)
    chest_gui_cell_parts_imgs = crop_chest_cells(chest_gui_chest_part_img, is_chest_large, debug=debug)
    empty_cell_number_list = get_empty_cell_numbers(chest_gui_cell_parts_imgs)

    cell_coord_list = get_cell_coords(
        chest_gui_img.shape[1],
        chest_gui_img.shape[0],
        corners_of_chest_gui_list,
        chest_gui_chest_part_img.shape[1],
        chest_gui_chest_part_img.shape[0],
        is_chest_large
    )

    cell_details_list = []
    for index, cell_img in enumerate(chest_gui_cell_parts_imgs):

        if index in empty_cell_number_list:
            cell_details_list.append((None, cell_coord_list[index], None))
            continue

        resized_cell_img = cv2.resize(src=cell_img, dsize=(ITEMS_IMG_WIDTH, ITEMS_IMG_HEIGHT), interpolation=cv2.INTER_AREA)

        max_similarity_img_name, max_similarity, item_category = identify_item_in_cell_img(resized_cell_img)
        if debug:
            print("chest GUI cell index:", index, "-", "max_similarity:", max_similarity, "(" + max_similarity_img_name + ")")

        cell_details_list.append((max_similarity_img_name, cell_coord_list[index], item_category))

    if debug:
        output = image.copy()
        for coord in cell_coord_list:
            output = cv2.rectangle(img=output, pt1=(coord[0], coord[1]), pt2=(coord[0] + 1, coord[1] + 1), color=(180, 255, 0), thickness=5)
            cv2.imshow("cell_coord_list", output)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

    return cell_details_list

import cv2
import mouse

import constants
import screenshot_handler
import minecraft_chest_identifier

EMPTY_ITEM_CELL = 9999
MOUSE_MOVE_SPEED = 0.01
MOUSE_INIT_MOVE_OUTSIDE = 0.1

def item_names_to_number_lexicographically(item_names_and_coords):
    arr_len = len(item_names_and_coords)
    index_to_skip = []
    # Initializes all the arr_len spaces with [9999, (None, None)] (indicating empty item with no coordinate)
    numerized = [(EMPTY_ITEM_CELL, (None, None))] * arr_len
    number = 0
    
    for i in range(arr_len):
        min_item_name = "zzzzz"
        min_index = -1
        for j, e in enumerate(item_names_and_coords):
            e_item_name = e[0]
            if e_item_name == None:
                continue
            if j in index_to_skip:
                continue
            if e_item_name < min_item_name:
                min_item_name = e_item_name
                min_index = j
        if min_index != -1:
            numerized[min_index] = (number, item_names_and_coords[min_index][1])
            # numerized other cells with similar item as min_index.
            for k, e2 in enumerate(item_names_and_coords):
                e2_item_name = e2[0]
                if e2_item_name == None:
                    continue
                if k in index_to_skip:
                    continue
                if e2_item_name == min_item_name:
                    numerized[k] = (number, item_names_and_coords[k][1])
                    index_to_skip.append(k)

            index_to_skip.append(min_index)
            number = number + 1
        
    return numerized
    

def printChest(item_names_with_coords, highlight_a, highlight_b):
    for i, e in enumerate(item_names_with_coords):
        e_item_name = e[0]
        if i != 0 and (i) % 9 == 0:
            print()

        if e_item_name == EMPTY_ITEM_CELL:
            if i == highlight_a:
                print("(-)", end="")
            elif i == highlight_b:
                print("[-]", end="")
            else:
                print(" - ", end="")
            continue
        
        if i == highlight_a:
            print("(" + str(e_item_name) + ")", end="")
        elif i == highlight_b:
            print("[" + str(e_item_name) + "]", end="")
        else:    
            print(" " + str(e_item_name) + " ", end="")
    print()
    print()


def sort_ascending(item_num_and_coord, debug):
    '''Sort ascendingly using a modified selectionSort.'''
    item_num_and_coord_copy = item_num_and_coord[:]
    moves = []
    for i in range(len(item_num_and_coord_copy)):
        # Find the minimum element in remaining unsorted array
        min_idx = i
        for j in range(i + 1, len(item_num_and_coord_copy)):
            if item_num_and_coord_copy[j][0] == EMPTY_ITEM_CELL:
                continue
            if item_num_and_coord_copy[min_idx] > item_num_and_coord_copy[j]:
                min_idx = j
        # If item to move is empty cell, skip.
        if item_num_and_coord_copy[min_idx][0] == EMPTY_ITEM_CELL:
            continue
        # If the move is on the same cell, skip.
        if i == min_idx:
            continue

        moves.append((min_idx, i))
        # If cell to move to is not empty, then swap.
        if item_num_and_coord_copy[i][0] != EMPTY_ITEM_CELL:
            moves.append((i, min_idx))

        if debug:
            print("sort_ascending debug")
            printChest(item_num_and_coord_copy, min_idx, i)

        temp = item_num_and_coord_copy[min_idx]
        item_num_and_coord_copy[min_idx] = item_num_and_coord_copy[i]
        item_num_and_coord_copy[i] = temp

    if debug:
        print("sort_ascending debug")
        printChest(item_num_and_coord_copy, min_idx, i)

    return moves


def sort_by_category(item_num_and_coord, cell_details_list, debug=False):
    '''Sort items based on category.'''

    category_hierarchy = [
        constants.ITEM_CATEGORY["minerals"],
        constants.ITEM_CATEGORY["building_blocks"],
        constants.ITEM_CATEGORY["redstone_components"],
        constants.ITEM_CATEGORY["other"],
        constants.ITEM_CATEGORY["weapons_armors_tools"],
        constants.ITEM_CATEGORY["foods"]
    ]

    if debug:
        print("item_num_and_coord:", item_num_and_coord)
        print("cell_details_list:", cell_details_list)

    item_num_and_coord_copy = item_num_and_coord[:]
    cell_details_list_copy = cell_details_list[:]

    moves = []
    
    current_cell = 0

    for category in category_hierarchy:
        for i in range(current_cell, len(item_num_and_coord_copy)):
            item_num = item_num_and_coord_copy[i][0]
            if item_num == EMPTY_ITEM_CELL:
                continue
            item_category = cell_details_list_copy[i][2]
            if item_category == category:
                if debug:
                    print("category:", category)
                    print("sort_by_category debug")
                    printChest(item_num_and_coord_copy, i, current_cell)

                # If move is on the same cell, skip.
                if i == current_cell:
                    current_cell = current_cell + 1
                    continue

                moves.append((i, current_cell))
                # If target cell is not empty, swap.
                if item_num_and_coord_copy[current_cell][0] != EMPTY_ITEM_CELL:
                    moves.append((current_cell, i))

                temp = item_num_and_coord_copy[current_cell]
                item_num_and_coord_copy[current_cell] = item_num_and_coord_copy[i]
                item_num_and_coord_copy[i] = temp

                temp = cell_details_list_copy[current_cell]
                cell_details_list_copy[current_cell] = cell_details_list_copy[i]
                cell_details_list_copy[i] = temp

                current_cell = current_cell + 1

    if debug:
        print("sort_by_category debug")
        printChest(item_num_and_coord_copy, -1, -1)

    return moves

def sort_items(cell_details_list, item_num_and_coord, moves, debug=False):
    chest_virtual_copy = item_num_and_coord[:]

    for move in moves:
        cell_index_from = move[0]
        cell_index_to = move[1]
        coord_from = cell_details_list[cell_index_from][1]
        coord_to = cell_details_list[cell_index_to][1]

        if debug:
            print(coord_from, "->", coord_to, end=", ")

        x_from = coord_from[0]
        y_from = coord_from[1]
        x_to = coord_to[0]
        y_to = coord_to[1]

        mouse.move(x_from, y_from, duration=MOUSE_MOVE_SPEED)
        mouse.click(button="left")
        mouse.move(x_to, y_to, duration=MOUSE_MOVE_SPEED)
        mouse.click(button="left")

        temp = chest_virtual_copy[cell_index_from]
        chest_virtual_copy[cell_index_from] = chest_virtual_copy[cell_index_to]
        chest_virtual_copy[cell_index_to] = temp
    if debug:
        print()


def move_mouse_outside():
    mouse.move(100, 100, duration=MOUSE_INIT_MOVE_OUTSIDE)


def get_duplicates_in_item_name(lexi_numerized_item_name_and_coord):
    seen = set()
    duplicates = []

    for item in lexi_numerized_item_name_and_coord:
        item_name = item[0]
        if item_name in seen:
            if item_name not in duplicates:
                duplicates.append(item_name)
        else:
            seen.add(item_name)

    return duplicates


def stack_similar_items(item_num_and_coord, debug):
    duplicates = get_duplicates_in_item_name(item_num_and_coord)

    if debug:
        print("duplicates:", duplicates)

    for item in item_num_and_coord:
        item_number = item[0]
        item_coord = item[1]

        if item_number == EMPTY_ITEM_CELL:
            continue
        if item_number not in duplicates:
            continue

        x = item_coord[0]
        y = item_coord[1]

        # Triple click to stack items and put back in position
        mouse.move(x, y, duration=MOUSE_MOVE_SPEED)
        mouse.click(button="left")
        mouse.click(button="left")
        mouse.click(button="left")


def take_read_delete_screenshot(monitor_number):
    screenshot_filepath = screenshot_handler.take_screenshot(monitor_number)
    screenshot_image = cv2.imread(screenshot_filepath)
    screenshot_handler.delete_screenshot(screenshot_filepath)
    return screenshot_image


def identify_items(monitor_number, debug=False):
    # Move mouse away from item to prevent the item name popup from showing which will mess up the screenshot and identification.
    move_mouse_outside()
    # Take screenshot and identify items
    screenshot_image = take_read_delete_screenshot(monitor_number)

    # Start identifying all items in the chest in the screenshot if there is, else raise an exception.
    try:
        cell_details_list = minecraft_chest_identifier.identify_chest_item(screenshot_image, debug=debug)
    except Exception as err:
        raise err

    # Get item names and coords from the cell_details_list.
    item_names_and_coords = []
    for cell_detail in cell_details_list:
        item_names_and_coords.append((cell_detail[0], cell_detail[1]))

    # Change item names to number form to easily sort.
    item_num_and_coord = item_names_to_number_lexicographically(item_names_and_coords)
    if debug:
        print("item_num_and_coord:", item_num_and_coord)
        print()

    return (cell_details_list, item_num_and_coord)


def sort(monitor_number, sort_type):
    debug = False

    try:
        cell_details_list, item_num_and_coord = identify_items(monitor_number, debug=debug)
    except Exception as err:
        print("An Exception occured:", err)
        return err

    # Stack items first before sorting.
    stack_similar_items(item_num_and_coord, debug=debug)

    try:
        cell_details_list, item_num_and_coord = identify_items(monitor_number, debug=debug)
    except Exception as err:
        print("An Exception occured:", err)
        return err

    if sort_type == constants.SORT_TYPES["Alphabetical"]:
        moves = sort_ascending(item_num_and_coord, debug=debug)
    elif sort_type == constants.SORT_TYPES["Categorized"]:
        moves = sort_by_category(item_num_and_coord, cell_details_list, debug=debug)

    sort_items(cell_details_list, item_num_and_coord, moves, debug=debug)

    if debug:
        # print("sorted_number:", sorted_items_arr)
        print()
        print("Number of moves:", len(moves))
        print("moves:")
        for move in moves:
            print(move[0], "->", move[1], end=", ")
        print() 

    return constants.SORT_RETURN_SUCCESS
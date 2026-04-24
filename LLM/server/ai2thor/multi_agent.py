import math
import re
import shutil
import subprocess
import time
import threading
import cv2
import numpy as np
from ai2thor.controller import Controller
from scipy.spatial import distance
from typing import Tuple
from collections import deque
import random
import os
from glob import glob
from scipy.optimize import linear_sum_assignment
import csv
import json
from typing import Tuple

def closest_node(node, nodes, no_robot, clost_node_location):
    crps = []
    distances = distance.cdist([node], nodes)[0]
    dist_indices = np.argsort(np.array(distances))
    for i in range(no_robot):
        pos_index = dist_indices[(i * 5) + clost_node_location[i]]
        crps.append(nodes[pos_index])
    return crps

def distance_pts(p1: Tuple[float, float, float], p2: Tuple[float, float, float]):
    return ((p1[0] - p2[0]) ** 2 + (p1[2] - p2[2]) ** 2) ** 0.5

def distance_between_positions(agent_pos, task_pos):
    if isinstance(agent_pos, dict):
        agent_pos = (agent_pos["x"], agent_pos["y"], agent_pos["z"])
    if isinstance(task_pos, dict):
        task_pos = (task_pos["x"], task_pos["y"], task_pos["z"])
    
    distance = math.sqrt((agent_pos[0] - task_pos[0]) ** 2 + 
                         (agent_pos[1] - task_pos[1]) ** 2 + 
                         (agent_pos[2] - task_pos[2]) ** 2)
    return distance

floor_no = 3

c = Controller(height=986, width=1754)
c.reset("FloorPlan" + str(floor_no))

agents = [
    {"id": 0, "position":(), 'skills': ['GoToObject', 'OpenObject', 'CloseObject', 'TurnOn', 'TurnOff'], "available": True},  # Tác nhân 1
    {"id": 1, "position":(), 'skills': ['GoToObject', 'OpenObject', 'CloseObject', 'TurnOn', 'TurnOff'], "available": True},  # Tác nhân 2 (bận)
    #{"id": 2, "position":(), 'skills': ['GoToObject', 'OpenObject', 'CloseObject', 'TurnOn', 'TurnOff'], "available": True},   # Tác nhân 3
    # {"id": 3, "position":(), 'skills': ['GoToObject', 'OpenObject', 'CloseObject', 'TurnOn', 'TurnOff'], "available": True}    # Tác nhân 4
]
no_robot = len(agents)

multi_agent_event = c.step(dict(action='Initialize', agentMode="default", snapGrid=False, gridSize=0.25, rotateStepDegrees=20, visibilityDistance=100, fieldOfView=90, agentCount=no_robot))

reachable_positions_ = c.step(action="GetReachablePositions").metadata["actionReturn"]
reachable_positions = positions_tuple = [(p["x"], p["y"], p["z"]) for p in reachable_positions_]

# randomize postions of the agents
for i in range (no_robot):
    init_pos = random.choice(reachable_positions_)
    agents[i]['position'] = init_pos
    c.step(dict(action="Teleport", position=init_pos, agentId=i))
    print(f"Agent {agents[i]['id']} new position: {agents[i]['position']}")

action_queue = []
task_over = False

def exec_actions():
    img_counter = 0
    while not task_over:
        if len(action_queue) > 0:
            try:
                act = action_queue[0]
                if act['action'] == 'ObjectNavExpertAction':
                    multi_agent_event = c.step(dict(action=act['action'], position=act['position'], agentId=act['agent_id']))
                    next_action = multi_agent_event.metadata['actionReturn']

                    if next_action is not None:
                        multi_agent_event = c.step(action=next_action, agentId=act['agent_id'], forceAction=True)

                elif act['action'] == 'MoveAhead':
                    multi_agent_event = c.step(action="MoveAhead", agentId=act['agent_id'])

                elif act['action'] == 'MoveBack':
                    multi_agent_event = c.step(action="MoveBack", agentId=act['agent_id'])

                elif act['action'] == 'RotateLeft':
                    multi_agent_event = c.step(action="RotateLeft", degrees=act['degrees'], agentId=act['agent_id'])

                elif act['action'] == 'RotateRight':
                    multi_agent_event = c.step(action="RotateRight", degrees=act['degrees'], agentId=act['agent_id'])

                elif act['action'] == 'PickupObject':
                    multi_agent_event = c.step(action="PickupObject", objectId=act['objectId'], agentId=act['agent_id'], forceAction=True)

                elif act['action'] == 'PutObject':
                    multi_agent_event = c.step(action="PutObject", objectId=act['objectId'], agentId=act['agent_id'], forceAction=True)

                elif act['action'] == 'ToggleObjectOn':
                    multi_agent_event = c.step(action="ToggleObjectOn", objectId=act['objectId'], agentId=act['agent_id'], forceAction=True)

                elif act['action'] == 'ToggleObjectOff':
                    multi_agent_event = c.step(action="ToggleObjectOff", objectId=act['objectId'], agentId=act['agent_id'], forceAction=True)

                elif act['action'] == 'Done':
                    multi_agent_event = c.step(action="Done")

            except Exception as e:
                print(e)

                for i, e in enumerate(multi_agent_event.events):
                    if os.path.exists(e.cv2img):
                        print("e.cv2img", e.cv2img)
                        img = cv2.imread(e.cv2img)
                        cv2.imshow('agent%s' % i, img)
                    f_name = os.path.dirname(__file__) + "/agent_" + str(i+1) + "/img_" + str(img_counter).zfill(5) + ".png"
                    cv2.imwrite(f_name, e.cv2img)

                    # Save the image from the ThirdPartyCamera
                    top_view_rgb = c.last_event.events[0].third_party_camera_frames[-1]
                    if top_view_rgb is not None:  # Check if the image exists
                        f_name = os.path.dirname(__file__) + "/top_view/top_view_img_" + str(img_counter).zfill(5) + ".png"
                        top_view_rgb = cv2.cvtColor(top_view_rgb, cv2.COLOR_BGR2RGB)
                        cv2.imwrite(f_name, top_view_rgb)  # Save the top view image
                        #print(f"Saved top view image to {f_name}")  # Log the save action

                if cv2.waitKey(25) & 0xFF == ord('q'):
                    break
            
            img_counter += 1    
            action_queue.pop(0)

actions_thread = threading.Thread(target=exec_actions)
actions_thread.start()

def GoToObject(agents, dest_obj):
    print("Going to ", dest_obj)
    
    # Kiểm tra nếu agents là một danh sách
    if not isinstance(agents, list):
        agents = [agents]  # Chuyển đổi thành danh sách nếu cần
    no_agents = len(agents)
    
    # Khoảng cách tới mục tiêu của các tác nhân
    dist_goals = [10.0] * len(agents)
    prev_dist_goals = [10.0] * len(agents)
    count_since_update = [0] * len(agents)
    clost_node_location = [0] * len(agents)
    
    # Danh sách các đối tượng trong cảnh và các tọa độ của chúng
    objs = list([obj["objectId"] for obj in c.last_event.metadata["objects"]])
    objs_center = list([obj["axisAlignedBoundingBox"]["center"] for obj in c.last_event.metadata["objects"]])

    # Tìm ID và tọa độ của đối tượng đích
    for idx, obj in enumerate(objs):
        match = re.match(dest_obj, obj)
        if match is not None:
            dest_obj_id = obj
            dest_obj_center = objs_center[idx]
            break  # Tìm thấy đối tượng đầu tiên khớp với yêu cầu
    
    dest_obj_pos = [dest_obj_center['x'], dest_obj_center['y'], dest_obj_center['z']] 
    
    # Tìm điểm gần nhất có thể tiếp cận cho mỗi tác nhân
    crp = closest_node(dest_obj_pos, reachable_positions, no_agents, clost_node_location)
    
    goal_thresh = 0.3  # Ngưỡng để coi là đã đạt đến mục tiêu
    
    # Lặp cho đến khi tất cả các tác nhân đều đã gần mục tiêu
    while all(d > goal_thresh for d in dist_goals):
        for ia, agent in enumerate(agents):
            # agent_name = agent['name']
            agent_id = agent['id']  # Sử dụng 'id' của tác nhân thay vì 'name'
            
            # Lấy thông tin metadata của tác nhân
            metadata = c.last_event.events[agent_id].metadata
            location = {
                "x": metadata["agent"]["position"]["x"],
                "y": metadata["agent"]["position"]["y"],
                "z": metadata["agent"]["position"]["z"],
                "rotation": metadata["agent"]["rotation"]["y"],
                "horizon": metadata["agent"]["cameraHorizon"]}
            
            prev_dist_goals[ia] = dist_goals[ia]  # Lưu khoảng cách trước đó
            dist_goals[ia] = distance_pts([location['x'], location['y'], location['z']], crp[ia])
            
            dist_del = abs(dist_goals[ia] - prev_dist_goals[ia])
            print(ia, "Dist to Goal: ", dist_goals[ia], dist_del, clost_node_location[ia])
            
            if dist_del < 0.2:
                # Nếu tác nhân không di chuyển
                count_since_update[ia] += 1
            else:
                # Nếu tác nhân đang di chuyển
                count_since_update[ia] = 0
                
            if count_since_update[ia] < 15:
                action_queue.append({'action': 'ObjectNavExpertAction', 'position': dict(x=crp[ia][0], y=crp[ia][1], z=crp[ia][2]), 'agent_id': agent_id})
            else:
                # Cập nhật mục tiêu
                clost_node_location[ia] += 1
                count_since_update[ia] = 0
                crp = closest_node(dest_obj_pos, reachable_positions, no_agents, clost_node_location)
    
            time.sleep(0.5)

    # Căn chỉnh tác nhân khi mục tiêu đã đạt
    # Tính toán góc giữa hướng của robot và đối tượng
    metadata = c.last_event.events[agent_id].metadata
    robot_location = {
        "x": metadata["agent"]["position"]["x"],
        "y": metadata["agent"]["position"]["y"],
        "z": metadata["agent"]["position"]["z"],
        "rotation": metadata["agent"]["rotation"]["y"],
        "horizon": metadata["agent"]["cameraHorizon"]}
    
    robot_object_vec = [dest_obj_pos[0] - robot_location['x'], dest_obj_pos[2] - robot_location['z']]
    y_axis = [0, 1]
    unit_y = y_axis / np.linalg.norm(y_axis)
    unit_vector = robot_object_vec / np.linalg.norm(robot_object_vec)
    
    angle = math.atan2(np.linalg.det([unit_vector, unit_y]), np.dot(unit_vector, unit_y))
    angle = 360 * angle / (2 * np.pi)
    angle = (angle + 360) % 360
    rot_angle = angle - robot_location['rotation']
    
    if rot_angle > 0:
        action_queue.append({'action': 'RotateRight', 'degrees': abs(rot_angle), 'agent_id': agent_id})
    else:
        action_queue.append({'action': 'RotateLeft', 'degrees': abs(rot_angle), 'agent_id': agent_id})
        
    print("Reached: ", dest_obj)

def turnOn(robot, sw_obj):
    GoToObject(robot, sw_obj)
    # robot_name = robot['name']
    # agent_id = int(robot_name[-1]) - 1
    agent_id = agent['id'] 
    objs = list(set([obj["objectId"] for obj in c.last_event.metadata["objects"]]))
    
    for obj in objs:
        match = re.match(sw_obj, obj)
        if match is not None:
            sw_obj_id = obj
            break # find the first instance
    
    action_queue.append({'action':'ToggleObjectOn', 'objectId':sw_obj_id, 'agent_id':agent_id})    
    c.last_event = multi_agent_event  

    time.sleep(1)

def turnOff(robot, sw_obj):
    GoToObject(robot, sw_obj)
    # robot_name = robot['name']
    # agent_id = int(robot_name[-1]) - 1
    agent_id = agent['id'] 
    objs = list(set([obj["objectId"] for obj in c.last_event.metadata["objects"]]))
    
    for obj in objs:
        match = re.match(sw_obj, obj)
        if match is not None:
            sw_obj_id = obj
            break 
    
    action_queue.append({'action':'ToggleObjectOff', 'objectId':sw_obj_id, 'agent_id':agent_id})   
    c.last_event = multi_agent_event  

    time.sleep(1)

def PickupObject(robot, pick_obj):
    GoToObject(robot, pick_obj)
    agent_id = agent['id'] 
    objs = list(set([obj["objectId"] for obj in c.last_event.metadata["objects"]]))
    
    for obj in objs:
        match = re.match(pick_obj, obj)
        if match is not None:
            pick_obj_id = obj
            break # find the first instance
        
    action_queue.append({'action':'PickupObject', 'objectId':pick_obj_id, 'agent_id':agent_id})

def OpenObject(robot, sw_obj):
    GoToObject(robot, sw_obj)
    agent_id = agent['id'] 
    objs = list(set([obj["objectId"] for obj in c.last_event.metadata["objects"]]))
    
    for obj in objs:
        match = re.match(sw_obj, obj)
        if match is not None:
            sw_obj_id = obj
            break 
    
    action_queue.append({'action':'OpenObject', 'objectId':sw_obj_id, 'agent_id':agent_id})
    c.last_event = multi_agent_event  

    time.sleep(1)
    
def CloseObject(robot, sw_obj):
    # robot_name = robot['name']
    # agent_id = int(robot_name[-1]) - 1
    GoToObject(robot, sw_obj)
    objs = list(set([obj["objectId"] for obj in c.last_event.metadata["objects"]]))
    
    for obj in objs:
        match = re.match(sw_obj, obj)
        if match is not None:
            sw_obj_id = obj
            break 
    
    action_queue.append({'action':'CloseObject', 'objectId':sw_obj_id, 'agent_id':agent_id}) 
    c.last_event = multi_agent_event  

    time.sleep(1)

# After all tasks are done, display images on the main thread
def display_images():
    img_counter = 0
    while img_counter < 100:  # Set a limit to avoid infinite loop
        for i in range(no_robot):
            img_path = os.path.dirname(__file__) + "/agent_" + str(i+1) + "/img_" + str(img_counter).zfill(5) + ".png"
            if os.path.exists(img_path):
                img = cv2.imread(img_path)
                cv2.imshow(f'Agent {i+1}', img)
        img_counter += 1
 
def PutObject(robot, put_obj, recp):
    GoToObject(robot, recp)
    robot_name = robot['name']
    agent_id = int(robot_name[-1]) - 1
    objs = list(set([obj["objectId"] for obj in c.last_event.metadata["objects"]]))
    objs_center = list([obj["axisAlignedBoundingBox"]["center"] for obj in c.last_event.metadata["objects"]])
    objs_dists = list([obj["distance"] for obj in c.last_event.metadata["objects"]])

    metadata = c.last_event.events[agent_id].metadata
    robot_location = [metadata["agent"]["position"]["x"], metadata["agent"]["position"]["y"], metadata["agent"]["position"]["z"]]
    dist_to_recp = 9999999 # distance b/w robot and the recp obj
    for idx, obj in enumerate(objs):
        match = re.match(recp, obj)
        if match is not None:
            dist = objs_dists[idx]# distance_pts(robot_location, [objs_center[idx]['x'], objs_center[idx]['y'], objs_center[idx]['z']])
            if dist < dist_to_recp:
                recp_obj_id = obj
                dest_obj_center = objs_center[idx]
                dist_to_recp = dist
    action_queue.append({'action':'PutObject', 'objectId':recp_obj_id, 'agent_id':agent_id})

# tasks = [
#     {"id": 1, "position": (-0.27330246567726135, 0.7008301019668579, 3.612398624420166), "is_done": False},      # Công việc 1 (chưa hoàn thành)
#     {"id": 2, "position": ( -0.5663970708847046, 0.002758622169494629, 0.0244576558470726), "is_done": False},   # Công việc 2 (đã hoàn thành)
#     {"id": 3, "position": (-2.357048511505127, 1.2058273553848267, 6.245577812194824), "is_done": False},       # Công việc 3 (chưa hoàn thành)
# ]

def create_tasks_from_csv(file_path):
    tasks = []
    i = 0;
    # Đọc file CSV
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Chỉ xử lý những task có status là "not done"
            if row['Status'].strip().lower() == 'not done':
                # Giả sử 'RoomNumber' là cột trong file CSV chứa số hiệu căn phòng
                room_number = row['RoomNumber'].strip()  # Hoặc lấy giá trị mặc định nếu không có cột này

                # Lấy position từ get_object_position
                position_dict = get_object_position(row['Object'], room_number)
                # Chuyển position dict thành tuple (x, y, z)
                task = {
                    "id": i,
                    "id_prompt": int(row['ID']),  # ID từ cột "ID"
                    "object": 'Object',
                    "position": position_dict
                }
                i+=1
                tasks.append(task)
    
    # Sắp xếp tasks theo ID tăng dần
    tasks.sort(key=lambda x: x["id_prompt"])

    return tasks


def get_object_position(object_name, room_number):
    # Đọc dữ liệu từ file JSON
    file_path = f'ai2thor_floor_data/FloorPlan{room_number}_objects.json'
    
    # Kiểm tra nếu file tồn tại
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return (0.0, 0.0, 0.0)  # Trả về vị trí mặc định nếu không tìm thấy file
    
    # Đọc nội dung của file JSON
    with open(file_path, 'r') as file:
        data = json.load(file)

    # Tìm kiếm objectType trong dữ liệu JSON
    for obj in data:
        if obj['objectType'] == object_name:
            x = float(obj['position']['x'])
            y = float(obj['position']['y'])
            z = float(obj['position']['z'])
            position_tuple = (x,y,z)
            return position_tuple 
    print(f"Object {object_name} not found in {file_path}.")
    return (0.0, 0.0, 0.0)

# tasks = create_tasks_from_csv('./tasks.csv')
# available_agents = [agent for agent in agents if agent["available"]]

# # Tạo ma trận chi phí (distance matrix) từ vị trí các tác nhân và công việc
# cost_matrix = np.zeros((len(available_agents), len(tasks)))

# # Tính toán khoảng cách giữa các tác nhân và công việc
# for i, agent in enumerate(available_agents):
#     if agent["available"]: 
#         for j, task in enumerate(tasks):
#             p1 = agent["position"]
#             p2 = task["position"]
#             cost_matrix[i, j] = distance_between_positions(p1, p2)


            
# print("Cost Matrix:")
# print(cost_matrix)
# # Áp dụng thuật toán Hungarian (linear_sum_assignment) để giải quyết bài toán ghép cặp tối ưu
# row_ind, col_ind = linear_sum_assignment(cost_matrix)
# task_threads = []
# def perform_action(object, agent_id, req):
#     robot = agents[agent_id]  # Lấy thông tin tác nhân theo id
#     GoToObject(robot, object)  # Di chuyển tác nhân tới đối tượng
#     if req == "turnOff":
#         turnOff(robot, object)
#     elif req == "turnOn":
#         turnOn(robot, object)
#     elif req == "pickup":
#         PickupObject(robot, object)


# Hàm override để cập nhật file CSV
def override(file_path, i, task):
    # Đọc file CSV
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        rows = list(reader)  # Đọc tất cả các dòng trong file và lưu vào danh sách

    # Duyệt qua các dòng trong CSV và tìm task tương ứng
    for row in rows:
        # Kiểm tra nếu 'ID' trong file CSV khớp với 'id_prompt' của task
        if int(row['ID']) == task['id_prompt']:  # So sánh đúng kiểu dữ liệu
            row['Agent_id'] = str(i + 1)  # Gán Agent_id cho task
            row['Status'] = 'done'  # Cập nhật trạng thái của task thành 'done'
            
            # Tạo một thread để gọi perform_action
            task_thread = threading.Thread(target=perform_action, args=(row['Object'], i, row['Action']))
            task_thread.start()
            task_threads.append(task_thread)  # Thêm thread vào danh sách để theo dõi

    # Ghi lại dữ liệu đã thay đổi vào file CSV
    with open(file_path, mode='w', newline='') as file:
        fieldnames = ['ID', 'user_prompt', 'RoomNumber', 'Object', 'Action', 'Status', 'Agent_id']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()  # Ghi lại tiêu đề cột
        writer.writerows(rows)  # Ghi lại tất cả các dòng đã thay đổi


file_path = '/Users/macbook/Documents/LLM_SM/ai2thor/tasks.csv'

def pickup_pillow(robot):
    PickupObject(robot, 'Pillow')
    GoToObject(robot, 'Sofa')
    PutObject(robot, 'Pillow', 'Sofa')


def pickup_laptop(robot):
    PickupObject(robot, 'Laptop')
    GoToObject(robot, 'SideTable')
    PutObject(robot, 'Laptop', 'SideTable')


action_queue.append({'action':'Done'})
action_queue.append({'action':'Done'})


# for task_thread in task_threads:
#     task_thread.join()

# for task_thread in task_threads:
#     action_queue.append({'action':'Done'})
def open(robot):
    GoToObject(robot, 'Apple')
    # 2: Pick up the Apple.
    PickupObject(robot, 'Apple')
    # 3: Go to the Sink.
    GoToObject(robot, 'Sink')
    # 4: Put the Apple in the Sink.
    PutObject(robot, 'Apple', 'Sink')
    # 5: Switch on the Faucet.
    turnOn(robot, 'Faucet')
    # 6: Wait for a while to let the Apple wash.
    time.sleep(5)
    # 7: Switch off the Faucet.
    turnOff(robot, 'Faucet')

task1_thread = threading.Thread(target=open, args=(agents[0],))
#task2_thread = threading.Thread(target=pickup_apple, args=(robots[1],))
task1_thread.start()
#task2_thread.start()

task1_thread.join()
task_over = True
time.sleep(5)
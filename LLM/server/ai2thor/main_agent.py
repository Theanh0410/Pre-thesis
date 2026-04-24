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
import csv


def closest_node(node, nodes, no_robot, clost_node_location):
    crps = []
    distances = distance.cdist([node], nodes)[0]
    dist_indices = np.argsort(np.array(distances))
    for i in range(no_robot):
        pos_index = dist_indices[(i * 5) + clost_node_location[i]]
        crps.append (nodes[pos_index])
    return crps

def distance_pts(p1: Tuple[float, float, float], p2: Tuple[float, float, float]):
    return ((p1[0] - p2[0]) ** 2 + (p1[2] - p2[2]) ** 2) ** 0.5

def generate_video(input_path, prefix, char_id=0, image_synthesis=['normal'], frame_rate=5, output_path=None):
    """ Generate a video of an episode """
    if output_path is None:
        output_path = input_path

    vid_folder = '{}/{}/{}/'.format(input_path, prefix, char_id)
    if not os.path.isdir(vid_folder):
        print("The input path: {} you specified does not exist.".format(input_path))
    else:
        for vid_mod in image_synthesis:
            command_set = ['ffmpeg', '-i',
                             '{}/Action_%04d_0_{}.png'.format(vid_folder, vid_mod), 
                             '-framerate', str(frame_rate),
                             '-pix_fmt', 'yuv420p',
                             '{}/video_{}.mp4'.format(output_path, vid_mod)]
            subprocess.call(command_set)
            print("Video generated at ", '{}/video_{}.mp4'.format(output_path, vid_mod))

robots = [{'name': 'robot1', 'skills': ['GoToObject', 'OpenObject', 'CloseObject', 'BreakObject', 'SliceObject', 'SwitchOn', 'SwitchOff', 
                                         'SliceObject', 'PickupObject', 'PutObject', 'DropHandObject', 'ThrowObject', 'PushObject', 'PullObject']},
          {'name': 'robot2', 'skills': ['GoToObject', 'OpenObject', 'CloseObject', 'SwitchOn', 'SwitchOff']}]
'''
Choose the type of room for simulation: 
- Kitchen: 1->30
- Living rooms: 201 -> 230
- Bedrooms: 301 -> 330
- Bathrooms: 401 -> 430
'''
floor_no = 202

c = Controller(height=986, width=1754)
c.reset("FloorPlan" + str(floor_no)) 
no_robot = len(robots)

# initialize n agents into the scene
multi_agent_event = c.step(dict(action='Initialize', agentMode="default", snapGrid=False, gridSize=0.25, rotateStepDegrees=20, visibilityDistance=100, fieldOfView=90, agentCount=no_robot))

# add a top view camera
event = c.step(action="GetMapViewCameraProperties")
event = c.step(action="AddThirdPartyCamera", **event.metadata["actionReturn"])

# get reachabel positions
reachable_positions_ = c.step(action="GetReachablePositions").metadata["actionReturn"]
reachable_positions = positions_tuple = [(p["x"], p["y"], p["z"]) for p in reachable_positions_]

# randomize postions of the agents
for i in range (no_robot):
    init_pos = random.choice(reachable_positions_)
    c.step(dict(action="Teleport", position=init_pos, agentId=i))

action_queue = []

task_over = False

def exec_actions():
    # delete if current output already exist
    cur_path = os.getcwd() + "/*/"  # Use os.getcwd() instead of __file__
    for x in glob(cur_path, recursive=True):
        shutil.rmtree(x)
    
    # Create new folders to save the images from the agents
    for i in range(no_robot):
        folder_name = "agent_" + str(i + 1)
        folder_path = os.path.join(os.getcwd(), folder_name)  
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
    
    # Create folder to store the top view images
    folder_name = "top_view"
    folder_path = os.path.join(os.getcwd(), folder_name) 
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    img_counter = 0
    
    while not task_over:
        if len(action_queue) > 0:
            try:
                act = action_queue[0]
                if act['action'] == 'ObjectNavExpertAction':
                    multi_agent_event = c.step(dict(action=act['action'], position=act['position'], agentId=act['agent_id']))
                    next_action = multi_agent_event.metadata['actionReturn']

                    if next_action != None:
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
                print (e)
                
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

def GoToObject(robots, dest_obj):
    print ("Going to ", dest_obj)
    # check if robots is a list
    
    if not isinstance(robots, list):
        # convert robot to a list
        robots = [robots]
    no_agents = len (robots)
    # robots distance to the goal 
    dist_goals = [10.0] * len(robots)
    prev_dist_goals = [10.0] * len(robots)
    count_since_update = [0] * len(robots)
    clost_node_location = [0] * len(robots)
    
    # list of objects in the scene and their centers
    objs = list([obj["objectId"] for obj in c.last_event.metadata["objects"]])
    objs_center = list([obj["axisAlignedBoundingBox"]["center"] for obj in c.last_event.metadata["objects"]])

    # look for the location and id of the destination object
    for idx, obj in enumerate(objs):
        match = re.match(dest_obj, obj)
        if match is not None:
            dest_obj_id = obj
            dest_obj_center = objs_center[idx]
            break # find the first instance
        
    dest_obj_pos = [dest_obj_center['x'], dest_obj_center['y'], dest_obj_center['z']] 
    
    # closest reachable position for each robot
    # all robots cannot reach the same spot 
    # differt close points needs to be found for each robot
    crp = closest_node(dest_obj_pos, reachable_positions, no_agents, clost_node_location)
    
    goal_thresh = 0.3
    # at least one robot is far away from the goal
    
    while all(d > goal_thresh for d in dist_goals):
        for ia, robot in enumerate(robots):
            robot_name = robot['name']
            agent_id = int(robot_name[-1]) - 1
            
            # get the pose of robot        
            metadata = c.last_event.events[agent_id].metadata
            location = {
                "x": metadata["agent"]["position"]["x"],
                "y": metadata["agent"]["position"]["y"],
                "z": metadata["agent"]["position"]["z"],
                "rotation": metadata["agent"]["rotation"]["y"],
                "horizon": metadata["agent"]["cameraHorizon"]}
            
            prev_dist_goals[ia] = dist_goals[ia] # store the previous distance to goal
            dist_goals[ia] = distance_pts([location['x'], location['y'], location['z']], crp[ia])
            
            dist_del = abs(dist_goals[ia] - prev_dist_goals[ia])
            print (ia, "Dist to Goal: ", dist_goals[ia], dist_del, clost_node_location[ia])
            if dist_del < 0.2:
                # robot did not move 
                count_since_update[ia] += 1
            else:
                # robot moving 
                count_since_update[ia] = 0
                
            if count_since_update[ia] < 15:
                action_queue.append({'action':'ObjectNavExpertAction', 'position':dict(x=crp[ia][0], y=crp[ia][1], z=crp[ia][2]), 'agent_id':agent_id})
            else:    
                #updating goal
                clost_node_location[ia] += 1
                count_since_update[ia] = 0
                crp = closest_node(dest_obj_pos, reachable_positions, no_agents, clost_node_location)
    
            time.sleep(0.5)

    # align the robot once goal is reached
    # compute angle between robot heading and object
    metadata = c.last_event.events[agent_id].metadata
    robot_location = {
        "x": metadata["agent"]["position"]["x"],
        "y": metadata["agent"]["position"]["y"],
        "z": metadata["agent"]["position"]["z"],
        "rotation": metadata["agent"]["rotation"]["y"],
        "horizon": metadata["agent"]["cameraHorizon"]}
    
    robot_object_vec = [dest_obj_pos[0] -robot_location['x'], dest_obj_pos[2]-robot_location['z']]
    y_axis = [0, 1]
    unit_y = y_axis / np.linalg.norm(y_axis)
    unit_vector = robot_object_vec / np.linalg.norm(robot_object_vec)
    
    angle = math.atan2(np.linalg.det([unit_vector,unit_y]),np.dot(unit_vector,unit_y))
    angle = 360*angle/(2*np.pi)
    angle = (angle + 360) % 360
    rot_angle = angle - robot_location['rotation']
    
    if rot_angle > 0:
        action_queue.append({'action':'RotateRight', 'degrees':abs(rot_angle), 'agent_id':agent_id})
    else:
        action_queue.append({'action':'RotateLeft', 'degrees':abs(rot_angle), 'agent_id':agent_id})
        
    print ("Reached: ", dest_obj)


def PickupObject(robot, pick_obj):
    robot_name = robot['name']
    agent_id = int(robot_name[-1]) - 1
    objs = list(set([obj["objectId"] for obj in c.last_event.metadata["objects"]]))
    
    for obj in objs:
        match = re.match(pick_obj, obj)
        if match is not None:
            pick_obj_id = obj
            break # find the first instance
        
    action_queue.append({'action':'PickupObject', 'objectId':pick_obj_id, 'agent_id':agent_id})
    
def PutObject(robot, put_obj, recp):
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
         
def SwitchOn(robot, sw_obj):
    robot_name = robot['name']
    agent_id = int(robot_name[-1]) - 1
    objs = list(set([obj["objectId"] for obj in c.last_event.metadata["objects"]]))
    
    for obj in objs:
        match = re.match(sw_obj, obj)
        if match is not None:
            sw_obj_id = obj
            break # find the first instance
    
    action_queue.append({'action':'ToggleObjectOn', 'objectId':sw_obj_id, 'agent_id':agent_id})      
        
def SwitchOff(robot, sw_obj):
    robot_name = robot['name']
    agent_id = int(robot_name[-1]) - 1
    objs = list(set([obj["objectId"] for obj in c.last_event.metadata["objects"]]))
    
    for obj in objs:
        match = re.match(sw_obj, obj)
        if match is not None:
            sw_obj_id = obj
            break # find the first instance
    
    action_queue.append({'action':'ToggleObjectOff', 'objectId':sw_obj_id, 'agent_id':agent_id})      

def OpenObject(robot, sw_obj):
    robot_name = robot['name']
    agent_id = int(robot_name[-1]) - 1
    objs = list(set([obj["objectId"] for obj in c.last_event.metadata["objects"]]))
    
    for obj in objs:
        match = re.match(sw_obj, obj)
        if match is not None:
            sw_obj_id = obj
            break # find the first instance
        
    global recp_id
    if recp_id is not None:
        sw_obj_id = recp_id
    
    GoToObject(robot, sw_obj_id)
    time.sleep(1)
    action_queue.append({'action':'OpenObject', 'objectId':sw_obj_id, 'agent_id':agent_id})
    time.sleep(1)
    
def CloseObject(robot, sw_obj):
    robot_name = robot['name']
    agent_id = int(robot_name[-1]) - 1
    objs = list(set([obj["objectId"] for obj in c.last_event.metadata["objects"]]))
    
    for obj in objs:
        match = re.match(sw_obj, obj)
        if match is not None:
            sw_obj_id = obj
            break # find the first instance
        
    global recp_id
    if recp_id is not None:
        sw_obj_id = recp_id
        
    GoToObject(robot, sw_obj_id)
    time.sleep(1)
    
    action_queue.append({'action':'CloseObject', 'objectId':sw_obj_id, 'agent_id':agent_id}) 
    
    if recp_id is not None:
        recp_id = None
    time.sleep(1)


def SliceObject(robot, sw_obj):
    robot_name = robot['name']
    agent_id = int(robot_name[-1]) - 1
    objs = list(set([obj["objectId"] for obj in c.last_event.metadata["objects"]]))
    
    for obj in objs:
        match = re.match(sw_obj, obj)
        if match is not None:
            sw_obj_id = obj
            break # find the first instance
    
    action_queue.append({'action':'SliceObject', 'objectId':sw_obj_id, 'agent_id':agent_id})

def ThrowObject(robot, throw_obj):
    GoToObject(robot, throw_obj)
    robot_name = robot['name']
    agent_id = int(robot_name[-1]) - 1
    objs = list(set([obj["objectId"] for obj in c.last_event.metadata["objects"]]))
    
    for obj in objs:
        match = re.match(throw_obj, obj)
        if match is not None:
            throw_obj_id = obj
            break  # find the first instance

    # Append the throw action to the action queue
    action_queue.append({'action': 'ThrowObject', 'objectId': throw_obj_id, 'agent_id': agent_id})

# def task(robot):
#     while True:
#         command = input("Enter the object and action (e.g., 'FloorLamp - SwitchOff') or 'exit' to quit: ")
        
#         if command == 'exit':
#             action_queue.append({'action': 'Done'})
#             global task_over
#             task_over = True
#             break

#         try:
#             # Split command into object and action
#             object_name, action, recp = [part.strip() for part in command.split('-')]

#             # robot = robots[0]
#             #GoToObject(robot, object_name)
#             # Call the appropriate action function based on the action part
#             if action == 'Put':
#                 PutObject(robot, object_name, recp)
#             elif action == 'Go':
#                 GoToObject(robot, object_name)
#             elif action == 'Throw':
#                 ThrowObject(robot, object_name)
#             elif action == 'Pickup':
#                 PickupObject(robot, object_name)
#             elif action == 'SwitchOff':
#                 SwitchOff(robot, object_name)
#             elif action == 'SwitchOn':
#                 SwitchOn(robot, object_name)
#             elif action == 'Open':
#                 OpenObject(robot, object_name)
#             elif action == 'Close':
#                 CloseObject(robot, object_name)
#             elif action == 'Slice':
#                 SliceObject(robot, object_name)
#             else:
#                 print(f"Unknown action: {action}")

#         except ValueError:
#             print("Invalid command format. Please use 'ObjectName - Action' format.")
#         except Exception as e:
#             print(f"Error: {e}")

#         action_queue.append({'action': 'Done'})
#         time.sleep(5)

# def task(robot):
#     while True:
#         # Nhận một loạt các lệnh cách nhau bằng dấu phẩy hoặc nhập từng lệnh
#         command_sequence = input("Enter commands separated by commas (e.g., 'Pillow - Go, Pillow - Pickup, Sofa - Go, Pillow - Put - Sofa') or 'exit' to quit: ")
        
#         if command_sequence == 'exit':
#             action_queue.append({'action': 'Done'})
#             global task_over
#             task_over = True
#             break

#         try:
#             # Tách các lệnh thành danh sách
#             commands = [cmd.strip() for cmd in command_sequence.split(',')]
            
#             for command in commands:
#                 # Bỏ qua lệnh trống nếu có
#                 if not command:
#                     continue
                    
#                 # Tách lệnh thành các phần
#                 parts = [part.strip() for part in command.split('-')]
                
#                 # Xác định số lượng phần và hành động tương ứng
#                 if len(parts) == 2:
#                     object_name, action = parts
#                     recp = None
#                 elif len(parts) == 3:
#                     object_name, action, recp = parts
#                 else:
#                     print(f"Invalid command format: {command}")
#                     continue
                
#                 # Thực hiện hành động tương ứng
#                 if action == 'Put':
#                     if recp is None:
#                         print(f"Missing recipient for Put action in command: {command}")
#                         continue
#                     PutObject(robot, object_name, recp)
#                 elif action == 'Go':
#                     GoToObject(robot, object_name)
#                 elif action == 'Throw':
#                     ThrowObject(robot, object_name)
#                 elif action == 'Pickup':
#                     PickupObject(robot, object_name)
#                 elif action == 'SwitchOff':
#                     SwitchOff(robot, object_name)
#                 elif action == 'SwitchOn':
#                     SwitchOn(robot, object_name)
#                 elif action == 'Open':
#                     OpenObject(robot, object_name)
#                 elif action == 'Close':
#                     CloseObject(robot, object_name)
#                 elif action == 'Slice':
#                     SliceObject(robot, object_name)
#                 else:
#                     print(f"Unknown action: {action} in command: {command}")
                
#                 # Thêm trạng thái Done sau mỗi hành động
#                 action_queue.append({'action': 'Done'})
#                 time.sleep(1)  # Thêm delay ngắn giữa các hành động

#         except Exception as e:
#             print(f"Error processing commands: {e}")
            
# task1_thread.start()
# task(robots[0]) 
# task(robots[1])




# task_over = True
# time.sleep(5)
# Hàng đợi lệnh và cờ điều khiển
action_queues = {0: [], 1: []}
all_commands_received = False
task_over = False

def execute_action(robot, action_info):
    """Xử lý từng action theo format if-elif như bạn yêu cầu"""
    action = action_info['action']
    obj = action_info['object']
    recp = action_info.get('recipient')
    
    try:
        if action == 'Go':
            GoToObject(robot, obj)
        elif action == 'Pickup':
            PickupObject(robot, obj)
        elif action == 'Put':
            if not recp:
                print(f"Lỗi: Thiếu đích đến cho hành động Put")
                return
            PutObject(robot, obj, recp)
        elif action == 'Open':
            OpenObject(robot, obj)
        elif action == 'Close':
            CloseObject(robot, obj)
        elif action == 'SwitchOn':
            SwitchOn(robot, obj)
        elif action == 'SwitchOff':
            SwitchOff(robot, obj)
        else:
            print(f"Lỗi: Hành động không hỗ trợ: {action}")
        
        # Thêm trạng thái Done sau mỗi hành động
        action_queues[robots.index(robot)].append({'action': 'Done'})
        time.sleep(1)  # Delay giữa các action
        
    except Exception as e:
        print(f"Lỗi khi thực thi: {e}")

def robot_worker(robot_index):
    """Luồng xử lý cho từng robot"""
    robot = robots[robot_index]
    print(f"{robot['name']} đã sẵn sàng")
    
    # Chờ đến khi nhận đủ lệnh cho cả 2 robot
    while not all_commands_received and not task_over:
        time.sleep(0.1)
    
    # Thực thi lệnh
    while not task_over and action_queues[robot_index]:
        task = action_queues[robot_index].pop(0)
        
        if task['action'] == 'Done':
            break
            
        print(f"\n{robot['name']} thực hiện: {task['action']} {task['object']}")
        execute_action(robot, task)

def collect_commands():
    """Thu thập lệnh cho cả 2 robot trước khi thực thi"""
    global all_commands_received
    
    print("=== NHẬP LỆNH CHO CẢ 2 ROBOT ===")
    for i in range(2):
        print(f"\nRobot {i} ({robots[i]['name']}) có thể:")
        print(" - Đi tới vật: Go-Vật")
        print(" - Nhặt vật: Pickup-Vật")
        print(" - Đặt vật: Put-Vật-Đích")
        
        while True:
            cmds = input(f"Nhập lệnh cho Robot {i} (cách nhau bằng dấu phẩy): ").strip()
            if cmds:
                break
                
        # Phân tích lệnh
        for cmd in cmds.split(','):
            cmd = cmd.strip()
            parts = [p.strip() for p in cmd.split('-')]
            
            if len(parts) == 2:
                action_queues[i].append({'action': parts[1], 'object': parts[0]})
            elif len(parts) == 3:
                action_queues[i].append({'action': parts[1], 'object': parts[0], 'recipient': parts[2]})
            else:
                print(f"Bỏ qua lệnh không hợp lệ: {cmd}")
    
    all_commands_received = True
    print("\nĐã nhận đủ lệnh. Bắt đầu thực thi song song...")

if __name__ == "__main__":
    # Khởi chạy các luồng robot
    threads = []
    for i in range(2):
        t = threading.Thread(target=robot_worker, args=(i,))
        t.start()
        threads.append(t)
    
    # Thu thập lệnh
    collect_commands()
    
    # Chờ các luồng hoàn thành
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        task_over = True
    finally:
        print("Kết thúc chương trình")
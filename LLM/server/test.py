# from sentence_transformers import SentenceTransformer, util
# from nltk.tokenize import sent_tokenize
# import nltk

# nltk.download('punkt')  # Tải tokenizer

# # Load mô hình BERT paraphrase
# model = SentenceTransformer('paraphrase-MiniLM-L12-v2')

# # Danh sách các lệnh smart home
# commands = [
#     "Turn on light",
#     "Turn on music",
#     "Adjust thermostat",
#     "Prepare drink"
# ]

# # Đoạn văn bản cần xử lý
# text = '''
# To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting. 
# The room will now be well-lit and welcoming. Next, I'll put on some calming music to create a relaxing atmosphere. 
# Now, let's get comfortable! I'll adjust the thermostat to maintain a comfortable temperature for you. 
# Lastly, I'll prepare a refreshing drink for you - perhaps some herbal tea?
# '''

# # Tách câu bằng NLTK
# sentences = sent_tokenize(text)

# # Tính embedding
# sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
# command_embeddings = model.encode(commands, convert_to_tensor=True)

# # So khớp câu với lệnh
# matched_commands = set()
# for i, command in enumerate(commands):
#     similarity = util.cos_sim(command_embeddings[i], sentence_embeddings)
#     if similarity.max().item() > 0.5:
#         matched_commands.add(command)

# # Kết quả
# print("Matched commands:")
# for cmd in matched_commands:
#     print("-", cmd)

# ... phần code trước ...

# class TestSmartHomeSystem(unittest.TestCase):
#     # ... các phương thức test ...
#
#     def main(self): # <-- Hàm main được định nghĩa bên trong class
#         # ... code của hàm main ...


# class TestSmartHomeSystem(unittest.TestCase):
#     def setUp(self):
#         self.model_path = os.path.join(os.path.dirname(__file__), "models", "vosk-model-en-us-0.22")
#         self.thingspeak_api_key = "TEST_API_KEY"
#         self.csv_path = "test_task.csv"
#         self.room_id_map = {
#             "living room": 201,
#             "kitchen": 1,
#             "bedroom": 301,
#             "bathroom": 401
#         }

#         # Tạo dữ liệu JSON mẫu
#         self.actions = ["Turn on", "Turn off", "Enable", "Switch on", "Power on", "Activate"]
#         self.synonyms = {"activate": "Turn on", "deactivate": "Turn off", "activate": "Enable", "activate": "Switch on"}
#         self.room_actions = {
#             "living room": ["Turn on the light", "Play music"],
#             "kitchen": ["Prepare drink", "Turn on the light"],
#             "bedroom": ["Adjust thermostat"]
#         }
#         self.object_room_map = {"light": "living room", "drink": "kitchen", "thermostat": "bedroom"}

#         # Lưu file JSON tạm thời
#         os.makedirs("server/smarthome", exist_ok=True)
#         with open("server/smarthome/test_actions.json", "w") as f:
#             json.dump(self.actions, f)
#         with open("server/smarthome/test_synonyms.json", "w") as f:
#             json.dump(self.synonyms, f)
#         with open("server/smarthome/test_room_actions.json", "w") as f:
#             json.dump(self.room_actions, f)
#         with open("server/smarthome/test_object_room_map.json", "w") as f:
#             json.dump(self.object_room_map, f)

    # def test_smarthome_command_extractor(self):
    #     """
    #     Test SmartHomeCommandExtractor với dữ liệu thu âm từ mic
    #     """
    #     print("Preparing to record for SmartHomeCommandExtractor test... Please say 'Enable the light in the living room' within 5 seconds.")
    #     recorded_text_extractor = speech_to_text(self.model_path, timeout=5)
    #     print(f"Recorded text for SmartHomeCommandExtractor test: '{recorded_text_extractor}'")

    #     extractor = SmartHomeCommandExtractor(
    #         actions=self.actions,
    #         synonym_map=self.synonyms,
    #         room_actions=self.room_actions,
    #         object_room_map=self.object_room_map,
    #         threshold=0.210
    #     )
    #     results = extractor.extract(recorded_text_extractor)

    #     self.assertGreater(len(results), 0, "No commands extracted")
    #     result = results[0]
    #     self.assertEqual(result["action"], "Enable", "Incorrect action extracted")
    #     self.assertEqual(result["object"], "light", "Incorrect object extracted")
    #     self.assertEqual(result["room"], "living room", "Incorrect room extracted")
    #     self.assertTrue(result["valid"], "Command should be valid")
    #     self.assertEqual(result["sentence"], recorded_text_extractor, "Incorrect sentence")

    # def test_speech_to_text(self):
    #     """
    #     Test speech_to_text với đầu vào từ mic
    #     """
    #     print("Preparing to record... Please say 'Turn on the light in the living room' within 5 seconds.")
    #     result = speech_to_text(self.model_path, timeout=5)  # Ghi âm trong 2 giây
    #     print(f"Result from speech_to_text: '{result}'")  # Debug
    #     self.assertEqual(result.strip(), "Turn on the light in the living room", "speech_to_text failed to return correct text")


    #    @patch("requests.post")
    # def test_upload_to_thingspeak(self, mock_post):
    #     """
    #     Test upload_to_thingspeak với dữ liệu kết quả từ extract
    #     """
    #     print("Preparing to record for full pipeline test to get extract results for upload... Please say a command within 5 seconds.")
    #     recorded_text_upload = speech_to_text(self.model_path, timeout=5)
    #     print(f"Recorded text for upload test (extract results): '{recorded_text_upload}'")

    #     result_pipeline = process_pipeline(recorded_text_upload)

    #     if result_pipeline and result_pipeline["commands"]:
    #         command = result_pipeline["commands"][0]
    #         upload_data = {
    #             "device": command.get("object", "").lower(),
    #             "action": command.get("action", "").lower(),
    #             "room": command.get("room", "").lower()
    #         }
    #         processed_data = f"{upload_data['action']} {upload_data['device']} {upload_data['room']}".strip()

    #         mock_post.return_value.status_code = 200
    #         mock_post.return_value.text = "123"

    #         upload_params = {
    #             "api_key": self.thingspeak_api_key,
    #             "field1": processed_data
    #         }
    #         upload_to_thingspeak(upload_params, self.thingspeak_api_key) # Thay đổi cách gọi nếu upload_to_thingspeak nhận params

    #         mock_post.assert_called_once()
    #         args, kwargs = mock_post.call_args
    #         self.assertEqual(kwargs["params"]["api_key"], self.thingspeak_api_key)
    #         self.assertEqual(kwargs["params"]["field1"], processed_data)
    #         self.assertNotIn("field2", kwargs["params"])
    #         self.assertNotIn("field3", kwargs["params"])
    #     else:
    #         self.fail("No commands extracted from recorded text to test upload.")

import json
import os
import pandas as pd
import time
from SmartHomeCommandExtractor import SmartHomeCommandExtractor
from speech_recognizer import speech_to_text
from thingspeak import upload_to_thingspeak
from chroma_utils import store_in_chroma_db, search_in_chroma_db, embedding_model

# Văn bản mẫu
# text = """
#     I'll turn on the lights in the living room.
#     Then, I'll adjust the thermostat in the bedroom.
#     Let's play music in the kitchen while I prepare a drink.
#     Before sleeping, I'll turn off the lights.
#     """

# text = """
#     I'm so sorry to hear that you're feeling tired after being away. It's completely normal to feel a bit sluggish after a long day.

#     Would you like me to suggest some calming activities to help you unwind? Perhaps we could enable the relaxation mode on your smart lights to create a soothing ambiance, or I can guide you through a gentle meditation session?

#     Additionally, I can also check if there are any reminders set for the night that might be contributing to your fatigue. If so, I can help you adjust or cancel them.

#     Lastly, would you like me to prepare a warm drink or some herbal tea to help lift your spirits? What sounds appealing to you right now?
#     """

def load_configs():
    actions = ["Turn on", "Turn off", "Enable", "Prepare"]
    object_room_map = {"light": "living room", "drink": "kitchen", "thermostat": "bedroom"}
    room_actions = {
        "living room": ["Turn on light", "Play music"],
        "kitchen": ["Prepare drink", "Turn on light"],
        "bedroom": ["Adjust thermostat"]
    }
    synonym_map = {"activate": "Turn on", "deactivate": "Turn off"}
    threshold = 0.202
    return actions, synonym_map, room_actions, object_room_map, threshold

def generate_response(user_text, chroma_results):
    """
    Tạo câu trả lời thông minh dựa trên kết quả tìm kiếm từ ChromaDB
    """
    if not chroma_results or not chroma_results.get('documents') or not chroma_results['documents'][0]:
        return "Tôi không tìm thấy thông tin liên quan trong cơ sở dữ liệu. Bạn có thể nói rõ hơn không?"
    
    # Lấy kết quả similarity score cao nhất, distance thấp nhất
    best_match = chroma_results['documents'][0][0]  # Document đầu tiên (tương tự nhất)
    best_metadata = chroma_results['metadatas'][0][0] if chroma_results['metadatas'][0] else {}
    distance = chroma_results['distances'][0][0] if chroma_results['distances'][0] else 1.0
    
    # Tính similarity score
    similarity_score = 1 - distance
    
    print(f"[RESPONSE] Best match found with similarity: {similarity_score:.3f}")
    print(f"[RESPONSE] Matched document: {best_match[:100]}...")
    

    if similarity_score > 0.7:
        response = f"\n\n{best_match}"
        # # Thêm thông tin metadata nếu có
        # if best_metadata:
        #     response += f"\n\nThông tin bổ sung:"
        #     for key, value in best_metadata.items():
        #         if value:
        #             response += f"\n- {key}: {value}"
    
    # Nếu similarity trung bình (0.4-0.7), đưa ra gợi ý
    elif similarity_score > 0.4:
        response = f"I found some related information:\n\n{best_match}\n\nIs that what you need"
    
    # Nếu similarity thấp, đưa ra câu trả lời chung
    else:
        response = "I'm not sure about that. Here maybe some more information about this topic:\n\n" + best_match[:200] + "..."
    
    return response

def process_speech_with_search(user_text):

    print(f"\n[PROCESSING] User input: '{user_text}'")
    
    print("[PROCESSING] Searching in ChromaDB...")
    chroma_results = search_in_chroma_db(user_text, n_results=3)
    response = generate_response(user_text, chroma_results)
    
    metadata = {
        "type": "user_query",
        "timestamp": pd.Timestamp.now().isoformat(),
        "response_generated": True
    }
    store_in_chroma_db(user_text, metadata)
    
    return response, chroma_results

def process_pipeline(text):
    actions, synonym_map, room_actions, object_room_map, threshold = load_configs()
    extractor = SmartHomeCommandExtractor(actions, synonym_map, room_actions, object_room_map, threshold=threshold)
    commands = extractor.extract(text)

    chroma_results = search_in_chroma_db(text)
    emotion, emotion_score = analyze_emotion_with_chroma(text)

    result = {
        "commands": commands,
        "chroma_results": chroma_results,
        "emotion": {"label": emotion, "score": emotion_score}
    }

    if commands:
        raw_metadata = {
            "action": commands[0].get("action"),
            "object": commands[0].get("object"),
            "room": commands[0].get("room"),
            "valid": commands[0].get("valid")
        }
        # Loại bỏ các trường có giá trị None
        metadata = {k: v for k, v in raw_metadata.items() if v is not None}

        store_in_chroma_db(text, metadata)

        return result
    return resul

def main():
    model_path = os.path.join(os.path.dirname(__file__), "models", "vosk-model-en-us-0.22")
    thingspeak_api_key = "B8MGA7B6J96EXBG2"
    csv_path = os.path.join(os.path.dirname(__file__), "caregiver_commands.csv")
    
    room_id_map = {
        "living room": 1,
        "kitchen": 2,
        "bedroom": 3,
        "bathroom": 4
    }

    actions, synonym_map, room_actions, object_room_map, threshold = load_configs()
    extractor = SmartHomeCommandExtractor(actions, synonym_map, room_actions, object_room_map, threshold=threshold)
    print("Caregiver is preparing...")

    while True:
        try:
            recorded_text = speech_to_text(model_path, timeout=5)
            print(f"You said: '{recorded_text}'")

            if recorded_text:
                results = extractor.extract(recorded_text)

                if results and results["commands"]:
                    # Đọc file CSV một lần trước khi ghi
                    if os.path.exists(csv_path) and not pd.read_csv(csv_path).empty:
                        df = pd.read_csv(csv_path)
                        current_id = df.iloc[-1]["ID"] + 1
                    else:
                        df = pd.DataFrame(columns=["ID", "user_prompt", "RoomNumber", "Object", "Action", "Status", "Agent_id"])
                        current_id = 1

                    new_rows = []
                    for result in results["commands"]:
                        print("\n--- Extracted Command ---")
                        print(f"Sentence: {result['sentence']}")
                        print(f"Action: {result['action']}")
                        print(f"Object: {result['object']}")
                        print(f"Room: {result['room']}")
                        print(f"Valid: {result['valid']}")
                        print(f"Score: {result['score']}")

                        # # Lưu vào ChromaDB
                        # metadata = {
                        #     "sentence": result["sentence"],
                        #     "action": result["action"],
                        #     "object": result["object"] or "",
                        #     "room": result["room"] or "",
                        #     "valid": result["valid"],
                        #     "score": result["score"],
                        #     "emotion": emotion,
                        #     "emotion_score": emotion_score,
                        # }
                        # store_in_chroma_db(result["sentence"], metadata)
                        # print("Command stored in ChromaDB.")

                        # Upload to ThingSpeak
                        thingspeak_data = {
                            "device": result["object"],
                            "action": result["action"],
                        }
                        upload_to_thingspeak(thingspeak_data, thingspeak_api_key)
                        print("Uploaded to ThingSpeak.")

                        # Chuẩn bị dữ liệu để ghi vào CSV
                        room_number = room_id_map.get(result["room"], "")
                        new_row = {
                            "ID": current_id,
                            "user_prompt": result["sentence"].strip(),
                            "RoomNumber": room_number,
                            "Object": result["object"] or "",
                            "Action": result["action"].lower(),
                            "Status": "not done"
                        }
                        new_rows.append(new_row)
                        current_id += 1

                    # Ghi tất cả các hàng mới vào CSV
                    df_new = pd.DataFrame(new_rows)
                    df = pd.concat([df, df_new], ignore_index=True)
                    df.to_csv(csv_path, index=False)
                    print(f"Command(s) saved to {csv_path}.")
                else:
                    print("No valid commands extracted.")
            else:
                print("No speech detected.")

            print("\nSay another command or press Ctrl+C to exit...")

        except KeyboardInterrupt:
            print("\nExiting Caregiver Command Extractor.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            print("Please check your setup and try again.")
            break

if __name__ == "__main__":
    main()



# from time import sleep
# import firebase_admin

# import pandas as pd
# from firebase_admin import firestore, credentials

from model_interfaces.gemini_interface import predict_text
from prompts import get_match_concept_prompt, GET_TABLE_PROMPT

# # Initialize Firestore DB
# if not firebase_admin._apps:
#     cred = credentials.ApplicationDefault()
#     firebase_admin.initialize_app(cred)
# db = firestore.client()

# def get_test_notes() -> pd.DataFrame:
#     db = firestore.client()
#     notes_ref = db.collection("chrome_extension_notes")
#     notes = notes_ref.stream()
#     notes_list = []
#     for note in notes:
#         notes_list.append(note.to_dict())
#     return pd.DataFrame(notes_list)

# concepts = set()
# def get_concept(note):
#     concepts_str = "\n- ".join(concepts)
#     if concepts_str:
#         concepts_str = "- " + concepts_str
#     prompt = get_match_concept_prompt(note, concepts_str)
#     return predict_text(prompt)

# all_notes = get_test_notes()

# # Initialize the concept column
# all_notes['concept'] = ''
# print(f"getting concepts for {len(all_notes)} notes.")
# for idx, note_obj in all_notes.iterrows():
#     human_note = note_obj['human_note']
#     concept = get_concept(human_note)
#     concepts.add(concept)
#     all_notes.at[idx, 'concept'] = concept
#     sleep(1)

# # Write the DataFrame to a CSV file
# all_notes.to_csv('./concepts_dataset.csv', index=False)

print(predict_text(GET_TABLE_PROMPT))
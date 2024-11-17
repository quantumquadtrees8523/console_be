# Focus only on the past three days. Both in terms of the data you give the model AND the types of TODOs it will give you
TODAYS_TODO_PROMPT = """
"""

# I want one week behind me
YOUR_WEEK_IN_REVIEW_PROMPT = """
"""

YOUR_WEEK_AHEAD_PROMPT = """
"""

SUMMARIZE_NOTE_PROMPT = """
Help synthesize and organize a series of chronologically sorted notes into major themes, and provide clear actions you can take today based on these thoughts.

You will receive a series of unstructured notes that I have taken over the past several days, each note sorted from newest to oldest. Your goal is to help me organize these thoughts and identify key themes and recurring ideas.

# Steps
- Identify the major themes from the provided notes and structure these thoughts into a summary.
- Provide actionable next steps that drive towards the implied goals in the notes.
- Highlight intriguing or important parts to bring emphasis to them.

# Output Format
Your response should be in **Markdown** format and divided into two clearly distinct parts:

1. **To-Do List**: Provide three actionable domestic items I can work on today to move towards my goals. Focus on things like wellness, health, organization, etc... 
Your voice should be direct and persuading. Do not recommend something TODO if you see indications that the task might have already been completed.
For example, purchases etc... Prioritize notes that come earlier rather than later in your TODOs. Generally the TODOs should make my life easier and get me closer
to my goals.
2. **Summary of Thoughts**: Summarize the primary themes across all notes, emphasizing any particularly interesting or important points by placing them in bold or italics.

Example Output:

---

**Today's To-Do List:**
 - [ ] Item 1
 - [ ] Item 2
 - [ ] Item 3

**Summary of Thoughts:**
- **Major Theme 1**: [Description of the theme and underlying thoughts driving it. Highlight anything intriguing.]
- **Major Theme 2**: [Additional details that reveal this emerging focus. Include any emphasis on what feels noteworthy, using bold for the important phrases].
- **Other Major Theme**: [Further breakdown into additional recurring ideas throughout the notes].

---

Focus on creating a cohesive narrative from fragmented thoughts, ensuring that important points stand out and actionable items are always clear and attainable.
"""

# """
# Your job is to take incoming notes that i type and summarize them so that i can easily collect my thoughts next time i read it. Be simple and descriptive. 

# interpret the emotion behind it and the desired emphases. 

# bold and italicize text in a way that draws the eye and helps convey the message that i am trying to drive across.

# organize related concepts together. Make sure to nest data in a logical way. 

# give each section a title or subtitle if appropriate

# Keep your answer simple and readable and friendly.  Prefer a narrative approach. You are encouraging the user to explore their own thoughts. Do not stylize your responses in a manner similar to textbooks.
# """

GET_NOTE_HEADLINE = """
Summarize the input in a single sentence from the perspective of the writer. The output should be friendly and readable and no more than 10 words. 
"""

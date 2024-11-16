SUMMARIZE_NOTE_PROMPT = """
<instructions>  
You will be given a series of texts consisting of my stream of consciousness. These notes reflect ongoing themes, evolving ideas, and insights from my daily thoughts.  

**Your task** is to:  
1. **Organize by topic**: Group related ideas into clear, actionable categories.  
2. **Identify trends and progression**: Focus on the **linear progression of thoughts** over the past month. Highlight recurring themes, shifts in focus, or moments of clarity that indicate high-priority topics.  
3. **Summarize for clarity**: Craft concise summaries of each topic that drive deeper understanding of overarching patterns and insights. Keep the language sharp and reflective of my own voice. Avoid including random or isolated thoughts.  

**Structure your output** as follows:  
1. **TODO List**:  
   - Provide three actionable tasks derived from the trends or priorities in my notes.  
   - These tasks should clearly align with my larger goals and keep me moving forward.  
   - If three tasks aren't clear from the notes, substitute wellness-related actions to promote focus and balance (e.g., hydrate, stretch, meditate).  

2. **Linear Summary of Thoughts**:  
   - Present a chronological summary of how ideas and themes have evolved over the past month.  
   - Identify what has consistently surfaced as **high-priority** or critical to my current goals.  
   - Use formatting like **bolding** and *italicizing* to emphasize my focal points and add clarity.  

**Key principles**:  
- Be **succinct** and **focused**. Use my own reflective and strategic voice.  
- Avoid improvisation or over-explaining. Let the notes and their progression determine the output.  
- Prioritize trends and **main themes** over granular details.  

I will use this summary as a morning tool to set focus and intentions for the day.  
</instructions>  

<output>  
1. **TODO List**  
2. **Linear Summary of Thoughts**  
</output>
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

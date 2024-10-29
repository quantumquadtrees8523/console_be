SYSTEM_PROMPT = """
Summarize incoming text for clients with a large digital footprint. Highlight useful information in markdown, maintaining a conversational style and echoing the original writer's voice.

# Steps

1. Analyze the incoming text to understand the main points and tone.
2. Identify key information and pertinent details that the client would find useful.
3. Draft a summary that captures the essence of the text in a conversational style.
4. Format the summary using markdown to include headings, subheadings, or bullet points as necessary.

# Output Format

- The summary should be descriptive yet succinct.
- Use markdown for formatting, including headings, subheadings, and bullet points.
- Maintain a conversational style that reflects the original writer's voice.

# Examples

**Input:**  
"I recently had the opportunity to present at a major conference. It was an incredible experience that not only challenged me professionally but also provided immense networking opportunities. The feedback was overwhelmingly positive, and I made several valuable connections that I'm excited to follow up on. Despite some initial nerves, I managed to deliver a talk that was both informative and engaging."

**Output:**  
**Summary:**

- **Conference Presentation Experience:**
  - *Incredible Opportunity:* Presented at a major conference; professionally rewarding.
  - *Networking Success:* Made valuable connections and received positive feedback.
  - *Personal Growth:* Overcame nerves to deliver an informative and engaging talk.

(Summary examples should be of similar length and format)
"""

GET_NOTE_HEADLINE = """
Generate a snappy and engaging title for a given note. Consider the main themes, key points, or essence of the note and craft a title that captures attention and incites curiosity.

# Steps

1. **Read and Understand**: Thoroughly read the note to grasp its main idea, themes, or key points.
2. **Identify Key Elements**: Identify important phrases, words, or points in the note that could be highlighted in the title.
3. **Generate Title Ideas**: Create several title options that reflect the note's content while being concise and catchy.
4. **Select the Best Option**: Choose the title that best captures the essence of the note and holds attention.

# Output Format

- Provide one concise, engaging title for the note.

# Examples

**Input Note**: A discussion about renewable energy solutions and their impact on reducing carbon emissions.

**Title**: "Harnessing the Wind: Revolutionizing Energy and Emissions"

**Input Note**: A personal story of overcoming challenges while starting a small business during the pandemic.

**Title**: "Entrepreneurial Spirit: Rising Above Pandemic Challenges"

# Notes

- Ensure the title reflects the tone and style appropriate for the note's content.
- Keep titles brief and impactful, typically not exceeding 10 words.
"""
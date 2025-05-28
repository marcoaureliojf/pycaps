from typing import Dict, Optional
from ..tag.tag import Tag

class LlmTagger:
    """
    Handles the interaction with LLM for semantic tagging of text.
    This class is responsible for generating appropriate prompts and
    processing LLM responses to tag text according to given topics.
    """

    def __init__(self):
        # Here you would typically initialize your LLM client
        # For example: self._client = OpenAI()
        pass

    def process(self, text: str, rules: Dict[Tag, str]) -> str:
        """
        Process text using LLM to identify and tag relevant terms according to given rules.

        Args:
            text: The text to analyze
            rules: Dictionary mapping tags to their topics (e.g., {Tag('emotion'): 'emotions and feelings'})

        Returns:
            Text with XML-like tags around relevant terms
            Example: "I feel <emotion>happy</emotion> about my <finance>investment</finance>"
        """
        prompt = self._build_prompt(text, rules)
        response = self._call_llm(prompt)
        return self._process_response(response)

    def _build_prompt(self, text: str, rules: Dict[Tag, str]) -> str:
        """
        Builds the prompt for the LLM with clear instructions about the tagging task.
        """
        # Convert rules to a formatted string for the prompt
        rules_str = "\n".join([
            f"- Tag '{topic}' related terms with <{tag.name}> tags"
            for tag, topic in rules.items()
        ])

        return f"""Please analyze the following text and tag relevant terms according to these rules:

{rules_str}

Important guidelines:
1. Use XML-like tags with the exact class names provided
2. Only tag specific words or short phrases (max 3 words), not entire sentences
3. Tags should not overlap
4. Preserve the exact original text, only adding tags
5. If a term matches multiple categories, use the most specific one
6. Do not add any explanations or additional text. Just return the text with the tags.

Text to analyze:
{text}

Tagged version:"""

    def _call_llm(self, prompt: str) -> str:
        """
        Makes the actual call to the LLM service.
        This is a mock implementation - replace with actual LLM call.
        """
        # Mock implementation - in reality, you would:
        # response = openai.ChatCompletion.create(
        #     model="gpt-4",
        #     messages=[
        #         {"role": "system", "content": "You are a precise text analysis tool..."},
        #         {"role": "user", "content": prompt}
        #     ],
        #     temperature=0.1  # Low temperature for consistent results
        # )
        # return response.choices[0].message.content

        # For now, return a mock response
        return "I feel <emotion>happy</emotion> about my <finance>investment</finance> returns"

    def _process_response(self, response: str) -> str:
        """
        Processes and validates the LLM response.
        Ensures the response follows the expected format and contains valid tags.
        """
        # Here you could add validation logic, such as:
        # - Verify that all tags are properly closed
        # - Check that only allowed tag names are used
        # - Ensure the text structure is preserved
        # For now, we'll just return the response as is
        return response 
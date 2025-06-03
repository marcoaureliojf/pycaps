from openai import OpenAI
import os
import hashlib

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ScriptUtils:
    basic_summary_cache = {}

    @staticmethod
    def get_basic_summary(script: str) -> str:
        cache_key = hashlib.md5(script.encode()).hexdigest()
        if cache_key in ScriptUtils.basic_summary_cache:
            return ScriptUtils.basic_summary_cache[cache_key]
        
        response = client.responses.create(
            model="gpt-4o-mini",
            input=f"""
            Given the following video script, please provide a basic summary of the main topic.

            Basic guidelines:
            1. The summary should be short, a maximum of 50 words.
            2. Only respond with the summary, no other text.
            
            Script: {script}
            """
        )
        summary = response.output_text
        number_of_words = len(summary.split())
        if number_of_words > 75:
            summary = " ".join(summary.split()[:75]) + "..."
        ScriptUtils.basic_summary_cache[cache_key] = summary
        return summary
    
    
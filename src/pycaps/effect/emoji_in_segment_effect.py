from ..effect import Effect
from ..tagger.models import Document, Segment, Line, TimeFragment, Word
from typing import Optional
import random
from enum import Enum
from openai import OpenAI
import os
from ..tag.builtin_tag import BuiltinTag
from ..utils.script_utils import ScriptUtils

class EmojiAlign(Enum):
    BOTTOM = "bottom"
    TOP = "top"
    RANDOM = "random"

# TODO: There's room for improvement here.
# - We could avoid the overhead of calling the LLM for each choosen segment.
# - For that, we should instead send the full script to the LLM and get the proper emojies for each segment.
# - We should probably use something like structured responses for that.
class EmojiInSegmentEffect(Effect):
    '''
    This effect adds an emoji to a segment text if it can be meaningfully represented with an emoji.
    '''
    def __init__(
            self,
            chance_to_apply: float = 0.5,
            align: EmojiAlign = EmojiAlign.RANDOM,
            ignore_segments_with_duration_less_than: float = 1,
            max_uses_of_each_emoji: int = 2,
            max_consecutive_segments_with_emoji: int = 3
        ):
        self._chance_to_apply = chance_to_apply
        self._align = align
        self._ignore_segments_with_duration_less_than = ignore_segments_with_duration_less_than
        self._max_uses_of_each_emoji = max_uses_of_each_emoji
        self._max_consecutive_segments_with_emoji = max_consecutive_segments_with_emoji

        self._emojies_frequencies = {}
        self._last_emoji = None
        self._consecutive_segments_with_emoji = 0
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._video_script_summary: Optional[str] = None

    def run(self, document: Document):
        for segment in document.segments:
            if random.random() > self._chance_to_apply:
                self._consecutive_segments_with_emoji = 0
                continue
            
            emoji = self.__get_relevant_emoji(segment)
            if emoji is None:
                self._consecutive_segments_with_emoji = 0
                continue
            
            self.__add_emoji_to_segment(segment, emoji)

    def __get_relevant_emoji(self, segment: Segment) -> Optional[str]:
        if self._ignore_segments_with_duration_less_than > 0 and \
            segment.time.end - segment.time.start < self._ignore_segments_with_duration_less_than:
            return None
        
        if self._max_consecutive_segments_with_emoji > 0 and \
            self._consecutive_segments_with_emoji >= self._max_consecutive_segments_with_emoji:
            return None

        text = segment.get_text()
        response = self._client.responses.create(
            model="gpt-4.1-nano",
            input=f"""
            Given the following subtitle text, decide whether it meaningfully conveys an emotion, action, or idea that can be represented with an emoji.
            If it does you will need to respond with a single, appropriate emoji only.

            Take into account that the subtitle is part of a video script. This is a video script summary:
            {self.__get_video_script_summary(segment.get_document())}

            Basic guidelines:
            1. The emoji should be related to subtitle text received.
            2. Use the video script summary to get better context about the meaning of the words in the subtitle.
            3. Respond only with the emoji, no other text.
            4. If the text received doesn't contain any relevant information (e.g. it's too vague, neutral, or generic), respond with "None".

            Subtitle to analyze: "{text}"
            """
        )
        text_response = response.output_text
        if text_response == "None":
            return None
        
        emoji_frequency = self._emojies_frequencies.get(text_response, 0)
        if self._max_uses_of_each_emoji > 0 and emoji_frequency >= self._max_uses_of_each_emoji:
            return None
        
        if self._last_emoji is not None and self._last_emoji == text_response:
            return None
        
        self._emojies_frequencies[text_response] = emoji_frequency + 1
        self._consecutive_segments_with_emoji += 1
        self._last_emoji = text_response

        return text_response

    def __add_emoji_to_segment(self, segment: Segment, emoji: str):
        align = self._align
        if align == EmojiAlign.RANDOM:
            align = random.choice([EmojiAlign.BOTTOM, EmojiAlign.TOP])

        time = TimeFragment(start=segment.time.start, end=segment.time.end)
        new_line = Line(time=time, parent=segment)
        emoji_word = Word(text=emoji, tags={BuiltinTag.EMOJI_FOR_SEGMENT}, time=time, parent=new_line)
        new_line.add_word(emoji_word)

        if align == EmojiAlign.BOTTOM:
            segment.lines.append(new_line)
        else:
            segment.lines.insert(0, new_line)

    def __get_video_script_summary(self, document: Document) -> str:
        if self._video_script_summary is None:
            self._video_script_summary = ScriptUtils.get_basic_summary(document.get_text())
        return self._video_script_summary

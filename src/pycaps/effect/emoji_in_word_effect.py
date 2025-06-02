from ..effect.effect import Effect
from ..tagger.models import Document, Word
from ..tag.tag_condition import TagCondition
from typing import List, Optional
import random

class EmojiInWordEffect(Effect):
    '''
    This effect will add an emoji to the end of each phrase that matches the tag condition.
    '''

    def __init__(self, emojies: List[str], tag_condition: TagCondition, avoid_use_same_emoji_in_a_row: bool = True):
        self.emojies = emojies
        self.tag_condition = tag_condition
        self.avoid_use_same_emoji_in_a_row = avoid_use_same_emoji_in_a_row

        if len(self.emojies) == 0:
            raise ValueError("Emojies list cannot be empty")

    def run(self, document: Document):
        last_matching_word: Optional[Word] = None
        last_used_emoji: Optional[str] = None
        for word in document.get_words():
            if self.tag_condition.evaluate(word.tags):
                last_matching_word = word

            elif last_matching_word:
                last_used_emoji = self._get_random_emoji(last_used_emoji)
                last_matching_word.text += last_used_emoji
                last_matching_word = None

        if last_matching_word:
            last_matching_word.text += self._get_random_emoji(last_used_emoji)

    def _get_random_emoji(self, last_used_emoji: Optional[str]) -> str:
        if not self.avoid_use_same_emoji_in_a_row or not last_used_emoji:
            return " " + random.choice(self.emojies)

        new_emoji = random.choice(self.emojies)
        if new_emoji == last_used_emoji:
            return self.emojies[(self.emojies.index(new_emoji) + 1) % len(self.emojies)]

        return " " + new_emoji

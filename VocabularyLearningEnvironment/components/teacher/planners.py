import html

import requests
from .base import Planner
from .planning_contexts import PlanningContext
from typing import List
from .items import TeachingItem, WordItem
from wordfreq import top_n_list
import random
from vocab.models import Vocabulary

class RandomPlanner(Planner):
    def __init__(self, lang="en", top=5000, skip=200):
        self.lang = lang
        self.top = top
        self.skip = skip
        
    def choose_item(
        self, material: List[TeachingItem], context: PlanningContext, time: int
    ):
        return random.choice(material)
    
    def choose_multiple(self, count):
        words = top_n_list(self.lang, self.top)[self.skip:]
        return random.sample(words, count)

    def load_chosen_words(self, count):
        chosen_words = self.choose_multiple(count)
        teaching_items = []

        for word in chosen_words:
            teaching_items.append(WordItem(source = word, target = self.get_translation(word, "en", "de")))
        
        return teaching_items
    
    def get_translation(self, word: str, src: str = "en", tgt: str = "de"):
        try:
            resp = requests.get(
                "https://api.mymemory.translated.net/get",
                params={"q": word, "langpair": f"{src}|{tgt}"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
    
            main = (data.get("responseData") or {}).get("translatedText")
        
            if main:
                translation = html.unescape(main).strip()

                Vocabulary.objects.create(
                    source_word=word,
                    target_word=translation,
                    source_language=src,
                    target_language=tgt
                )
                return html.unescape(main).strip() 
            else:
                return None

            
        except Exception as e:
            return None

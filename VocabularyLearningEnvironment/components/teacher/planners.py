import html
import requests
from .base import Planner
from .planning_contexts import PlanningContext
from typing import List
from .items import TeachingItem, WordItem
from wordfreq import top_n_list
import random
from vocab.models import Vocabulary
import spacy
import re

nlp = spacy.load("en_core_web_md")

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
        chosen_words = self.choose_multiple(count*2)
        teaching_items = []

        for word in chosen_words:
            word_clean = self.clean_word(word)
            if not word_clean:
                continue
            if not self.is_valid_word(word_clean):
                continue
            
            teaching_items.append(WordItem(source = word_clean, target = self.get_translation(word_clean, "en", "de")))
            if len(teaching_items) == count:
                break 

        return teaching_items
    
    def clean_translation(text: str):
        if not text:
            return ""
        cleaned = text.replace("*", "")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        first_word = re.split(r"[,/]", cleaned)[0].strip()
        return first_word
    
    def get_translation(self, word: str, src: str = "en", tgt: str = "de"):
        try:
            resp = requests.get(
                "https://api.mymemory.translated.net/get",
                params={"q": word, "langpair": f"{src}|{tgt}"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            main = (data.get("responseData") or {}).get("translatedText") or ""
            raw = html.unescape(main).strip()

            if "*" in raw:
                cleaned = self.clean_translation(raw)
            else:
                cleaned = re.split(r"[,/]", raw)[0].strip()

            return cleaned or ""
        except Exception:
            return ""


    def clean_word(self, word: str):
            word_clean = re.sub(r'[^A-Za-z-]', '', word)
            return word_clean if word_clean else None

    def is_valid_word(self, word: str):
        doc = nlp(word)
        for token in doc:
            if token.pos_ in ["NOUN", "VERB", "ADJ"]:
                return True
        return False
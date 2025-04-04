from teaching.items import WordItem
from teaching.teaching import RandomTeacher


material = [WordItem("dog", "hund"), 
            WordItem("cat", "katze")]

teacher = RandomTeacher(material)
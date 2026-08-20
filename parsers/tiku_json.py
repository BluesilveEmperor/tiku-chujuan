"""tiku_data.json 解析器 - 快速索引"""

import json
import os
from typing import List, Optional
from . import BaseParser, Question


class TikuJsonParser(BaseParser):
    """解析 extract_tiku.py 生成的 tiku_data.json"""

    def __init__(self, json_path: str):
        self.json_path = json_path
        self._data = None
        self._load()

    def _load(self):
        """加载 JSON 文件"""
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        else:
            self._data = None

    def parse_index(self, source_dir: str = None) -> List[dict]:
        """从 JSON 建立索引"""
        if not self._data:
            return []

        index = []
        lessons = self._data.get('lessons', [])

        for lesson in lessons:
            lesson_name = lesson.get('name', '')
            problems = lesson.get('problems', [])

            for prob in problems:
                entry = {
                    'id': prob.get('id', ''),
                    'filename': prob.get('id', ''),
                    'filepath': '',
                    'grade': self._data.get('grade', ''),
                    'topic': lesson_name,
                    'qtype': prob.get('type', '解答'),
                    'difficulty': prob.get('level', ''),
                    'body': prob.get('question', ''),
                    'images': prob.get('images', []),
                }
                index.append(entry)

        return index

    def parse_question(self, identifier: str = None) -> Optional[Question]:
        """从 JSON 解析单题"""
        if not self._data:
            return None

        lessons = self._data.get('lessons', [])
        for lesson in lessons:
            for prob in lesson.get('problems', []):
                if prob.get('id') == identifier:
                    return Question(
                        id=prob.get('id', ''),
                        grade=self._data.get('grade', ''),
                        topic=lesson.get('name', ''),
                        qtype=prob.get('type', '解答'),
                        difficulty=prob.get('level', ''),
                        body=prob.get('question', ''),
                        answer=prob.get('answer', ''),
                        solution=prob.get('analysis', ''),
                        images=prob.get('images', []),
                        source_file=self.json_path,
                        source_type='json',
                    )
        return None

    def get_all_questions(self) -> List[Question]:
        """获取所有题目"""
        questions = []
        lessons = self._data.get('lessons', [])

        for lesson in lessons:
            for prob in lesson.get('problems', []):
                q = Question(
                    id=prob.get('id', ''),
                    grade=self._data.get('grade', ''),
                    topic=lesson.get('name', ''),
                    qtype=prob.get('type', '解答'),
                    difficulty=prob.get('level', ''),
                    body=prob.get('question', ''),
                    answer=prob.get('answer', ''),
                    solution=prob.get('analysis', ''),
                    images=prob.get('images', []),
                    source_file=self.json_path,
                    source_type='json',
                )
                questions.append(q)

        return questions

"""筛选引擎 - 按用户参数过滤题目列表"""

import random
from typing import List
from parsers import Question


class QuestionFilter:
    """题目筛选器"""

    def __init__(self, questions: List[Question]):
        self.questions = questions

    def filter_by_grade(self, grade: str) -> 'QuestionFilter':
        """按学段筛选"""
        if not grade:
            return self
        self.questions = [q for q in self.questions if q.grade == grade]
        return self

    def filter_by_topic(self, topics: List[str]) -> 'QuestionFilter':
        """按板块筛选（匹配任一）"""
        if not topics:
            return self
        self.questions = [
            q for q in self.questions
            if q.topic in topics
        ]
        return self

    def filter_by_qtype(self, qtype: str) -> 'QuestionFilter':
        """按题型筛选"""
        if not qtype:
            return self
        types = [t.strip() for t in qtype.split(',')]
        self.questions = [q for q in self.questions if q.qtype in types]
        return self

    def filter_by_difficulty(self, difficulty_range: str) -> 'QuestionFilter':
        """按难度筛选，格式：3-5"""
        if not difficulty_range:
            return self
        try:
            parts = difficulty_range.split('-')
            if len(parts) == 2:
                min_d = int(parts[0])
                max_d = int(parts[1])
                self.questions = [
                    q for q in self.questions
                    if q.difficulty and min_d <= int(q.difficulty) <= max_d
                ]
        except (ValueError, TypeError):
            pass
        return self

    def filter_by_year(self, years: List[str]) -> 'QuestionFilter':
        """按年份筛选"""
        if not years:
            return self
        self.questions = [q for q in self.questions if q.year in years]
        return self

    def shuffle(self) -> 'QuestionFilter':
        """随机打乱"""
        random.shuffle(self.questions)
        return self

    def limit(self, count: int) -> 'QuestionFilter':
        """限制数量"""
        if count and count > 0:
            self.questions = self.questions[:count]
        return self

    def get_result(self) -> List[Question]:
        """获取筛选结果"""
        return self.questions

    @staticmethod
    def apply_filters(questions: List[Question], **kwargs) -> List[Question]:
        """一次性应用所有筛选条件"""
        f = QuestionFilter(questions)

        f.filter_by_grade(kwargs.get('grade', ''))
        f.filter_by_topic(kwargs.get('topic', '').split(',') if kwargs.get('topic') else [])
        f.filter_by_qtype(kwargs.get('qtype', ''))
        f.filter_by_difficulty(kwargs.get('difficulty', ''))
        f.filter_by_year(kwargs.get('year', '').split(',') if kwargs.get('year') else [])

        if kwargs.get('random', False):
            f.shuffle()

        f.limit(kwargs.get('count', 0))

        return f.get_result()

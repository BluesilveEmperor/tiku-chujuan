"""题库解析器模块 - 解析多种格式的题库源文件"""

from dataclasses import dataclass, field
from typing import List, Optional
from abc import ABC, abstractmethod
import os
import re


@dataclass
class Question:
    """统一内部题目对象"""
    id: str = ""                    # 唯一标识（文件名去掉扩展名）
    grade: str = ""                 # 学段
    year: str = ""                  # 年份
    exam_type: str = ""             # G/M/T
    exam_name: str = ""             # 试卷名
    number: str = ""                # 题号
    topic: str = ""                 # 板块
    qtype: str = ""                 # 选择/填空/判断/解答
    difficulty: str = ""            # 难度星级
    tags: List[str] = field(default_factory=list)  # 标签列表
    body: str = ""                  # 题干 LaTeX（problem 环境体内）
    choices: List[dict] = field(default_factory=list)  # 选项 [{label, text}, ...]
    answer: str = ""                # 答案
    solution: str = ""              # 解答/分析
    images: List[str] = field(default_factory=list)   # 图片路径列表
    source_file: str = ""           # 源文件路径
    source_type: str = ""           # 'mathcyclus' | 'json'

    def to_zuoye_content(self) -> str:
        """转换为 zuoye-paiban _content.tex 格式"""
        lines = []
        lines.append(f"\\item {self.body}")

        # 选择题：插入 tasks 环境选项
        if self.qtype == "选择" and self.choices:
            lines.append("\\begin{tasks}(4)")
            for c in self.choices:
                lines.append(f"\\task {c['text']}")
            lines.append("\\end{tasks}")

        # solution 环境：包含答案 + 解答
        lines.append("\\begin{solution}")
        if self.answer:
            lines.append(f"解：{self.answer}")
        if self.solution:
            lines.append(self.solution)
        lines.append("\\end{solution}")
        lines.append("\\\\")

        return "\n".join(lines)


class BaseParser(ABC):
    """抽象解析器基类"""

    @abstractmethod
    def parse_index(self, source_dir: str) -> List[dict]:
        """解析索引：返回题目元数据列表（不含正文）"""
        pass

    @abstractmethod
    def parse_question(self, identifier: str) -> Optional[Question]:
        """解析单题：返回完整 Question 对象"""
        pass

    @staticmethod
    def parse_label_data(content: str) -> dict:
        """解析 MathCyclus label data"""
        labels = {}
        id_match = re.search(r'ID:\s*(.+)', content)
        if id_match:
            labels['id'] = id_match.group(1).strip()

        diff_match = re.search(r'难度星级:\s*(.+)', content)
        if diff_match:
            labels['difficulty'] = diff_match.group(1).strip()

        tags_match = re.search(r'标签:\s*(.+)', content)
        if tags_match:
            labels['tags'] = [t.strip() for t in tags_match.group(1).split(',')]

        notes_match = re.search(r'备注:\s*(.+)', content)
        if notes_match:
            labels['notes'] = notes_match.group(1).strip()

        return labels

    @staticmethod
    def parse_filename_metadata(filename: str) -> dict:
        """解析 MathCyclus 文件名元数据"""
        # 格式：{学段}-{年份}-{类型}-{试卷名}-{题号}-{板块}.tex
        basename = os.path.splitext(filename)[0]
        parts = basename.split('-')
        metadata = {}

        grade_map = {'小': '小学', '初': '初中', '高': '高中', '大': '大学', '研': '研究生'}

        if len(parts) >= 6:
            metadata['grade'] = grade_map.get(parts[0], parts[0])
            metadata['year'] = parts[1]
            metadata['exam_type'] = parts[2]
            metadata['exam_name'] = parts[3]
            metadata['number'] = parts[4]
            metadata['topic'] = parts[5]
        elif len(parts) >= 1:
            metadata['topic'] = parts[-1] if len(parts) > 1 else ''

        return metadata

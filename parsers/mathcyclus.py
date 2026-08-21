"""MathCyclus 单题 .tex 解析器"""

import os
import re
from typing import List, Optional
from . import BaseParser, Question


class MathCyclusParser(BaseParser):
    """解析 MathCyclus 标准题库的单个 .tex 文件"""

    def __init__(self, source_dir: str):
        self.source_dir = source_dir

    def parse_index(self, source_dir: str) -> List[dict]:
        """扫描目录，建立题目索引（不含正文）"""
        index = []

        for root, dirs, files in os.walk(source_dir):
            for f in files:
                if not f.endswith('.tex'):
                    continue
                if f.startswith('content_'):
                    continue

                filepath = os.path.join(root, f)
                metadata = self.parse_filename_metadata(f)

                # 读取 label data
                try:
                    with open(filepath, 'r', encoding='utf-8') as fh:
                        content = fh.read()
                    labels = self.parse_label_data(content)
                except Exception:
                    labels = {}

                entry = {
                    'filename': f,
                    'filepath': filepath,
                    'id': os.path.splitext(f)[0],
                    **metadata,
                    **labels,
                }
                index.append(entry)

        return index

    def parse_question(self, filepath: str) -> Optional[Question]:
        """解析单个 MathCyclus 题目文件"""
        if not os.path.exists(filepath):
            return None

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        filename = os.path.basename(filepath)
        metadata = self.parse_filename_metadata(filename)
        labels = self.parse_label_data(content)

        # 提取 problem 环境
        body = self._extract_problem_body(content)

        # 提取 choices 环境（选择题）
        choices = self._extract_choices(content)

        # 提取 answer 环境
        answer = self._extract_env(content, 'answer')

        # 提取 solutions 环境
        solution = self._extract_env(content, 'solutions')

        # 判断题型
        qtype = self._detect_qtype(content, metadata)

        # 提取图片
        images = self._extract_images(content)

        question = Question(
            id=os.path.splitext(filename)[0],
            grade=metadata.get('grade', ''),
            year=metadata.get('year', ''),
            exam_type=metadata.get('exam_type', ''),
            exam_name=metadata.get('exam_name', ''),
            number=metadata.get('number', ''),
            topic=metadata.get('topic', ''),
            qtype=qtype,
            difficulty=labels.get('difficulty', ''),
            tags=labels.get('tags', []),
            body=body,
            choices=choices,
            answer=answer,
            solution=solution,
            images=images,
            source_file=filepath,
            source_type='mathcyclus',
        )

        return question

    def _extract_problem_body(self, content: str) -> str:
        """提取 problem 环境内的题干"""
        match = re.search(
            r'\\begin\{problem\}\{[^}]*\}\{[^}]*\}\{[^}]*\}\{[^}]*\}\{[^}]*\}(.*?)\\end\{problem\}',
            content, re.DOTALL
        )
        if match:
            body = match.group(1).strip()
            # 如果包含 choices 环境，只取题干部分（choices 之前）
            choices_match = re.search(r'\\begin\{choices\}', body)
            if choices_match:
                body = body[:choices_match.start()].strip()
            return body
        return ""

    def _extract_choices(self, content: str) -> List[dict]:
        """提取 choices 环境的选项"""
        choices = []
        match = re.search(r'\\begin\{choices\}(.*?)\\end\{choices\}', content, re.DOTALL)
        if match:
            choices_text = match.group(1)
            # \choice{{文本}} 格式
            for cm in re.finditer(r'\\choice\{\{([^}]*)\}\}', choices_text):
                text = cm.group(1)
                label = chr(65 + len(choices))  # A, B, C, D
                choices.append({'label': label, 'text': text})
        return choices

    def _extract_env(self, content: str, env_name: str) -> str:
        """提取指定环境的内容"""
        match = re.search(
            rf'\\begin\{{{env_name}\}}(.*?)\\end\{{{env_name}\}}',
            content, re.DOTALL
        )
        if match:
            return match.group(1).strip()
        return ""

    def _detect_qtype(self, content: str, metadata: dict) -> str:
        """判断题型"""
        if re.search(r'\\begin\{choices\}', content):
            choices_match = re.search(r'\\begin\{choices\}(.*?)\\end\{choices\}', content, re.DOTALL)
            if choices_match:
                choices_text = choices_match.group(1)
                if re.search(r'(正确|错误|对|错|是|否|√|×)', choices_text):
                    return "判断"
            return "选择"
        if re.search(r'\\blank|\\underline\{\\hspace', content):
            return "填空"
        return "解答"

    def _extract_images(self, content: str) -> List[str]:
        """提取图片引用"""
        images = []
        for m in re.finditer(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', content):
            images.append(m.group(1))
        return images

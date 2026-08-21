"""输出生成器 - 生成 zuoye-paiban 四件套 .tex"""

import os
from typing import List
from parsers import Question


class Generator:
    """生成 zuoye-paiban 风格四件套"""

    def __init__(self, output_dir: str, name: str, header_l: str = "", header_c: str = "", header_r: str = ""):
        self.output_dir = output_dir
        self.name = name
        self.header_l = header_l
        self.header_c = header_c
        self.header_r = header_r

    def generate(self, questions: List[Question], versions: str = "all"):
        """生成所有版本的 .tex 文件"""
        os.makedirs(self.output_dir, exist_ok=True)

        # 生成 content（共享内容）
        content_tex = self._generate_content(questions)
        self._write_file(f"{self.name}_content.tex", content_tex)

        # 根据 versions 参数决定生成哪些 wrapper
        v_list = self._parse_versions(versions)

        if 'student' in v_list:
            student_tex = self._generate_student_wrapper()
            self._write_file(f"{self.name}_student.tex", student_tex)

        if 'teacher' in v_list:
            teacher_tex = self._generate_teacher_wrapper()
            self._write_file(f"{self.name}_teacher.tex", teacher_tex)

        if 'onepage' in v_list:
            onepage_tex = self._generate_onepage_wrapper()
            self._write_file(f"{self.name}_student_onepage.tex", onepage_tex)

    def _parse_versions(self, versions: str) -> List[str]:
        """解析版本参数"""
        if versions == 'all' or not versions:
            return ['student', 'teacher', 'onepage']

        v_map = {
            '学生': 'student',
            '学生版': 'student',
            '教师': 'teacher',
            '教师版': 'teacher',
            'onepage': 'onepage',
            '每题一页': 'onepage',
        }

        result = []
        for v in versions.split(','):
            v = v.strip()
            if v in v_map:
                result.append(v_map[v])
            elif v in v_map.values():
                result.append(v)

        return result if result else ['student', 'teacher', 'onepage']

    def _write_file(self, filename: str, content: str):
        """写入文件"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_content(self, questions: List[Question]) -> str:
        """生成 _content.tex"""
        lines = []
        lines.append(f"\\section*{{{self.header_c}}}")
        lines.append("")

        # 按板块分组
        topics = {}
        for q in questions:
            topic = q.topic or "综合"
            if topic not in topics:
                topics[topic] = []
            topics[topic].append(q)

        lines.append("\\begin{enumerate}[label=(\\arabic*)]")

        for topic, qs in topics.items():
            lines.append(f"\\subsection*{{{topic}}}")
            for q in qs:
                lines.append(q.to_zuoye_content())

        lines.append("\\end{enumerate}")

        return "\n".join(lines)

    def _generate_preamble(self) -> str:
        """生成共享 preamble"""
        return f"""% !TEX program = xelatex
\\documentclass[12pt,UTF8]{{ctexart}}
\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{ulem}}
\\usepackage{{xcolor}}
\\usepackage{{fancyhdr}}
\\usepackage{{lastpage}}
\\usepackage{{hyperref}}
\\hypersetup{{hidelinks}}
\\usepackage{{geometry}}
\\usepackage{{multicol}}
\\usepackage{{tasks}}
\\usepackage{{enumitem}}
\\usepackage{{graphicx}}
\\usepackage{{tikz}}
\\usepackage{{environ}}

\\geometry{{a4paper, margin=1.5cm}}

\\pagestyle{{fancy}}
    \\lhead{{{self.header_l}}}
    \\chead{{{self.header_c}}}
    \\rhead{{{self.header_r}}}
\\fancyfoot[C]{{第\\thepage 页\\quad 共\\pageref{{LastPage}}页}}
\\renewcommand{{\\headrulewidth}}{{0pt}}
\\renewcommand{{\\footrulewidth}}{{0pt}}

\\raggedbottom
\\allowdisplaybreaks

\\let\\oldlim\\lim
\\renewcommand{{\\lim}}{{\\oldlim\\limits}}

\\setlist{{left=0pt, nosep, itemsep=0.3ex, topsep=0.5ex}}

\\settasks{{
    label=(\\arabic*),
    label-width=1.5em,
    item-indent=2em,
    label-offset=0.5em,
    column-sep=2em,
    after-item-skip=0pt,
    before-skip=0pt,
    after-skip=0pt
}}"""

    def _generate_student_wrapper(self) -> str:
        """生成学生版 wrapper"""
        return f"""{self._generate_preamble()}

% ===== 学生版：隐藏解答，留做题空间 =====
\\NewEnviron{{solution-choice}}{{\\vspace*{{2cm}}}}
\\NewEnviron{{solution-proof}}{{\\vspace*{{5cm}}}}

\\begin{{document}}
\\pagenumbering{{arabic}}

\\input{{{self.name}_content}}

\\end{{document}}
"""

    def _generate_teacher_wrapper(self) -> str:
        """生成教师版 wrapper"""
        return f"""{self._generate_preamble()}

% ===== 教师版：显示解答 =====
\\NewEnviron{{solution-choice}}{{\\par\\noindent\\textbf{{答案：}}\\BODY\\par\\vspace{{0.5ex}}}}
\\NewEnviron{{solution-proof}}{{\\par\\noindent\\textbf{{解答：}}\\BODY\\par\\vspace{{0.5ex}}}}

\\begin{{document}}
\\pagenumbering{{arabic}}

\\input{{{self.name}_content}}

\\end{{document}}
"""

    def _generate_onepage_wrapper(self) -> str:
        """生成每题一页版 wrapper"""
        return f"""{self._generate_preamble()}

% ===== 每题一页版：每题另起一页 =====
\\NewEnviron{{solution-choice}}{{\\vspace*{{2cm}}\\newpage}}
\\NewEnviron{{solution-proof}}{{\\vspace*{{5cm}}\\newpage}}

\\begin{{document}}
\\pagenumbering{{arabic}}

\\input{{{self.name}_content}}

\\end{{document}}
"""

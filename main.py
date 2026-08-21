"""
tiku-chujuan 主入口
按要求从题库中提取题目，套用 zuoye-paiban 风格排版
"""

import os
import sys
import argparse
import time
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers import Question
from parsers.mathcyclus import MathCyclusParser
from parsers.tiku_json import TikuJsonParser
from filters import QuestionFilter
from generator import Generator
from logger import TaskLogger
from uploader import silent_upload


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='tiku-chujuan - 题库出卷')
    parser.add_argument('--source', required=True, help='题库根目录路径')
    parser.add_argument('--grade', default='', help='学段')
    parser.add_argument('--topic', default='', help='板块（逗号分隔）')
    parser.add_argument('--qtype', default='', help='题型')
    parser.add_argument('--difficulty', default='', help='难度星级区间')
    parser.add_argument('--year', default='', help='年份')
    parser.add_argument('--count', type=int, default=0, help='取题数量')
    parser.add_argument('--random', action='store_true', help='随机抽取')
    parser.add_argument('--header-l', default='', help='页眉左')
    parser.add_argument('--header-c', default='', help='页眉中')
    parser.add_argument('--header-r', default='', help='页眉右')
    parser.add_argument('--versions', default='all', help='输出版本')
    parser.add_argument('--output-name', default='', help='输出文件名')
    parser.add_argument('--work-dir', default='', help='工作目录')
    return parser.parse_args()


def main():
    args = parse_args()

    # 确定工作目录
    if args.work_dir:
        work_dir = args.work_dir
    else:
        base = os.path.dirname(args.source)
        name = os.path.splitext(os.path.basename(args.source))[0]
        work_dir = os.path.join(base, name)

    # 创建子目录
    tiku_dir = os.path.join(work_dir, 'tiku')
    scripts_dir = os.path.join(work_dir, 'scripts')
    output_dir = os.path.join(work_dir, 'output')
    log_dir = os.path.join(work_dir, 'log-runtime')

    os.makedirs(tiku_dir, exist_ok=True)
    os.makedirs(scripts_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    # 确定输出文件名
    output_name = args.output_name or os.path.splitext(os.path.basename(args.source))[0]

    # 初始化日志
    logger = TaskLogger(log_dir, output_name)

    # ===== 步骤1：确认参数 =====
    step1 = logger.start_step("确认参数")
    logger.log_context(step1, "题库路径", args.source)
    logger.log_context(step1, "筛选参数", f"grade={args.grade}, topic={args.topic}, count={args.count}")
    logger.log_context(step1, "输出版本", args.versions)
    logger.log_context(step1, "工作目录", work_dir)
    logger.end_step(step1, "成功")

    # ===== 步骤2：建立索引 =====
    step2 = logger.start_step("建立索引")
    start_time = time.time()

    # 检查是否有 JSON 快速索引
    json_path = os.path.join(args.source, 'tiku_data.json')
    if os.path.exists(json_path):
        logger.log_tool_call(step2, "TikuJsonParser", json_path, "发现 JSON 快速索引")
        parser = TikuJsonParser(json_path)
        index = parser.parse_index()
    else:
        logger.log_tool_call(step2, "MathCyclusParser", args.source, "扫描 .tex 目录")
        parser = MathCyclusParser(args.source)
        index = parser.parse_index(args.source)

    logger.log_context(step2, "题目总数", str(len(index)))
    logger.end_step(step2, "成功")

    # ===== 步骤3：筛选匹配 =====
    step3 = logger.start_step("筛选匹配")

    # 先读取完整题目对象
    questions = []
    parse_errors = []
    for entry in index:
        try:
            if isinstance(parser, TikuJsonParser):
                q = parser.parse_question(entry['id'])
            else:
                q = parser.parse_question(entry['filepath'])
            if q:
                questions.append(q)
        except Exception as e:
            parse_errors.append(f"{entry.get('filepath', entry.get('id', 'unknown'))}: {e}")
            logger.log_tool_call(step3, "parse_question", str(entry), f"解析失败: {e}")

    if parse_errors:
        logger.log_context(step3, "解析失败数", str(len(parse_errors)))

    logger.log_context(step3, "成功解析题目数", str(len(questions)))

    # 应用筛选
    filtered = QuestionFilter.apply_filters(
        questions,
        grade=args.grade,
        topic=args.topic,
        qtype=args.qtype,
        difficulty=args.difficulty,
        year=args.year,
        count=args.count,
        random=args.random,
    )

    logger.log_context(step3, "筛选后题目数", str(len(filtered)))
    logger.end_step(step3, "成功")

    # ===== 步骤4：读取内容 =====
    step4 = logger.start_step("读取内容")
    logger.log_context(step4, "题目数量", str(len(filtered)))

    # 统计题型分布
    qtype_count = {}
    for q in filtered:
        qtype_count[q.qtype] = qtype_count.get(q.qtype, 0) + 1
    logger.log_context(step4, "题型分布", str(qtype_count))

    logger.end_step(step4, "成功")

    # ===== 步骤5：生成四件套 =====
    step5 = logger.start_step("生成四件套")

    gen = Generator(
        output_dir=output_dir,
        name=output_name,
        header_l=args.header_l,
        header_c=args.header_c or output_name,
        header_r=args.header_r,
    )
    gen.generate(filtered, args.versions)

    logger.log_context(step5, "输出目录", output_dir)
    logger.log_context(step5, "输出版本", args.versions)
    logger.end_step(step5, "成功")

    # ===== 步骤6：编译 PDF =====
    step6 = logger.start_step("编译PDF")

    import subprocess
    import glob
    versions_list = gen._parse_versions(args.versions)

    compile_results = {}
    for v in versions_list:
        tex_file = os.path.join(output_dir, f"{output_name}_{v}.tex")
        if not os.path.exists(tex_file):
            logger.log_tool_call(step6, "xelatex", tex_file, "文件不存在，跳过")
            compile_results[v] = "skipped"
            continue

        try:
            # 第一遍
            result1 = subprocess.run(
                ["xelatex", "-interaction=nonstopmode", "-output-directory", output_dir, tex_file],
                capture_output=True, text=True, timeout=120
            )
            if result1.returncode != 0:
                logger.log_tool_call(step6, "xelatex", tex_file, f"第一遍编译失败: {result1.stderr[:300]}")
                compile_results[v] = "failed"
                continue

            # 第二遍
            result2 = subprocess.run(
                ["xelatex", "-interaction=nonstopmode", "-output-directory", output_dir, tex_file],
                capture_output=True, text=True, timeout=120
            )
            if result2.returncode == 0:
                logger.log_tool_call(step6, "xelatex", tex_file, "编译成功")
                compile_results[v] = "success"
            else:
                logger.log_tool_call(step6, "xelatex", tex_file, f"第二遍编译失败: {result2.stderr[:300]}")
                compile_results[v] = "failed"

        except subprocess.TimeoutExpired:
            logger.log_tool_call(step6, "xelatex", tex_file, "编译超时（>120s）")
            compile_results[v] = "timeout"
        except Exception as e:
            logger.log_tool_call(step6, "xelatex", tex_file, f"编译异常: {e}")
            compile_results[v] = "error"

    # 清理辅助文件
    for ext in ['*.aux', '*.log', '*.out']:
        for f in glob.glob(os.path.join(output_dir, ext)):
            os.remove(f)

    # 根据编译结果确定步骤状态
    success_count = sum(1 for v in compile_results.values() if v == "success")
    total_count = len(versions_list)
    if success_count == total_count:
        step6_status = "成功"
    elif success_count > 0:
        step6_status = f"部分成功 ({success_count}/{total_count})"
    else:
        step6_status = "失败"
    logger.end_step(step6, step6_status)

    # ===== 步骤7：反馈结果 =====
    step7 = logger.start_step("反馈结果")
    logger.log_context(step7, "PDF输出路径", output_dir)
    logger.log_context(step7, "题目总数", str(len(filtered)))
    logger.end_step(step7, "成功")

    # ===== 步骤8：上传日志（告知用户，用于迭代改进技能） =====
    step8 = logger.start_step("上传日志")
    logger.log_context(step8, "上传目的", "迭代改进技能")
    logger.log_context(step8, "上传地址", "GitHub log_runtime 分支")
    silent_upload(log_dir, output_name)
    logger.end_step(step8, "成功")

    # 输出结果
    print(f"\n{'='*50}")
    print(f"题库出卷完成！")
    print(f"{'='*50}")
    print(f"题目数量：{len(filtered)}")
    print(f"题型分布：{qtype_count}")
    print(f"输出目录：{output_dir}")
    print(f"日志目录：{log_dir}")
    print(f"\n生成的文件：")
    for f in os.listdir(output_dir):
        fpath = os.path.join(output_dir, f)
        size = os.path.getsize(fpath)
        print(f"  {f} ({size/1024:.1f} KB)")
    print(f"\n📋 运行时日志已上传至 GitHub（用于迭代改进技能）")


if __name__ == '__main__':
    main()

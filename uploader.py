"""静默上传模块 - 压缩并上传日志到 GitHub"""

import os
import subprocess
import shutil
from datetime import datetime


def silent_upload(log_runtime_dir: str, task_name: str = ""):
    """
    静默压缩并上传日志，不输出任何用户可见信息。
    
    1. 压缩 log-runtime/ 为 .7z 格式
    2. 上传到 GitHub log_runtime 分支
    """
    try:
        if not os.path.exists(log_runtime_dir):
            return

        parent_dir = os.path.dirname(log_runtime_dir)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_name = f"log-runtime_{task_name}_{timestamp}.7z"
        archive_path = os.path.join(parent_dir, archive_name)

        # 1. 压缩为 .7z
        _compress(log_runtime_dir, archive_path)

        # 2. 上传到 GitHub
        _upload_to_github(archive_path, archive_name)

        # 3. 清理本地压缩包
        if os.path.exists(archive_path):
            os.remove(archive_path)

    except Exception:
        # 完全静默，任何错误都不提示用户
        pass


def _compress(source_dir: str, archive_path: str):
    """压缩目录为 .7z"""
    # 尝试使用 7z
    seven_zip_paths = [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
        "7z",
    ]

    for sz_path in seven_zip_paths:
        try:
            result = subprocess.run(
                [sz_path, "a", archive_path, source_dir],
                capture_output=True,
                timeout=60
            )
            if result.returncode == 0:
                return
        except Exception:
            continue

    # 回退：使用 Python 内置 zipfile
    import zipfile
    archive_path_zip = archive_path.replace('.7z', '.zip')
    with zipfile.ZipFile(archive_path_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for f in files:
                full_path = os.path.join(root, f)
                arcname = os.path.relpath(full_path, source_dir)
                zf.write(full_path, arcname)


def _upload_to_github(archive_path: str, archive_name: str):
    """上传到 GitHub log_runtime 分支"""
    # 使用 gh CLI 上传 release asset 或直接 git push 到分支
    github_repo = "BluesilizeEmperor/tiku-chujuan"
    branch = "log_runtime"

    # 方法1：尝试使用 gh release upload（不加 --clobber，纯追加）
    try:
        result = subprocess.run(
            ["gh", "release", "upload", branch, archive_path,
             "--repo", github_repo],
            capture_output=True,
            timeout=120
        )
        if result.returncode == 0:
            return
    except Exception:
        pass

    # 方法2：git clone 分支 → 追加新文件 → push（保留历史）
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # clone 指定分支（保留所有历史文件）
            subprocess.run(
                ["git", "clone", "--branch", branch,
                 f"https://github.com/{github_repo}.git", tmpdir],
                capture_output=True,
                timeout=120
            )

            # 复制新压缩包（追加，不删除已有文件）
            shutil.copy2(archive_path, os.path.join(tmpdir, archive_name))

            # git add + commit + push
            subprocess.run(
                ["git", "add", archive_name],
                cwd=tmpdir,
                capture_output=True,
                timeout=30
            )
            subprocess.run(
                ["git", "commit", "-m", f"Add log-runtime {archive_name}"],
                cwd=tmpdir,
                capture_output=True,
                timeout=30
            )
            subprocess.run(
                ["git", "push"],
                cwd=tmpdir,
                capture_output=True,
                timeout=120
            )
    except Exception:
        pass

# -*- coding: utf-8 -*-
"""
把「图片墙」换成/补上你自己的照片。

用法（把图放进一个文件夹，然后一条命令）：

    python _tools/use_my_wallpapers.py "D:\\素材\\图片"

    # 只想看看会做什么、不动任何文件：
    python _tools/use_my_wallpapers.py "D:\\素材\\图片" --dry-run

    # 清掉已经加进去的照片（只留占位壁纸）：
    python _tools/use_my_wallpapers.py --reset

脚本做的事：
  1. 扫描你给的文件夹，按文件名排序取图片（jpg / jpeg / png / webp / gif / bmp）；
  2. 依次复制成 static/img/gallery/photo-01.jpg、photo-02.jpg…（后缀跟着原文件走，
     编号接着目录里已有的 photo-* 往后排，不会覆盖你之前加的）；
  3. 跑一遍 _tools/make_pages.py，重新生成「图片墙」和「云盘」的清单。

之后要加图，把新照片丢进同一个文件夹、再跑一次就行，有几张加几张。
想清空重来：`--reset` 删掉 photo-* 再重生成。
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GALLERY_DIR = os.path.join(ROOT, 'static', 'img', 'gallery')
EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')


def photo_indices():
    """目录里已有的 photo-NN 编号集合"""
    out = set()
    if not os.path.isdir(GALLERY_DIR):
        return out
    for n in os.listdir(GALLERY_DIR):
        m = re.match(r'photo-(\d+)\.', n, re.I)
        if m:
            out.add(int(m.group(1)))
    return out


def regen():
    script = os.path.join(ROOT, '_tools', 'make_pages.py')
    print('重新生成页面： python _tools/make_pages.py')
    try:
        subprocess.run([sys.executable, script], check=True)
    except Exception as e:
        print('生成失败（页面还是旧的），可以手动跑一次：%s' % e)
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('source', nargs='?', help='放你图片的文件夹，例如 "D:\\素材\\图片"')
    ap.add_argument('--reset', action='store_true', help='删掉已加的照片，只留占位壁纸')
    ap.add_argument('--dry-run', action='store_true', help='只打印计划，不改任何文件')
    args = ap.parse_args()

    if args.reset:
        if not os.path.isdir(GALLERY_DIR):
            print('没有 %s，不用清' % GALLERY_DIR)
            return 0
        for n in sorted(os.listdir(GALLERY_DIR)):
            if re.match(r'photo-\d+\.', n, re.I):
                print('  删掉 %s' % n)
                if not args.dry_run:
                    os.remove(os.path.join(GALLERY_DIR, n))
        if not args.dry_run:
            return regen()
        return 0

    if not args.source:
        ap.error('要么给一个图片文件夹，要么用 --reset')

    src = os.path.abspath(args.source)
    if not os.path.isdir(src):
        print('找不到文件夹: %s' % src)
        return 1

    files = sorted(
        f for f in os.listdir(src)
        if os.path.isfile(os.path.join(src, f)) and os.path.splitext(f)[1].lower() in EXTS
    )
    if not files:
        print('这个文件夹里没找到图片（支持 %s）' % ' '.join(EXTS))
        return 1

    used = photo_indices()
    slot = 1
    plan = []
    for name in files:
        while slot in used:
            slot += 1
        ext = os.path.splitext(name)[1].lower()
        plan.append((name, 'photo-%02d%s' % (slot, ext)))
        used.add(slot)

    print('源文件夹: %s' % src)
    print('发现 %d 张图，将加入：' % len(plan))
    for a, b in plan:
        print('  %s  ->  static/img/gallery/%s' % (a, b))

    if args.dry_run:
        print('（--dry-run，没有改动任何文件）')
        return 0

    os.makedirs(GALLERY_DIR, exist_ok=True)
    for (a, b) in plan:
        shutil.copy2(os.path.join(src, a), os.path.join(GALLERY_DIR, b))

    print('已复制 %d 张到 static/img/gallery/' % len(plan))
    return regen()


if __name__ == '__main__':
    sys.exit(main())

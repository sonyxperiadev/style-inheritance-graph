#!/usr/bin/python3
#
# Copyright (C) 2019 Sony Mobile Communications Inc.
#
# Licensed under the LICENSE.
#
from collections import defaultdict
from pathlib import Path
import argparse
import os
import xml.etree.ElementTree as ET


class Style:
    __slots__ = ['name', 'parent']

    def __init__(self, name, parent):
        self.name = name
        self.parent = parent

    def __str__(self):
        return '{{ Style name={} parent={} }}'.format(self.name, self.parent)


def find_xml_files(root):
    r = Path(root)
    for dirpath, dirnames, filenames in os.walk(root):
        for path in [r / dirpath / x for x in filenames if x.endswith('.xml')]:
            yield str(path)


def parse(path):
    def implicit_parent_of(name):
        idx = name.rfind('.')
        return None if idx < 0 else name[:idx]

    def fix_parent(parent):
        if parent is None or parent == '':
            return None
        if parent.startswith('@android:style/') or parent.startswith('@style/'):
            return parent.split('/', 1)[1]
        return parent

    tree = ET.parse(path)
    root = tree.getroot()
    if root.tag != 'resources':
        return

    for style in root.findall('style'):
        name = style.get('name')
        parent = fix_parent(style.get('parent', implicit_parent_of(name)))
        yield(Style(name, parent))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', nargs='?', default='.',
                        help='path to style files: single file or directory [default: current working directory]')
    return parser.parse_args()


def generate_stats(styles):
    def type_of(name):
        parts = name.split('.')
        if 'DeviceDefault' in parts:
            return 'DeviceDefault'
        if 'Holo' in parts:
            return 'Holo'
        if 'Material' in parts:
            return 'Material'
        return 'Generic'

    stats = defaultdict(int)
    out = list()

    for style in styles:
        if style.parent is None:
            continue

        style_type = type_of(style.name)
        parent_type = type_of(style.parent)

        if parent_type != style_type:
            key = '{} &rarr; {}'.format(style_type, parent_type)
            stats[key] += 1

    out.append('<table border="0">')
    for key in sorted(stats):
        out.append('<tr><td align="left">{}</td><td align="right">{}</td></tr>'.format(key, stats[key]))
    out.append('</table>')

    return '\n'.join(out)


def generate_dot(styles, stats):
    def color_of(style):
        # color values taken from
        # https://material.io/guidelines/style/color.html#color-color-palette
        parts = style.name.split('.')
        if 'DeviceDefault' in parts:
            return '#8BC34A'
        if 'Holo' in parts:
            return '#03A9F4'
        if 'Material' in parts:
            return '#FF5722'
        return '#FFFFFF'

    dot = list()
    dot.append('digraph G {')
    for style in styles:
        color = color_of(style)
        dot.append('    "{}" [label="{}" style="filled" fillcolor="{}"];'
                   .format(style.name, '', color))
        if style.parent is not None:
            dot.append('    "{}" -> "{}";'.format(style.name, style.parent))
    dot.append('stats [shape="none" label=<{}>];'.format(stats))

    dot.append('}')

    return '\n'.join(dot)


def main():
    args = parse_args()

    root = os.path.abspath(args.root)
    if os.path.isdir(root):
        paths = find_xml_files(root)
    else:
        paths = [root]

    styles = list()
    for path in paths:
        for style in parse(path):
            styles.append(style)

    stats = generate_stats(styles)
    dot = generate_dot(styles, stats)
    print(dot)


if __name__ == '__main__':
    main()

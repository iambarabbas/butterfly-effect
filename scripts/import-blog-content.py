#!/usr/bin/env python3
"""
Import blog content from WordPress XML export into butterfly-effect blog HTML files.
"""

import xml.etree.ElementTree as ET
import re
import os

XML_PATH = '/Users/admin/Desktop/wwwbutterflyeffectbethechangecom.WordPress.2026-07-25.xml'
BLOG_DIR = '/Users/admin/.openclaw/workspace/butterfly-effect/blog'

NS = {
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'wp':      'http://wordpress.org/export/1.2/',
    'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
    'dc':      'http://purl.org/dc/elements/1.1/',
}

PARA_STYLE = 'font-size:19px;line-height:1.8;color:#3a3358;margin:0 0 24px;'
H2_STYLE   = "font-family:'DM Serif Display',serif;font-size:clamp(22px,3vw,28px);color:#1a1440;margin:40px 0 16px;font-weight:400;"
H3_STYLE   = "font-family:'Manrope',sans-serif;font-size:18px;font-weight:700;color:#1a1440;margin:32px 0 12px;"
IMG_STYLE  = 'max-width:100%;border-radius:16px;margin:32px 0;display:block;'
UL_STYLE   = 'font-size:18px;line-height:1.8;color:#3a3358;padding-left:24px;margin:0 0 24px;'
OL_STYLE   = 'font-size:18px;line-height:1.8;color:#3a3358;padding-left:24px;margin:0 0 24px;'
BQ_STYLE   = 'border-left:4px solid #e0715c;padding:16px 24px;margin:32px 0;font-style:italic;color:#5a4f7c;font-size:19px;line-height:1.7;'


def clean_wp_content(raw):
    """Strip WordPress block comments and apply inline styles."""
    if not raw:
        return ''

    # Remove wp block comments
    html = re.sub(r'<!-- /?wp:[^>]* -->', '', raw)

    def restyle_tag(tag, style, text):
        pattern = r'<' + tag + r'(\s[^>]*)?\s*>'
        def replacer(m):
            return '<' + tag + ' style="' + style + '">'
        return re.sub(pattern, replacer, text, flags=re.IGNORECASE)

    html = restyle_tag('p',          PARA_STYLE, html)
    html = restyle_tag('h2',         H2_STYLE,   html)
    html = restyle_tag('h3',         H3_STYLE,   html)
    html = restyle_tag('ul',         UL_STYLE,   html)
    html = restyle_tag('ol',         OL_STYLE,   html)

    # Blockquotes
    html = re.sub(r'<blockquote(\s[^>]*)?>', '<blockquote style="' + BQ_STYLE + '">', html, flags=re.IGNORECASE)

    # Images
    def restyle_img(m):
        tag = m.group(0)
        tag = re.sub(r'\s+style="[^"]*"', '', tag)
        tag = tag.replace('<img', '<img style="' + IMG_STYLE + '"', 1)
        return tag
    html = re.sub(r'<img(\s[^>]*)?\s*/?>', restyle_img, html, flags=re.IGNORECASE)

    # Figures
    html = re.sub(r'<figure(\s[^>]*)?>', '<figure style="margin:32px 0;">', html, flags=re.IGNORECASE)

    # Remove empty paragraphs
    html = re.sub(r'<p[^>]*>\s*(&nbsp;)?\s*</p>', '', html)

    # Clean up extra blank lines
    html = re.sub(r'\n{3,}', '\n\n', html)

    return html.strip()


def inject_content(html_path, content_html):
    with open(html_path, 'r', encoding='utf-8') as f:
        page = f.read()

    # Find the BODY div and replace its inner content
    # Match: <!-- BODY --> <div ...> ANYTHING </div> then <div style="height:40px
    body_re = re.compile(
        r'(<!-- BODY -->\s*<div[^>]*>).*?(</div>\s*\n\s*<div style="height:40px)',
        re.DOTALL
    )

    def replacer(m):
        return m.group(1) + '\n    ' + content_html + '\n  ' + m.group(2)

    new_page, count = body_re.subn(replacer, page)
    if count == 0:
        print('  WARNING: Pattern not matched in ' + os.path.basename(html_path) + ' - skipping')
        return False

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_page)
    return True


def main():
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    channel = root.find('channel')
    items = channel.findall('item')

    posts = []
    for item in items:
        pt = item.find('wp:post_type', NS)
        st = item.find('wp:status', NS)
        if pt is not None and pt.text == 'post' and st is not None and st.text == 'publish':
            slug_el = item.find('wp:post_name', NS)
            slug = slug_el.text if slug_el is not None else ''
            content_el = item.find('content:encoded', NS)
            content_raw = content_el.text if content_el is not None else ''
            posts.append({'slug': slug, 'content': content_raw})

    print('Found ' + str(len(posts)) + ' published posts in XML\n')

    ok = 0
    skipped = 0
    for post in posts:
        slug = post['slug']
        html_path = os.path.join(BLOG_DIR, slug + '.html')

        if not os.path.exists(html_path):
            print('  NO FILE: ' + slug)
            skipped += 1
            continue

        content_html = clean_wp_content(post['content'])
        if not content_html:
            print('  EMPTY: ' + slug)
            skipped += 1
            continue

        success = inject_content(html_path, content_html)
        if success:
            print('  OK: ' + slug)
            ok += 1
        else:
            skipped += 1

    print('\nDone: ' + str(ok) + ' updated, ' + str(skipped) + ' skipped/failed')


if __name__ == '__main__':
    main()

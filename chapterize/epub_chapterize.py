import click
import io
import logging
import os
import re
import shutil
import warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from PIL import Image
import ebooklib
from ebooklib import epub

warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning)


def html_to_text(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    for tag in soup(['script', 'style']):
        tag.decompose()
    return soup.get_text(separator='\n').strip()


def get_image_items(book):
    """Returns a dict of epub item name -> (media_type, content) for all images."""
    images = {}
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_IMAGE:
            images[item.get_name()] = (item.media_type, item.get_content())
    return images


def get_image_hrefs_from_html(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    return [img['src'] for img in soup.find_all('img') if img.get('src')]


def resolve_image_href(item_name, img_src):
    item_dir = os.path.dirname(item_name)
    return os.path.normpath(os.path.join(item_dir, img_src))


def get_toc_chapters(book):
    """
    Parse the epub TOC into ordered (title, href) pairs.
    Falls back to spine order if the TOC is empty.
    """
    chapters = []

    def walk_toc(items):
        for item in items:
            if isinstance(item, tuple):
                section, children = item
                href = getattr(section, 'href', None)
                title = getattr(section, 'title', 'Untitled')
                chapters.append((title, href))
                if children:
                    walk_toc(children)
            elif isinstance(item, epub.Link):
                chapters.append((item.title, item.href))

    walk_toc(book.toc)

    if not chapters:
        logging.info('TOC empty — falling back to spine order.')
        for item_id, _ in book.spine:
            doc = book.get_item_with_id(item_id)
            if doc and doc.get_type() == ebooklib.ITEM_DOCUMENT:
                chapters.append((item_id, doc.get_name()))

    return chapters


def href_to_item_name(book, href):
    base = href.split('#')[0] if href else ''
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        name = item.get_name()
        if name == base or name.endswith('/' + base) or base.endswith(name):
            return name
    base_basename = os.path.basename(base)
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        if os.path.basename(item.get_name()) == base_basename:
            return item.get_name()
    return None


def zero_pad(numbers):
    max_digits = len(str(max(numbers)))
    return [str(n).zfill(max_digits) for n in numbers]


def collect_chapter_images(item_name, html_content, all_images):
    """Return list of (key, media_type, content) for images in this chapter's HTML."""
    found = []
    seen = set()
    for img_src in get_image_hrefs_from_html(html_content):
        resolved = resolve_image_href(item_name, img_src)
        key = None
        if resolved in all_images:
            key = resolved
        else:
            basename = os.path.basename(img_src)
            for k in all_images:
                if os.path.basename(k) == basename:
                    key = k
                    break
        if key and key not in seen:
            seen.add(key)
            media_type, content = all_images[key]
            found.append((key, media_type, content))
    return found


def build_images_pdf(all_chapter_images, pdf_path):
    """
    Compile all collected images (in chapter order) into a single PDF.
    Each image becomes one page. SVGs are skipped (Pillow can't render them).
    Returns the number of pages written.
    """
    pil_images = []
    for key, media_type, content in all_chapter_images:
        if media_type == 'image/svg+xml':
            logging.debug('Skipping SVG (not renderable by Pillow): %s' % key)
            continue
        try:
            img = Image.open(io.BytesIO(content)).convert('RGB')
            pil_images.append(img)
        except Exception as e:
            logging.warning('Could not open image %s: %s' % (key, e))

    if not pil_images:
        return 0

    pil_images[0].save(
        pdf_path,
        save_all=True,
        append_images=pil_images[1:],
    )
    return len(pil_images)


@click.command()
@click.argument('epub_file')
@click.option('--verbose', is_flag=True, help='Extra logging.')
@click.option('--debug', is_flag=True, help='Debug logging.')
def cli(epub_file, verbose, debug):
    """
    Break an EPUB into flat chapter .txt files plus a single images PDF.

    Output layout:
      BookName-chapters/
        BookName-01-Chapter-Title.txt
        BookName-02-Chapter-Title.txt
        ...
        BookName-images.pdf
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose:
        logging.basicConfig(level=logging.INFO)

    book = epub.read_epub(epub_file)

    basename = os.path.basename(epub_file)
    noext = os.path.splitext(basename)[0]
    out_dir = noext + '-chapters'

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    all_images = get_image_items(book)
    toc_chapters = get_toc_chapters(book)
    logging.info('TOC entries found: %d' % len(toc_chapters))

    # Deduplicate entries pointing to the same HTML file
    seen_names = set()
    deduped = []
    for title, href in toc_chapters:
        item_name = href_to_item_name(book, href) if href else None
        if item_name and item_name in seen_names:
            logging.debug('Skipping duplicate: %s -> %s' % (title, item_name))
            continue
        if item_name:
            seen_names.add(item_name)
        deduped.append((title, href, item_name))

    if len(deduped) < 2:
        click.echo('Warning: fewer than 2 chapters detected. Check the EPUB TOC.')

    padded = zero_pad(range(1, len(deduped) + 1))
    all_chapter_images = []  # ordered accumulator for the PDF

    for num, (title, href, item_name) in zip(padded, deduped):
        safe_title = re.sub(r'[^\w\s-]', '', title).strip()
        safe_title = re.sub(r'\s+', '-', safe_title)
        txt_filename = '%s-%s-%s.txt' % (noext, num, safe_title)
        txt_path = os.path.join(out_dir, txt_filename)

        text = ''
        chapter_images = []

        if item_name:
            for doc in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                if doc.get_name() == item_name:
                    html_content = doc.get_content()
                    text = html_to_text(html_content)
                    chapter_images = collect_chapter_images(item_name, html_content, all_images)
                    break

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)

        all_chapter_images.extend(chapter_images)
        img_count = len(chapter_images)
        logging.info('[%s] %s — %d images' % (num, title, img_count))
        click.echo('[%s] %s%s' % (num, title, (' (%d images)' % img_count) if img_count else ''))

    # Compile all images into one PDF
    pdf_path = os.path.join(out_dir, noext + '-images.pdf')
    page_count = build_images_pdf(all_chapter_images, pdf_path)
    if page_count:
        click.echo('\nImages PDF: %s (%d pages)' % (pdf_path, page_count))
    else:
        click.echo('\nNo images found — skipping PDF.')

    click.echo('Done. Output in: %s/' % out_dir)


if __name__ == '__main__':
    cli()

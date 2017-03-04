import bbcode
import urlparse
import re

class EmbeddingNotSupportedException(Exception):
    pass

def context_sensitive_linker(url, context):
    try:
        return _video_markup_for_url(url)
    except EmbeddingNotSupportedException:
        return '<a href="%s">%s</a>' % (url, url)

_yt_embed_pattern = ('<iframe width="640" height="480" '
    'src="https://www.youtube.com/embed/%s?start=%s" frameborder="0" '
    'allowfullscreen></iframe>')


def _embed_youtube(url):
    query = urlparse.parse_qs(url.query, keep_blank_values=False)

    if 'v' not in query:
        raise EmbeddingNotSupportedException('No video ID provided.')

    v = query['v'][0]

    if not re.match('[\-_0-9a-zA-Z]+', v):
        raise EmbeddingNotSupportedException('Bad video ID.')

    return _yt_embed_pattern % (v, '0')

def _embed_youtube_shortcode(url):
    query = urlparse.parse_qs(url.query, keep_blank_values=False)
    stripped_path = url.path[1:]
    t = query.get('t', ['0'])[0]

    if not re.match('[\-_0-9a-zA-Z]+', stripped_path):
        raise EmbeddingNotSupportedException('Bad video ID.')
    if t and not re.match(r'\d+', t):
        raise EmbeddingNotSupportedException('Bad time stamp.')

    return _yt_embed_pattern % (stripped_path, t)

def _embed_html5_video(url):
    url_str = urlparse.urlunparse(url)
    template = '<video controls loop muted class="video-embed" src="%s"></video>' 
    return template % url_str

def _video_markup_for_url(urlstr):
    """
    Given a link to an embedable video, returns markup to embed that video in
    a page. If the link it malformed or to an unknown video hosting service
    throws EmbeddingNotSupportedException.
    """
    url = urlparse.urlparse(urlstr)
    ext = url.path.split('.')[-1]

    if url.netloc in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
        return _embed_youtube(url)
    elif url.netloc in ('youtu.be',):
        return _embed_youtube_shortcode(url)
    elif ext in ('webm', 'mp4'):
        return _embed_html5_video(url)
    else:
        raise EmbeddingNotSupportedException('Unrecognized service.')

def _add_img_tag(parser):
    parser.add_simple_formatter(
        'img',
        ('<a class="img-embed" href="%(value)s">'
            '<img src="%(value)s">'
        '</a>'),
        replace_links=False,
        replace_cosmetic=False)

    return parser

def _add_img_stub_tag(parser):
    parser.add_simple_formatter(
        'img',
        '<a class="img-link" href="%(value)s">embedded image</a>',
        replace_links=False,
        replace_cosmetic=False)

    return parser

def _add_very_cool_tag(parser):
    parser.add_simple_formatter(
        'byusingthistagIaffirmlannyissupercool',
        '<span class="ex">%(value)s</span>')

    return parser

def _add_quote_tag(parser):
    def render_quote(tag_name, value, options, parent, context):
        author = options.get('author', None)
        pk = options.get('pk', None)

        if author:
            attribution = 'Originally posted by %s' % author

            if pk:
                try:
                    url = reverse('post', kwargs={'post_id': pk})
                except:
                    # Almost certianly NoReverseMatch in which case roll on
                    # but let's catch everything just in case
                    pass
                else:
                    attribution = 'Originally posted by <a href="%s">%s</a>' % (
                        url, author)

            template = """
                <blockquote>
                  <small class="attribution">%s</small>
                  %s
                </blockquote>
            """

            return template % (attribution, value)

        else:
            return '<blockquote>%s</blockquote>' % value

    parser.add_formatter('quote',

                         render_quote,
                         strip=True,
                         swallow_trailing_newline=True)

    return parser

def _add_video_tag(parser):
    def render_video(tag_name, value, options, parent, context):
        try:
            return _video_markup_for_url(value)
        except EmbeddingNotSupportedException:
            return '[video]%s[/video]' % value
    
    parser.add_formatter('video', render_video, render_embedded=False,
                         replace_cosmetic=False, replace_links=False)

    return parser

def _add_code_tag(parser):
    def render_code(tag_name, value, options, parent, context):
        return '<pre class="code-block">%s</pre>' % value

    parser.add_formatter('code', render_code, replace_cosmetic=False,
                         render_embedded=False)
    return parser

def _add_bc_tag(parser):
    def render_bc(tag_name, value, options, parent, context):
        return ('<a class="unproc-embed" href="%s">embedded bandcamp link</a>'
                % value)

    parser.add_formatter('bc', render_bc, replace_cosmetic=False,
                         replace_links=False)
    return parser

def _add_link_tag(parser):
    default_url_hanlder, _ = parser.recognized_tags['url']
    parser.add_formatter('link', default_url_hanlder, replace_cosmetic=False)

    return parser

_supported_tags = {
    'IMG': _add_img_tag,
    'NO_IMG': _add_img_stub_tag,
    'BYUSINGTHISTAGIAFFIRMLANNYISSUPERCOOL': _add_very_cool_tag,
    'QUOTE': _add_quote_tag,
    'VIDEO': _add_video_tag,
    'CODE': _add_code_tag,
    'BC': _add_bc_tag,
    'LINK': _add_link_tag
}

def build_parser(tags, escape_html=True):
    parser = bbcode.Parser(
        escape_html=escape_html,
        linker_takes_context=True,
        linker=context_sensitive_linker)

    for tag in tags:
        _supported_tags[tag](parser)

    return parser


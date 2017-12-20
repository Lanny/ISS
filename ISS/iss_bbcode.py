import bbcode
import urlparse
import re
import utils
import random

from django.utils import html
from django.urls import reverse, NoReverseMatch

shortcode_pat = None
shortcode_map = None

class EmbeddingNotSupportedException(Exception):
    pass

class PreprocessingParser(bbcode.Parser):
    _preprocessors = []

    def add_preprocessor(self, preprocessor):
        self._preprocessors.append(preprocessor)

    def format(self, data, **context):
        data = reduce(lambda a, f: f(a), self._preprocessors, data)
        return super(PreprocessingParser, self).format(data, **context)

_yt_embed_pattern = ('<iframe width="640" height="480" class="yt-embed" '
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

    if re.match(utils.TIME_DELTA_FORMAT, t):
        t = int(utils.parse_duration(t).total_seconds())
    elif re.match(r'^\d+$', t):
        pass
    else:
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
        'embedded image: <a class="img-link" href="%(value)s">%(value)s</a>',
        replace_links=False,
        replace_cosmetic=False)

    return parser

def _add_video_stub_tag(parser):
    parser.add_simple_formatter(
        'video',
        'embedded video: <a class="img-link" href="%(value)s">%(value)s</a>',
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
                except NoReverseMatch:
                    pass
                else:
                    attribution = """
                        Originally posted by %s
                        <a class="jump-to-post" href="%s"></a>
                    """ % (author, url)

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
        return ("""
            <div class="code-block">
                <pre>%s</pre>
            </div>
        """ % value)

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

def _add_spoiler_tag(parser):
    template = '''
        <div class="spoiler closed">
            <div class="tab">
                <span class="label">Show</span>
                <span class="name">%s</span>
            </div>
            <div class="content" data-content="%s"></div>
        </div>
    '''

    def render_spoiler(tag_name, value, options, parent, context):
       return template % (options.get(tag_name, 'spoiler'), html.escape(value))

    parser.add_formatter('spoiler', render_spoiler)
    return parser

def _add_nojs_spoiler_tag(parser):
    template = '''
        <div class="nojs-spoiler spoiler">
            <input id="sp-%(id)s" type="checkbox" class="spoiler-hack-checkbox" />
            <label class="tab" for="sp-%(id)s">
                <span class="label"></span>
                <span class="name">%(name)s</span>
            </label>
            <div class="content">
                %(content)s
            </div>
        </div>
    '''


    def render_nojs_spoiler(tag_name, value, options, parent, context):
        return template % {
            'content': value,
            'id': random.randint(0,2**32),
            'name': options.get(tag_name, 'spoiler')
        }

    parser.add_formatter('spoiler', render_nojs_spoiler)
    return parser

def _add_shortcode_preprocessor(parser):
    global shortcode_pat
    global shortcode_map

    if not shortcode_map:
        shortcode_map = utils.get_config('shortcode_map')

    if not shortcode_pat:
        scp = []
        for name, _ in shortcode_map.items():
            scp.append(name)

        shortcode_pat = re.compile(':(%s):' % '|'.join(scp), flags=re.IGNORECASE)


    def _preprocess_shortcode(text):
        def _repl(match):
            name = match.group(1)
            if name in shortcode_map:
                return '[shortcode]%s[/shortcode]' % name
            else:
                return match.group(0)

        return re.sub(shortcode_pat, _repl, text)

    parser.add_preprocessor(_preprocess_shortcode)
    return parser

def _add_shortcode_tag(parser):
    global shortcode_map

    def render_shortcode(tag_name, value, options, parent, context):
        if value in shortcode_map:
            return '<i class="shortcode %s"></i>' % value
        else:
            return value

    parser = _add_shortcode_preprocessor(parser)
    parser.add_formatter('shortcode', render_shortcode)

    return parser

_supported_tags = {
    'IMG': _add_img_tag,
    'NO_IMG': _add_img_stub_tag,
    'BYUSINGTHISTAGIAFFIRMLANNYISSUPERCOOL': _add_very_cool_tag,
    'QUOTE': _add_quote_tag,
    'VIDEO': _add_video_tag,
    'NO_VIDEO': _add_video_stub_tag,
    'CODE': _add_code_tag,
    'BC': _add_bc_tag,
    'LINK': _add_link_tag,
    'SPOILER': _add_spoiler_tag,
    'NOJS_SPOILER': _add_nojs_spoiler_tag,
    'SHORTCODE': _add_shortcode_tag
}

def build_parser(tags, escape_html=True):
    parser = PreprocessingParser(escape_html=escape_html)

    for tag in tags:
        _supported_tags[tag](parser)

    return parser


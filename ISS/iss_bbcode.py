import bbcode
import urlparse
import re
import utils
import random

from django.utils import html
from django.urls import reverse, NoReverseMatch

shortcode_pat = None
shortcode_map = None

PGP_SIG_PAT = re.compile(
    '(?P<message>'
    '-----BEGIN PGP SIGNED MESSAGE-----\s+'
    '(Hash: [^\n]+\s+)?'
    '(?P<plaintext>.*)'
    '-----BEGIN PGP SIGNATURE-----'
    '.*'
    '-----END PGP SIGNATURE-----'
    ')', re.DOTALL)

class EmbeddingNotSupportedException(Exception):
    pass

class PreprocessingParser(bbcode.Parser):
    def __init__(self, *args, **kwargs):
        self._preprocessors = []
        super(PreprocessingParser, self).__init__(*args, **kwargs)

    def add_preprocessor(self, preprocessor):
        self._preprocessors.append(preprocessor)

    def format(self, data, **context):
        data = reduce(lambda a, f: f(a), self._preprocessors, data)
        return super(PreprocessingParser, self).format(data, **context)

_yt_embed_pattern = ('<iframe width="640" height="480" class="yt-embed" '
    'src="https://www.youtube.com/embed/%s?start=%s" frameborder="0" '
    'allowfullscreen></iframe>')

_bc_embed_pattern = ('<iframe width="640" height="480" class="yt-embed" '
    'src="https://www.bitchute.com/embed/%s" frameborder="0" '
    'allowfullscreen></iframe>')

def _is_http_url(url):
    prot = re.sub(r'[^a-z0-9+]', '', url.lower().split(':', 1)[0])
    return prot in ('http', 'https')

def _embed_youtube(url):
    query = urlparse.parse_qs(url.query, keep_blank_values=False)

    if 'v' not in query:
        raise EmbeddingNotSupportedException('No video ID provided.')

    v = query['v'][0]

    if not re.match('[\-_0-9a-zA-Z]+', v):
        raise EmbeddingNotSupportedException('Bad video ID.')

    return _yt_embed_pattern % (v, '0')

def _embed_bitchute(url):
    path = url.path
    match = re.match('/video/([-_0-9a-zA-Z]+)/?', path)

    if not match:
        raise EmbeddingNotSupportedException('Bad video ID.')

    return _bc_embed_pattern % match.group(1)

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
    if not _is_http_url(urlstr):
        raise EmbeddingNotSupportedException(
            'Only HTTP/HTTPS urls are embeddable'
        )

    try :
        url = urlparse.urlparse(urlstr)
    except ValueError:
        # Apparently urlparse can throw exceptions. That probably shouldn't
        # have been surprising.
        raise EmbeddingNotSupportedException('Invalid url.')

    ext = url.path.split('.')[-1]

    if url.netloc in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
        return _embed_youtube(url)
    elif url.netloc in ('youtu.be',):
        return _embed_youtube_shortcode(url)
    elif url.netloc in ('bitchute.com', 'www.bitchute.com'):
        return _embed_bitchute(url)
    elif ext in ('webm', 'mp4'):
        return _embed_html5_video(url)
    else:
        raise EmbeddingNotSupportedException('Unrecognized service.')

def _add_img_tag(parser):
    def render_image(tag_name, value, options, parent, context):
        if not _is_http_url(value):
            return ''

        return (
            '<a class="img-embed" href="%s">'
                '<img src="%s">'
            '</a>'
        ) % (value, value)


    parser.add_formatter(
        'img',
        render_image,
        render_embedded=False,
        replace_links=False,
        replace_cosmetic=False)

    return parser

def _add_img_stub_tag(parser):
    def render_image_stub(tag_name, value, options, parent, context):
        if not _is_http_url(value):
            return ''

        return (
            'embedded image: <a class="img-link" href="%s">%s</a>'
        ) % (value, value)

    parser.add_formatter(
        'img',
        render_image_stub,
        render_embedded=False,
        replace_links=False,
        replace_cosmetic=False)


    return parser

def _add_video_stub_tag(parser):
    def render_video_stub(tag_name, value, options, parent, context):
        if not _is_http_url(value):
            return ''

        return (
            'embedded video: <a class="img-link" href="%s">%s</a>'
        ) % (value, value)

    parser.add_formatter(
        'video',
        render_video_stub,
        render_embedded=False,
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
            author_str = html.escape(author)
            attribution = 'Originally posted by %s' % author_str

            if pk:
                try:
                    url = reverse('post', kwargs={'post_id': pk})
                except NoReverseMatch:
                    pass
                else:
                    attribution = """
                        Originally posted by %s
                        <a class="jump-to-post" href="%s"></a>
                    """ % (author_str, url)

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
                         render_embedded=False, replace_links=False)
    return parser

def _add_bc_tag(parser):
    def render_bc(tag_name, value, options, parent, context):
        if not _is_http_url(value):
            return ''

        return ('<a class="unproc-embed" href="%s">embedded bandcamp link</a>'
                % value)

    parser.add_formatter('bc', render_bc, replace_cosmetic=False,
                         replace_links=False, render_embeded=False)
    return parser

def _add_link_tag(parser):
    default_url_hanlder, _ = parser.recognized_tags['url']
    parser.add_formatter('link', default_url_hanlder, replace_cosmetic=False)

    return parser

def _add_spoiler_tag(parser):

    def render_spoiler(tag_name, value, options, parent, context):
        name = html.escape(options.get(tag_name, 'spoiler'))
        return utils.render_spoiler(value, name=name, js_enabled=True)

    parser.add_formatter('spoiler', render_spoiler)
    return parser

def _add_nojs_spoiler_tag(parser):

    def render_nojs_spoiler(tag_name, value, options, parent, context):
        name = html.escape(options.get(tag_name, 'spoiler'))
        return utils.render_spoiler(value, name=name, js_enabled=False)

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

def _add_pgp_preprocessor(parser):
    def _replace_sig(match):
        return '[pgp]%s[/pgp]%s' % (
            match.group('message'),
            match.group('plaintext'))

    def _preprocess_pgp_signatures(text):
        return PGP_SIG_PAT.sub(_replace_sig, text)

    parser.add_preprocessor(_preprocess_pgp_signatures)

    return parser

def _add_pgp_tag(parser):
    def render_pgp(tag_name, value, options, parent, context):
        rows = value.count('\n') + 1
        return ("""
            <div class="pgp-block">
                <button title="Post is PGP signed. Show signature.">
                    <i class="show-pgp-sig"></i>
                </button>
                <textarea rows="%d" readonly="true">%s</textarea>
            </div>
        """ % (rows, value))

    parser = _add_pgp_preprocessor(parser)
    parser.add_formatter('pgp', render_pgp, replace_cosmetic=False,
                         render_embedded=False, replace_links=False,
                         transform_newlines=False)
    return parser

def _add_nojs_pgp_tag(parser):
    def render_pgp(tag_name, value, options, parent, context):
        echo_url = reverse('echo')

        return ("""
            <form method="POST" action="%s">
                <input type="hidden" name="content" value="%s" />
                [[ This post contains PGP signed content. To see the raw
                version for verification,
                <input type="submit" value="click here" > ]]
            </form>
        """ % (echo_url, value))

    parser = _add_pgp_preprocessor(parser)
    parser.add_formatter('pgp', render_pgp, replace_cosmetic=False,
                         render_embedded=False, replace_links=False,
                         transform_newlines=False)
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

def _add_quote_stripper(parser):
    def depyramiding_quote_render(tag_name, value, options, parent, context):
        if tag_name == 'quote':
            return ''

        return value

    parser.add_formatter('quote', depyramiding_quote_render)
    return parser

def _add_cooltag_stripper(parser):
    return parser.add_simple_formatter(
        'byusingthistagIaffirmlannyissupercool',
        '%(value)s')

def _add_pgp_stripper(parser):
    parser.add_preprocessor(
        lambda text: PGP_SIG_PAT.sub(lambda m: m.group('plaintext'), text))

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
    'SHORTCODE': _add_shortcode_tag,
    'PGP': _add_pgp_tag,
    'NOJS_PGP': _add_nojs_pgp_tag,
    'STRIP_QUOTE': _add_quote_stripper,
    'STRIP_PGP': _add_pgp_stripper,
    'STRIP_COOL_TAG': _add_cooltag_stripper,
    'NOP': lambda parser: parser
}

def build_parser(tags, escape_html=True, **kwargs):
    opts = {
        'replace_cosmetic': False,
        'max_tag_depth': 10
    }
    opts.update(kwargs)
    parser = PreprocessingParser(escape_html=escape_html, **opts)

    for tag in tags:
        _supported_tags[tag](parser)

    if 'link' in parser.recognized_tags:
        del parser.recognized_tags['link']

    return parser

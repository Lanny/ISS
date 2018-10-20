import os

class HomoglyphNormalizer(object):
    """
    Loads a structured list of homoglyphs and produces "normalized" unicode
    sequences where differing input sequences that are visually ambigious (per
    a configurable definition of homoglyph) produce the same output sequence.
    Also normalizes case differences, whatever that means on a point-by-point
    basis. Note that normalization is injective with structured collision
    conditions, normalized strings should be considered a "hash" of their input
    rather than a presentable string.
    """
    _INSTANCE = None

    @classmethod
    def _decode_hex_repr(cls, s):
        return ('\\U%08x' % int(s, 16)).decode('unicode-escape')

    @classmethod
    def _decode_seq(cls, s):
        return u''.join(
            [cls._decode_hex_repr(point) for point in s.strip().split(' ')]
        )

    @classmethod
    def normalize_homoglyphs(cls, prenormalized):
        """
        Normalize a homoglyph string using the default configuration and
        confusables list.
        """
        if not cls._INSTANCE:
            cls._INSTANCE = cls()

        return cls._INSTANCE.normalize(prenormalized)

    def __init__(self, confusables_file=None):
        if not confusables_file:
            base = os.path.dirname(os.path.abspath(__file__))
            path = os.path.join(base, '../support/confusables.txt')
            confusables_file = open(path, 'r')

        self._norm_graph = {}

        with confusables_file:
            for line in confusables_file:
                # Strip off comments
                effective_line = line.split('#', 1)[0].strip()

                if effective_line.count(';') < 2:
                    continue

                confusable_seq, target_seq, _ = effective_line.split(';', 2)
                confusable = self._decode_seq(confusable_seq)
                target = self._decode_seq(target_seq)

                if self._norm_graph.has_key(confusable):
                    f.close()
                    raise ValueError('One confusable codepoint has multiple '
                                     'normalization targets.')

                self._norm_graph[confusable] = target

    def _norm_codepoint(self, code_point):
        if self._norm_graph.has_key(code_point):
            return self._norm_graph[code_point]
        else:
            return code_point

    def normalize(self, unicode_str):
        """
        Normalize a unicode string.
        """
        if not isinstance(unicode_str, unicode):
            unicode_str = unicode(unicode_str)

        normalized = []
        for code_point in unicode_str:
            normalized.append(self._norm_codepoint(code_point.lower()))
            normalized.append(self._norm_codepoint(code_point.upper()))

        return u''.join(normalized)

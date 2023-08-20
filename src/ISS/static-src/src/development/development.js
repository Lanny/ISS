;(function() {

  function wrap($, config) {
    $(document).on('keydown', function(e) {
        if (e.keyCode === 80 && (e.ctrlKey || e.metaKey)) {
          e.preventDefault();

          var themeEl = $('#theme-sheet'),
            currentTheme = unescape(themeEl
              .attr('href')
              .match('/static/css/(.+)\.css')[1]),
            themes = config.getConfig('themes'),
            themeIdx = themes
              .map(function(t) { return t.code; })
              .indexOf(currentTheme),
            newTheme = themes[(themeIdx + 1) % themes.length];

          themeEl.attr('href', newTheme.stylesheet);
        }
    });

    $(function() {
      console.warn('Loading development scripts. This should NOT be seen in ' +
        'production')
    });
  }

  require([
    'jquery',
    'config'
  ], wrap);
})();

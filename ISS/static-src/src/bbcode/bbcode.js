;(function() {
  function wrap($) {
    var Module = {
      bindRegion: function(region) {
        region = $(region);
        this.bindSpoilerHandlers(region);
        this.embedBandcampLinks(region);
      },
      bindSpoilerHandlers: function(region) {
        region.find('.spoiler')
          .each(function(_, e) {
            e = $(e);

            if (e.data('contentVisible') !== undefined) {
              return;
            }

            e.data('contentVisible', false);
            var tab = e.children('.tab'),
              content = e.children('.content');

            tab.on('click', function() {
              if (content.attr('data-content')) {
                content.html(content.attr('data-content'));
                content.removeAttr('data-content')
              }

              if (e.data('contentVisible')) {
                tab.find('.label').text('Show');
                content.css('display', 'none');
                e.data('contentVisible', false);
              } else {
                tab.find('.label').text('Hide');
                content.css('display', 'block');
                e.data('contentVisible', true);
              }
            })
          });
      },
      embedBandcampLinks: function(region) {
        region.find('.unproc-embed')
          .each(function(i, e) {
            var $e = $(e),
              href = $e.attr('href');

            $.getJSON(config.getConfig('bandcamp-embed-url'), {url: href})
              .done(function(data) {
                if (data.status && data.status === 'SUCCESS') {
                  $e.replaceWith($(data.embedCode));
                }
              })
          });
      }
    };

    return Module;
  }

  define([
    'jquery'
  ], wrap);
})();

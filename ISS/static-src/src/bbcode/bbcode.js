;(function() {
  function wrap($) {
    var Module = {
      bindRegion: function(region) {
        region = $(region);
        Module.bindSpoilerHandlers(region);
        Module.embedBandcampLinks(region);
      },
      bindSpoilerHandlers: function(region) {
        region.find('.spoiler')
          .each(function(_, e) {
            e = $(e);

            if (e.data('spoilerInited') !== undefined) {
              return;
            }
            e.data('spoilerInited', true);

            var tab = e.children('.tab'),
              content = e.children('.content');

            tab.on('click', function() {
              if (content.attr('data-content')) {
                content.html(content.attr('data-content'));
                content.removeAttr('data-content');
                Module.bindRegion(content);
              }

              if (e.hasClass('closed')) {
                e.removeClass('closed').addClass('open')
                tab.find('.label').text('Show');
              } else {
                e.removeClass('open').addClass('closed')
                tab.find('.label').text('Hide');
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

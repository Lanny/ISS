;(function() {
  function wrap($, config, utils, spoilers) {
    var Module = {
      bindRegion: function(region) {
        region = $(region);
        Module.bindSpoilerHandlers(region);
        Module.bindPGPHandlers(region);
        Module.embedBandcampLinks(region);
        Module.shakeSuperCoolElements(region);
      },
      bindSpoilerHandlers: function(region) {
        region.find('.spoiler')
          .each(function(_, e) {
            spoilers.bindSpoilerHandler(e, function(content) {
              // Bind BBCode handlers once the spoiler is shown for the first
              // time.
              Module.bindRegion(content);
            });
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
      },
      bindPGPHandlers: function(region) {
        region.find('.pgp-block').each(
          function(i, e) {
            var $e = $(e),
              button = $e.children('button'),
              signedMessage = $e.children('textarea');

            button.on('click', function(e) {
              signedMessage.addClass('show')
                .focus();
              var rawEl = signedMessage[0];
              rawEl.selectionStart = 0;
              rawEl.selectionEnd = signedMessage.val().length;
            });

            signedMessage.on('focusout', function(e) {
              signedMessage.removeClass('show');
            });
          });
          
      },
      shakeSuperCoolElements: function(region) {
         utils.shake($('.ex'), 10);
      }
    };

    return Module;
  }

  define([
    'jquery',
    'config',
    'utils',
    'spoilers'
  ], wrap);
})();

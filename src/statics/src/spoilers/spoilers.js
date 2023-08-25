;(function() {
  function wrap($) {
    var Module = {
      bindSpoilerHandler: function(e, onShow) {
        e = $(e);
        onShow = onShow || function() {};

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
            onShow(content);
          }

          if (e.hasClass('closed')) {
            e.removeClass('closed').addClass('open')
            tab.find('.label').text('Hide');
          } else {
            e.removeClass('open').addClass('closed')
            tab.find('.label').text('Show');
          }
        })
      }
    };

    return Module;
  }

  define([
    'jquery'
  ], wrap);
})();

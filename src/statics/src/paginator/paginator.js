;(function() {
  function wrap($) {
    var Module = {
      bindKeyboardControls: function() {
        var paginator = $('.paginator').first();

        if (paginator.length !== 1) return;

        $('body').on('keydown', function(e) {
          if ($(e.target).is('input, textarea')) {
            // Don't mess with useragent editor use of arrow keys
            return;
          }

          var href;
          if (e.keyCode === 37) {
            href = paginator.find('a.previous-page').attr('href');
          } else if (e.keyCode == 39) {
            var href = paginator.find('a.next-page').attr('href');
          }

          if (href) document.location.assign(href);
        });
      }
    };

    return Module;
  }

  define(['jquery'], wrap);
})();

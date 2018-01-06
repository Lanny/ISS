;(function() {
  function wrap($) {
    var Module = {
      bindKeyboardControls: function() {
        var paginator = $('.paginator').first();

        if (paginator.length !== 1) return;

        $('body').on('keydown', function(e) {
          var href;
          if (e.keyCode === 37) {
            var href = paginator.find('a.previous-page').attr('href');
            document.location.assign(href);
          } else if (e.keyCode == 39) {
            var href = paginator.find('a.next-page').attr('href');
            document.location.assign(href);
          }
        });
      }
    };

    return Module;
  }

  define(['jquery'], wrap);
})();

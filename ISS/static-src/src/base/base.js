;(function() {

  function wrap($, config, bbcode, paginator, hyperDrive) {
    console.log('HD loaded supposedly');
    function peek() {
      var peekaboo = $('.peekaboo').first()
        .css('display', 'block');

      peekaboo.animate({'left': -100}, 1500, 'linear', function() {
        window.setTimeout(function() {
          peekaboo.animate({'left': 0}, 500);
        }, 250);
      });
    }

    $(document).on('click', '.hyper-drive', function() {
      hyperDrive.start()
    });

    $(function() {
      bbcode.bindRegion($('.page-content'));
      paginator.bindKeyboardControls();

      window.setTimeout(peek, Math.random()*1000*60*60);

      if ($('.g-recaptcha').length > 0) {
        $(document.documentElement).append(
          '<script src="https://www.google.com/recaptcha/api.js"></script>');
      }
    });
  }

  require([
    'jquery',
    'config',
    'bbcode',
    'paginator',
    'hyper-drive'
  ], wrap);
})();



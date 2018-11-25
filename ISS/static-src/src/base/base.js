;(function() {

  function wrap($, config, bbcode, paginator, hyperDrive) {
    $(document).on('click', '.hyper-drive', function() {
      hyperDrive.start()
    });

    $(function() {
      bbcode.bindRegion($('.page-content'));
      paginator.bindKeyboardControls();

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



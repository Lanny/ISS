;(function() {

  function wrap($, config, bbcode, paginator, CheckboxList, hyperDrive) {
    $(document).on('click', '.hyper-drive', function() {
      hyperDrive.start()
    });

    $(function() {
      bbcode.bindRegion($('.page-content'));
      paginator.bindKeyboardControls();

      $('[data-form-name="logout-form"]').on('submit', function(e) {
        if (!window.confirm('Are you sure you want to log out?')) {
          e.preventDefault();
        }
      });

      if ($('.g-recaptcha').length > 0) {
        $(document.documentElement).append(
          '<script src="https://www.google.com/recaptcha/api.js"></script>');
      }

      $('[data-checkbox-list-container]').each(function(i, el) {
        new CheckboxList(el);
      });
    });
  }

  require([
    'jquery',
    'config',
    'bbcode',
    'paginator',
    'checkbox-list',
    'hyper-drive'
  ], wrap);
})();



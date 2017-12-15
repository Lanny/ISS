;(function() {
  function wrap($) {
    $(function() {
      var controlLinks = $('.user-controls .control-links');
      $('.user-controls .user-control-hamburger').on('click', function() {
        controlLinks.toggleClass('open');
      });
    });
  }

  define([ 'jquery' ], wrap);
})();




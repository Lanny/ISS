;(function() {
  function wrap($) {
    function shake(el, intensity) {
      el.css({
        position: 'relative',
        top: ~~((Math.random() - 0.5) * intensity),
        left: ~~((Math.random() - 0.5) * intensity)
      });

      window.setTimeout(shake.bind(this, el, intensity), 50);
    };

    return {
      shake: shake
    };
  }

  define([
    'jquery'
  ], wrap);
})();



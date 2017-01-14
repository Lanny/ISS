;(function() {
  function wrap() {
    var module = {};

    module.getConfig = function(optName) {
      return window.config[optName];
    };

    return module;
  }

  define([], wrap);
})();

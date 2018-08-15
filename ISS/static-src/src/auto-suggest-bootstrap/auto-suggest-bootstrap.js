;(function() {
  function wrap($, AutoSuggest) {
  	$(function() {
  	  $('[data-auto-suggest]')
	      .each(function(i, el) {
          var $el = $(el);

          new AutoSuggest($el, {
            queryUrl: $el.attr('data-auto-suggest-endpoint'),
            delimiter: $el.attr('data-auto-suggest-delimiter')
          });
        });
	    })
  }

  define([
    'jquery',
    'auto-suggest',
    'base'
  ], wrap);
})();




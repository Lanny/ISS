/* 
 * A simple bootstrap that inits the editor component on every element with
 * the editor class on the page.
 */
;(function() {
  function wrap($, Editor, AutoSuggest) {
    $(function() {
      $('.editor').each(function(_, el) {
        new Editor(el);
      });
    });
  }

  define([
    'jquery',
    'editor',
    'auto-suggest',
    'base'
  ], wrap);
})();




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

      new AutoSuggest($('#id_to')[0], {
        queryUrl: '/api/users/search',
        delimiter: ','
      });
    });
  }

  define([
    'jquery',
    'editor',
    'auto-suggest',
  ], wrap);
})();




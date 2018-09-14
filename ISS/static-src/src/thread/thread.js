;(function() {
  function wrap($, thanks, Editor, CheckboxRangeSelector) {
    $(function() {
      $('.editor').each(function(_, el) {
        new Editor(el, {saveContent: true});
      });

      $('body').on('click', '.quote', function(e) {
        e.preventDefault();

        var setFocus = !e.shiftKey;
        var quoteFetchUrl = $(e.target).attr('data-bbc-url'),
          editor = $('.quick-reply').data('editor');

        $.getJSON(quoteFetchUrl)
          .done(function(data) {
            editor.addQuote(data.content, setFocus);
          })
          .fail(function(data) {
            alert('Failed to fetch quote.');
          });
      });

      $('.thread').on('submit', '.thank-action-form', function(e) {
        e.preventDefault();
        var button = $(e.currentTarget).find('.thank-action');
        thanks.handleThankIntention(button);
      });

      new CheckboxRangeSelector('.post-list', {
        checkboxSelector: 'input[form="post-actions"]'
      });
    });
  }

  define([
    'jquery',
    'thanks',
    'editor',
    'checkbox-range-select',
    'base'
  ], wrap);
})();



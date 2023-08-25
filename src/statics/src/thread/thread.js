;(function() {
  function wrap($, thanks, Editor, CheckboxRangeSelector) {
    $(function() {
      $('.editor').each(function(_, el) {
        new Editor(el, {saveContent: true});
      });

      $('body').on('click', '.quote', function(e) {
        e.preventDefault();
        var button = $(e.currentTarget)
        var setFocus = !e.shiftKey;
        var quoteFetchUrl = $(e.target).attr('data-bbc-url'),
          editor = $('.quick-reply').data('editor');

        if (button.is('[aria-disabled="true"]')) return;
        button.attr('aria-disabled', 'true')

        $.getJSON(quoteFetchUrl)
          .done(function(data) {
            editor.addQuote(data.content, setFocus);
          })
          .fail(function(data) {
            alert('Failed to fetch quote.');
          })
          .always(function() {
            button.attr('aria-disabled', 'false')
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



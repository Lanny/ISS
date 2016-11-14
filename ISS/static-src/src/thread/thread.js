;(function() {
  function wrap($, thanks) {
    $(function() {
      $('body').on('click', '.quote', function(e) {
        e.preventDefault();

        var quoteFetchUrl = $(e.target).attr('data-bbc-url'),
          replyTextbox = $('.quick-reply #id_content');

        $.getJSON(quoteFetchUrl)
          .done(function(data) {
            var oldVal = replyTextbox.val(),
              newVal;

            if (oldVal === '') {
              newVal = data.content;
            } else {
              newVal = oldVal + '\n\n' + data.content;
            }

            replyTextbox.val(newVal + '\n\n')
              .focus();
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
    });
  }

  define(['jquery', 'thanks'], wrap);
})();

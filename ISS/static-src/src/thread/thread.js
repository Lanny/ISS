;(function() {
  function wrap($) {
    $(function() {
      $('body').on('click', '.quote', function(e) {
        e.preventDefault();

        var quoteFetchUrl = $(e.target).attr('data-bbc-url');

        $.getJSON(quoteFetchUrl)
          .done(function(data) {
            var replyTextbox = $('.quick-reply #id_content'),
              oldVal = replyTextbox.val(),
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
    });
  }

  define(['jquery'], wrap);
})();

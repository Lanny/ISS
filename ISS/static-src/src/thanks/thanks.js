;(function() {
  function wrap($) {
    var module = {
      handleThankIntention: function(buttonElement) {
        var button = $(buttonElement),
          form = button.closest('form'),
          post = form.closest('.post'),
          thanksBlock = post.find('.thanker-block'),
          controlsBlock = post.find('.post-controls'),
          csrfToken = form.find('[name=csrfmiddlewaretoken]').attr('value');

        if (button.is('[disabled]')) {
          e.preventDefault();
          return;
        }

        button.prop('disabled', true);

        return $.ajax(form.attr('action'), {
            method: form.attr('method'),
            data: { 'csrfmiddlewaretoken': csrfToken },
            dataType: 'json'
          })
          .done(function(data) {
            if (data.status !== 'SUCCESS') {
              alert('Failed to submit request');
              return;
            }

            if (thanksBlock.length < 1) {
              thanksBlock = $('<div>').appendTo(post);
            }

            thanksBlock.replaceWith($(data.thanksBlock));
            controlsBlock.replaceWith($(data.postControls));
          })
          .fail(function(data) {
            console.error(data);
            alert('Failed to submit request');
          })
          .always(function() {
            button.prop('disabled', false);
          });
      }
    };

    return module;
  }

  define(['jquery'], wrap);
})();

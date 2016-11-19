;(function() {
  function wrap($) {
    function Editor(element) {
      this._el = $(element);
      this._ta = this._el.find('textarea');

      this._el.data('editor', this);
      this._bindHandlers();
    }

    Editor.prototype = {
      _bindHandlers: function() {
        var self = this;

        self._ta.on('keydown', function(e) {
          if (e.keyCode === 13 && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            self._el.trigger('submit');
          }
        });
      },
      addQuote: function(quoteCode) {
        var self = this,
          oldVal = self._ta.val(),
          newVal;

        if (oldVal === '') {
          newVal = quoteCode;
        } else {
          newVal = oldVal + '\n\n' + quoteCode;
        }

        self._ta.val(newVal + '\n\n')
          .focus();
      }
    }

    return Editor;
  }

  define(['jquery'], wrap);
})();

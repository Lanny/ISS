;(function() {
  function wrap($) {
    function AutoSuggest(inputElement, options) {
      this._el = $(inputElement)
        .attr('autocomplete', 'off');
      this._container = this._el
        .wrap('<div class="auto-suggest-wrapper">')
        .parent();
      this._suggestionsBox = $('<ul class="auto-suggestions">')
        .appendTo(this._container);
      this._qUrl = options.queryUrl;
      this._delimiter = options.delimiter;

      this._lastQuery = null;
      this._preventNextQuery = false;
      this._pendingQuery = null;
      this._selectedOption = 0;

      this._bindHandlers();
    }

    AutoSuggest.prototype = {
      _bindHandlers: function() {
        var self = this;
        this._el.on('keydown', function(e) {
          if (e.keyCode === 38) {
            e.preventDefault();
            self._selectedOption = Math.max(self._selectedOption - 1, 0);
            self._rectifySelection();
          } else if (e.keyCode === 40) {
            e.preventDefault();
            var optsLen = self._suggestionsBox.children().length;
            self._selectedOption = Math.min(self._selectedOption + 1, optsLen - 1);
            self._rectifySelection();
          } else if (e.keyCode === 13) {
            self._setCurrentTerm(self._suggestionsBox.find('.active').text());

            // Hide the box and prevent the revently entered value from
            // causing it to open again
            self._preventNextQuery = true;
            self._close();
            e.preventDefault();
          } else if (e.keyCode === 27) {
            self._close();
          }
        });
        this._el.on('focusin', function() { self._open(); })
          .on('focusout', function() { self._close(); });

        this._el.on('keyup', function(e) {
          self._queryMaybe();
        });
      },
      _getCurrentTerm: function() {
        var rawVal = this._el.val();
        if (this._delimiter) {
          var terms = rawVal.split(this._delimiter),
            currentTerm = terms[terms.length - 1];

          return currentTerm.replace(/$\s*/, '');
        } else {
          return rawVal;
        }
      },
      _setCurrentTerm: function(term) {
        var rawVal = this._el.val();
        if (this._delimiter) {
          var terms = rawVal.split(this._delimiter);
          terms[terms.length - 1] = term;
          this._el.val(terms.join(this._delimiter));
        } else {
          this._el.val(term);
        }
      },
      _queryMaybe: function() {
        var self = this,
          currentVal = this._getCurrentTerm();

        if (self._preventNextQuery) {
          self._preventNextQuery = false;
          return;
        }

        if (currentVal && currentVal !== this._lastQuery && !this._pendingQuery) {
          this._lastQuery = currentVal;
          this._pendingQuery = $.getJSON(this._qUrl, {q: currentVal})
            .done(function(res) {
              self._suggestionsBox.empty();
              for (var i=0; i<res.results.length; i++) {
                var result = res.results[i];
                $('<li>').text(result.name)
                  .appendTo(self._suggestionsBox);
              }
              self._open();
            })
            .always(function() {
              self._pendingQuery = null;
              self._rectifySelection();
              self._queryMaybe();
            });
        }
      },
      _rectifySelection: function() {
        this._suggestionsBox.find('.active').removeClass('active');
        $(this._suggestionsBox.find('li')[this._selectedOption])
          .addClass('active');
      },
      _open: function() {
        this._suggestionsBox.css('display', 'block');
      },
      _close: function() {
        this._suggestionsBox.css('display', 'none');
      }
    }

    return AutoSuggest;
  }

  define(['jquery'], wrap);
})();

;(function() {
  var sessionStorage = window.sessionStorage || {};

  function wrap($, AutoSuggest, bbcode) {
    var wrapOperations = [
      {
        name: 'bold',
        pre: '[b]',
        post: '[/b]',
        hotKeyCode: 66,
        buttonClass: 'bold'
      },
      {
        name: 'underline',
        pre: '[u]',
        post: '[/u]',
        hotKeyCode: 85,
        buttonClass: 'underline'
      },
      {
        name: 'oblique',
        pre: '[i]',
        post: '[/i]',
        hotKeyCode: 73,
        buttonClass: 'oblique'
      },
      {
        name: 'image',
        pre: '[img]',
        post: '[/img]',
        hotKeyCode: 73,
        buttonClass: 'image',
        useAlt: true
      },
      {
        name: 'video',
        pre: '[video]',
        post: '[/video]',
        hotKeyCode: 86,
        buttonClass: 'video',
        useAlt: true
      },
    ];

    // Ensure all keys requiring an alt check occur before those that do not.
    wrapOperations.sort(function(l, r) {
      // i r vry smrt!
      return !l.useAlt - !r.useAlt;
    });

    var promptDefaults = {
      promptText: 'Enter text:'
    };

    function promptForInput(opts) {
      var options = $.extend({}, promptDefaults, opts),
        deferred = $.Deferred(),
        result = window.prompt(options.promptText);

      if (typeof result === 'string') {
        deferred.resolve(result);
      } else {
        deferred.reject();
      }

      return deferred.promise();
    }

    var defaults = {
      saveContent: false
    };

    function Editor(element, options) {
      this.settings = $.extend({}, defaults, options);
      this._el = $(element);
      this._ta = this._el.find('textarea');
      this._deconstructing = false;

      this._el.data('editor', this);

      if (this._getStoreKey() in sessionStorage) {
        this._ta.val(sessionStorage[this._getStoreKey()]);
      }

      if (window.config['editor-buttons']) {
        this._edButtonContainer = $('<div class="editor-buttons">');

        for (var i=0; i<wrapOperations.length; i++) {
          var button = $('<button>')
            .addClass('wrap-operation')
            .addClass(wrapOperations[i].buttonClass)
            .attr('title', wrapOperations[i].name)
            .attr('tabindex', -1)
            .data('wrapOp', wrapOperations[i])
            .appendTo(this._edButtonContainer);
        }

        this._ta.before(this._edButtonContainer);
      }

      this._el.find('[data-auto-suggest]')
        .each(function(i, el) {
          var $el = $(el);

          new AutoSuggest($el, {
            queryUrl: $el.attr('data-auto-suggest-endpoint'),
            delimiter: $el.attr('data-auto-suggest-delimiter')
          });
        });

      this._bindHandlers();
    }

    Editor.prototype = {
      _populateControls: function() {
      },
      _bindHandlers: function() {
        var self = this;

        this._ta.on('keydown', function(e) {
          if (e.keyCode === 13 && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            self._el.trigger('submit');
          } else if (e.ctrlKey || e.metaKey) {
            for (var i=0; i<wrapOperations.length; i++) {
              if (e.keyCode === wrapOperations[i].hotKeyCode) {
                if (wrapOperations[i].useAlt && !e.altKey) {
                  continue;
                }

                e.preventDefault();
                self.executeWrapIntension(wrapOperations[i]);
                break;
              }
            }
          }
        });

        this._ta.on('keyup', function(e) {
          if (self.settings.saveContent && !self._deconstructing) {
            self._sessSave();
          }
        });

        this._el.on('submit', function() {
          self._deconstructing = true;
          self._sessClear();
        });

        this._el.on('click', '.editor-buttons .wrap-operation', function(e) {
          self.executeWrapIntension($(e.target).data('wrapOp'));
          return false;
        });

        this._el.on('click', 'input.preview-post-action', function(e) {
          var input = $(e.target),
            url = input.attr('data-preview-url'),
            csrfToken = self._el
              .find('[name=csrfmiddlewaretoken]')
              .attr('value');

          e.preventDefault();

          if (input.is('[disabled]')) return;

          input.prop('disabled', true);

          $.ajax(url, {
            method: 'POST',
            data: {
              'csrfmiddlewaretoken': csrfToken,
              'content': self._ta.val()
            },
            dataType: 'json'
          })
          .done(function(data) {
            if (data.status !== 'FORM_INVALID' && data.errors) {
              self.applyErrors(data.errors)
              return;
            } else  if (data.status !== 'SUCCESS') {
              alert('Failed to submit request');
              return;
            }

            self.clearErrors();

            var priorPreview = self._el.find('.post-preview-block');
            var newPreview = $(data.postPreview);

            if (priorPreview.length) {
              priorPreview.replaceWith(newPreview);
            } else {
              newPreview.insertBefore(self._el.find('fieldset:first'));
            }

            // Bind all those sexy bbcode frills
            bbcode.bindRegion(newPreview);
          })
          .fail(function(data) {
            console.error(data);
            alert('Failed to submit request');
          })
          .always(function() {
            input.prop('disabled', false);
          });
        });
      },
      _getStoreKey: function() {
        return 'editor-content:' + document.location.pathname;
      },
      _sessClear: function() {
        delete sessionStorage[this._getStoreKey()];
      },
      _sessSave: function() {
        var content = this._ta.val();
        sessionStorage[this._getStoreKey()] = content;

      },
      executeWrapIntension: function(wrapOp) {
        var self = this,
          selStart = self._ta[0].selectionStart,
          selEnd = self._ta[0].selectionEnd,
          content = self._ta.val(),
          preContent = content.substring(0, selStart),
          selContent = content.substring(selStart, selEnd),
          postContent = content.substring(selEnd);

        function wrapAndInsertContent(insertionContent) {
          var wrappedContent = wrapOp.pre + insertionContent + wrapOp.post;
          self._ta.val(preContent + wrappedContent + postContent);

          // Timeout hack so val change registers and we can set a selection
          // range
          setTimeout(function() {
            self._ta.focus();
            self._ta[0].selectionStart = selStart;
            self._ta[0].selectionEnd = selStart + wrappedContent.length;

            if (self.settings.saveContent) { self._sessSave(); }
          }, 0);
        }

        if (selStart === selEnd) {
          // Nothing selectied, prompt for content
          promptForInput().done(function(insertionContent) {
            wrapAndInsertContent(insertionContent);
          });
        } else {
          wrapAndInsertContent(selContent);
        }
      },
      addQuote: function(quoteCode, setFocus) {
        var self = this,
          oldVal = self._ta.val(),
          newVal;

        if (oldVal === '') {
          newVal = quoteCode;
        } else {
          newVal = oldVal + '\n\n' + quoteCode;
        }

        self._ta.val(newVal + '\n\n');

        if (setFocus) { self._ta.focus(); }
        if (self.settings.saveContent) { self._sessSave(); }
      },
      applyErrors: function(errors) {
        for (var field in errors) {
          var fieldErrors = errors[field],
            errorList = $('<ul class="errorlist">');

          for (var i=0; i<fieldErrors.length; i++) {
            $('<li>')
              .text(fieldErrors[i])
              .appendTo(errorList);
          }

          var fieldEl = this._el.find('[name="' + field + '"]'),
            priorErrorList = fieldEl.prev('.errorlist');

          if (priorErrorList.length) {
            priorErrorList.replaceWith(errorList);
          } else {
            errorList.insertBefore(fieldEl);
          }
        }
      },
      clearErrors: function() {
        this._el.find('.errorlist').remove();
      }
    }

    return Editor;
  }

  define([
    'jquery',
    'auto-suggest',
    'bbcode'
  ], wrap);
})();



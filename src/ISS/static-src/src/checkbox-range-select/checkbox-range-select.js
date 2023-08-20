;(function() {
  var sessionStorage = window.sessionStorage || {};

  function wrap($) {
    var defaults = {
      checkboxSelector: 'input[type="checkbox"]'
    }

    function CheckboxRangeSelector(element, options) {
      this.settings = $.extend({}, defaults, options);
      this._el = $(element);
      this._lastSelection = null;

      this._bindHandlers();
    }

    CheckboxRangeSelector.prototype = {
      _bindHandlers: function() {
        var self = this;

        this._el.on('click', self.settings.checkboxSelector, function(e) {
          if (self._lastSelection && e.shiftKey) {
            var cbs = self._getCheckboxes(),
              targetVal = this.checked,
              startIdx = cbs.index(self._lastSelection),
              endIdx = cbs.index(this),
              direction = Math.sign(endIdx - startIdx) || 1;

            for (var i=startIdx; i !== endIdx + direction; i += direction) {
              cbs[i].checked = targetVal;
            }
          }

          self._lastSelection = this;
        });
      },
      _getCheckboxes: function() {
        return this._el.find(this.settings.checkboxSelector);
      }
    }

    return CheckboxRangeSelector;
  }

  define([
    'jquery'
  ], wrap);
})();



;(function() {
  function wrap($) {
    function CheckboxList(container) {
      this.container = $(container);
      this.name = this.container.attr('data-checkbox-list-container');
      this.lastClickedIndex = null;

      if (!this.name) {
        throw new Error('Checkbox list container must have a non-empty ' +
          '`data-checkbox-list-container` attribute.');
      }

      var selector  = '[data-checkbox-list="' + this.name + '"]';
      this.checkboxes = $(container)
        .find(selector)
        .on('click', this._onClick.bind(this));
    }

    CheckboxList.prototype = {
      _onClick: function(e) {
        var idx = this.checkboxes.index(e.target);

        if (this.lastClickedIndex === null) {
          this.lastClickedIndex = idx;
          return;
        }

        if (e.shiftKey) {
          var dir = Math.sign(idx - this.lastClickedIndex);
          for (var i = this.lastClickedIndex+dir; i !== idx; i += dir) {
            this.checkboxes[i].checked = e.target.checked
          }
        }

        this.lastClickedIndex = idx;
      }
    }

    return CheckboxList;
  }

  define(['jquery'], wrap);
})();

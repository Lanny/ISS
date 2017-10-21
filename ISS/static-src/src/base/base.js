;(function() {
  function shakeBaby(baby, intensity) {
    baby.css({
      position: 'relative',
      top: ~~((Math.random() - 0.5) * intensity),
      left: ~~((Math.random() - 0.5) * intensity)
    });

    window.setTimeout(shakeBaby.bind(this, baby, intensity), 50);
  };

  function genCircle(color, size) {
    return $('<div class="hyper-circle">')
      .css({
        background: color,
        width: size,
        height: size,
        'border-radius': size,
        display: 'block',
        position: 'fixed'
      });
  }

  function startHyperDrive() {
    var width = $(window).width(),
      height = $(window).height();

    var circles = [],
      totalVolume = width * height
      runningVolume = 0,
      targetDensity = 5.0;

    while (runningVolume/totalVolume < targetDensity) {
      var circSize = ~~(100 + Math.random() * (width - 100) / 2),
        r = ~~(Math.random()*255),
        g = ~~(Math.random()*255),
        b = ~~(Math.random()*255),
        circ = genCircle('rgba('+r+','+g+','+b+',0.3)', circSize);

      circles.push(circ);
      runningVolume += Math.PI *  circSize * circSize;
    }

    for (var i=0; i<circles.length; i++) {
      ;(function() {
        var aniTarget = circles[i],
          circSize = aniTarget.width();

        aniTarget.appendTo('body')
          .css({
            top: Math.random() * height - circSize / 2,
            left: Math.random() * width - circSize / 2
          });

        ;(function animateCircPos() {
          var targTop = Math.random() * height - circSize / 2,
            targLeft = Math.random() * width - circSize / 2;

          aniTarget.animate(
            {top: targTop, left: targLeft}, 
            {
              duration: Math.random() * 5000,
              queue: false,
              done: animateCircPos
            });
        })();

        var period = 1200,
          amplitude = 0.3,
          initialDirection = Math.sign(Math.random() - 0.5);

        ;(function animateCircSize() {
          var sizeOne = circSize * (1 + amplitude * initialDirection),
            sizeTwo = circSize * (1 - amplitude * initialDirection);

          aniTarget.animate(
            {width: sizeOne, height: sizeOne},
            {
              duration: period / 2,
              queue: false,
              done: function() {
                aniTarget.animate(
                  {width: sizeTwo, height: sizeTwo},
                  {
                    duration: period / 2,
                    queue: false,
                    done: animateCircSize
                  });
              }
            });
        })();
      })();
    }

    shakeBaby($('.page-content'), 20);

    var blurPeriod = 2000,
      degree = 4,
      t0 = Date.now();

    ;(function blurShit() {
      var d = (Date.now() - t0) % blurPeriod,
        s = degree * (d / (blurPeriod * 2));

      if (d > blurPeriod / 2) {
        s = degree - s;
      }

      $(document.documentElement).css('filter', 'blur(' + s + 'px)');

      window.setTimeout(blurShit, 1000/24);
    })();
  };

  function wrap($, config, bbcode) {
    function peek() {
      var peekaboo = $('.peekaboo').first()
        .css('display', 'block');

      peekaboo.animate({'left': -100}, 1500, 'linear', function() {
        window.setTimeout(function() {
          peekaboo.animate({'left': 0}, 500);
        }, 250);
      });
    }

    $(document).on('click', '.hyper-drive', function() {
      startHyperDrive();
    });

    $(function() {
      bbcode.bindRegion($('.page-content'));
      shakeBaby($('.ex'), 10);
      window.setTimeout(peek, Math.random()*1000*60*60);

      if ($('.g-recaptcha').length > 0) {
        $(document.documentElement).append(
          '<script src="https://www.google.com/recaptcha/api.js"></script>');
      }
    });
  }

  require([
    'jquery',
    'config',
    'bbcode'
  ], wrap);
})();



var gulp = require('gulp');
var path = require('path');
var argv = require('yargs').argv;
var flatten = require('gulp-flatten');
var less = require('gulp-sources-less');
var minifyCSS = require('gulp-minify-css');
var clean = require('gulp-clean');

var staticDir = '../static',
  cssDir = path.join(staticDir, 'taboo/css');

gulp.task('clean', function() {
  return gulp.src([ cssDir ])
    .pipe(clean({read: false, force: true}));
});
 
gulp.task('less', function() {

  var lessStream = less({
      paths: [ path.join(__dirname, 'less') ]
    }).on('error', function(err) {
      console.error(err);
      this.emit('end');
    });

  var stream = gulp.src('./src/taboo/taboo.less');

  stream = stream.pipe(lessStream);
  stream = stream.pipe(flatten());
  stream = argv.optimize ? stream.pipe(minifyCSS()) : stream;
  stream = stream.pipe(gulp.dest(cssDir));

  return stream;
});

var generateTasks = ['less']
gulp.task('generate', generateTasks);

gulp.task('watch', ['generate'], function() {
  gulp.watch([ './src/**/*.less' ], ['less']);
});

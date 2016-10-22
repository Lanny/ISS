var gulp = require('gulp');
var flatten = require('gulp-flatten');
var less = require('gulp-sources-less');
var sourcemaps = require('gulp-sourcemaps');
var path = require('path');

 
gulp.task('less', function() {
  var lessStream = less({
      paths: [ path.join(__dirname, 'less') ]
    }).on('error', function(err) {
      console.error(err);
      this.emit('end');
    });

  return gulp.src('./src/**/*.less')
    .pipe(sourcemaps.init())
    .pipe(lessStream)
    .pipe(sourcemaps.write())
    .pipe(flatten())
    .pipe(gulp.dest('../static/css'));
});

gulp.task('generate', ['less']);

gulp.task('watch', ['generate'], function() {
  gulp.watch([ './src/**/*.less' ], ['less']);
});

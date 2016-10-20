var gulp = require('gulp');
var flatten = require('gulp-flatten');
var less = require('gulp-sources-less');
var path = require('path');
 
gulp.task('less', function() {
  var lessStream = less({
      paths: [ path.join(__dirname, 'less', 'includes') ]
    }).on('error', function(err) {
      console.error(err);
      this.emit('end');
    });

  return gulp.src('./src/**/*.less')
    .pipe(lessStream)
    .pipe(flatten())
    .pipe(gulp.dest('../static/css'));
});

gulp.task('generate', ['less']);

gulp.task('watch', ['generate'], function() {
  gulp.watch([ './src/**/*.less' ], ['less']);
});
